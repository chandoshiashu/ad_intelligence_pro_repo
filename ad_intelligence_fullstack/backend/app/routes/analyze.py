import asyncio
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import AnalyzeRequest
from app.services.demo_data import sample_ads
from app.services.apify import collect_brand_ads
from app.ml.pipeline import run_pipeline
from app.services.gemini import synthesize_insights

router = APIRouter(tags=["analysis"])


def _brand_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _normalise_ad(raw: dict[str, Any], requested_brand: str) -> dict[str, Any] | None:
    advertiser = str(raw.get("advertiser_name") or raw.get("page_name") or raw.get("advertiser") or "").strip()
    if not advertiser:
        return None
    requested_key = _brand_key(requested_brand)
    advertiser_key = _brand_key(advertiser)
    # Keep exact/substring brand matches; discard obvious unrelated advertisers.
    if advertiser_key != requested_key:
        return None

    platforms = raw.get("platforms") or raw.get("publisher_platforms") or []
    if isinstance(platforms, str):
        platforms = [p.strip() for p in re.split(r"[,;|]", platforms) if p.strip()]
    if not isinstance(platforms, list):
        platforms = []

    return {
        "advertiser_name": advertiser,
        "ad_archive_id": raw.get("ad_archive_id") or raw.get("archive_id") or raw.get("id"),
        "ad_text": str(raw.get("ad_text") or raw.get("primary_text") or raw.get("body") or ""),
        "headline": str(raw.get("headline") or raw.get("title") or ""),
        "start_date": raw.get("start_date") or raw.get("ad_start_date"),
        "platforms": [str(p) for p in platforms],
        "media_type": raw.get("media_type") or raw.get("format") or None,
        "landing_page_url": raw.get("landing_page_url") or raw.get("destination_url") or raw.get("link_url"),
        "ad_library_url": raw.get("ad_library_url") or raw.get("source_url") or raw.get("url"),
        "image_url": raw.get("image_url") or raw.get("creative_url") or None,
        "source_verified": True,
    }


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    company = request.company.strip()
    competitor = request.competitor.strip()
    if _brand_key(company) == _brand_key(competitor):
        raise HTTPException(status_code=422, detail="Company and competitor must be different brands.")

    demo_mode = settings.demo_mode
    if demo_mode:
        raw_company = sample_ads(company)
        raw_competitor = sample_ads(competitor, competitor=True)
    else:
        if not settings.tinyfish_api_key:
            raise HTTPException(status_code=503, detail="Live collection is unavailable: configure TINYFISH_API_KEY or enable DEMO_MODE.")
        
        try:
            raw_company, raw_competitor = await asyncio.gather(
                collect_brand_ads(company, limit=5),
                collect_brand_ads(competitor, limit=5),
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail=(
                    "Ad collection timed out after 90 seconds. "
                    "Check the TinyFish API response and timeout settings."
                ),
            ) from exc

        except Exception as exc:
            import traceback
            traceback.print_exc()

            error_message = str(exc).strip() or repr(exc) or "No error details available"

            raise HTTPException(
                status_code=502,
                detail=(
                    f"Ad collection failed "
                    f"({type(exc).__name__}): {error_message}"
                ),
            ) from exc

    company_ads = [ad for raw in raw_company if (ad := _normalise_ad(raw, company))]
    competitor_ads = [ad for raw in raw_competitor if (ad := _normalise_ad(raw, competitor))]

    # Demo records intentionally carry source_verified=False and are clearly marked.
    if demo_mode:
        company_ads = raw_company
        competitor_ads = raw_competitor

    result = run_pipeline(company, competitor, company_ads, competitor_ads, demo_mode=demo_mode)
    result["ai_insights"] = await synthesize_insights(result)
    return result
