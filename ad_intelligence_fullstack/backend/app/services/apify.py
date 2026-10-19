
"""Apify Meta Ad Library collection with evidence-based advertiser matching.

Responsibilities:
- Search multiple query variants when needed.
- Normalize the observed Apify actor schema.
- Ask Gemini to classify candidate advertisers using source evidence.
- Validate the returned evidence against the raw record.
- Fall back to strict aliases if Gemini is unavailable.
- Preserve the fields consumed by the existing analysis pipeline.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings


APIFY_API_BASE = "https://api.apify.com/v2"
DEFAULT_ACTOR_ID = "lergassy~meta-ad-library-scraper"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# These are query expansions and fallback aliases, not proof that an ad
# belongs to a brand. Gemini evidence validation is used for ambiguous cases.
BRAND_CONFIG: dict[str, dict[str, list[str]]] = {
    "primevideo": {
        "queries": [
            "prime video",
            "amazon prime video",
            "prime video india",
            "amazon prime",
        ],
        "aliases": [
            "prime video",
            "amazon prime video",
            "amazon prime video india",
            "prime video india",
        ],
    },
    "amazonprime": {
        "queries": [
            "amazon prime",
            "amazon prime video",
            "prime video",
            "prime video india",
        ],
        "aliases": [
            "amazon prime",
            "amazon prime video",
            "amazon prime video india",
            "prime video",
            "prime video india",
        ],
    },
    "netflix": {
        "queries": ["netflix", "netflix india"],
        "aliases": ["netflix", "netflix india"],
    },
    "zomato": {
        "queries": ["zomato", "zomato india"],
        "aliases": ["zomato", "zomato india"],
    },
    "swiggy": {
        "queries": ["swiggy", "swiggy india"],
        "aliases": ["swiggy", "swiggy india"],
    },
}


def _clean(value: Any) -> str:
    """Return scalar values as clean text."""
    if value is None or isinstance(value, bool):
        return ""

    if isinstance(value, (str, int, float)):
        return str(value).strip()

    return ""


def _real_text(*values: Any) -> str:
    """Return the first useful value, ignoring template placeholders."""
    for value in values:
        text = _clean(value)

        if not text:
            continue

        if re.search(r"\{\{.*?\}\}", text):
            continue

        if text.casefold() in {
            "null",
            "none",
            "n/a",
            "undefined",
            "unknown",
        }:
            continue

        return text

    return ""


def _unique_texts(values: Any) -> list[str]:
    """Clean and deduplicate text values from a list."""
    if not isinstance(values, list):
        return []

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = _real_text(value)
        key = text.casefold()

        if text and key not in seen:
            seen.add(key)
            result.append(text)

    return result


def _brand_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _brand_config(brand: str) -> dict[str, list[str]]:
    key = _brand_key(brand)

    if key in BRAND_CONFIG:
        return BRAND_CONFIG[key]

    # Do not invent aliases for brands not explicitly configured.
    return {
        "queries": [brand.strip()],
        "aliases": [brand.strip()],
    }


def _strict_alias_match(advertiser: str, brand: str) -> bool:
    """Conservative fallback when Gemini cannot be used."""
    advertiser_key = _brand_key(advertiser)
    if not advertiser_key:
        return False

    aliases = _brand_config(brand)["aliases"]
    return advertiser_key in {_brand_key(alias) for alias in aliases}


def _normalise_platforms(raw: dict[str, Any]) -> list[str]:
    platforms = (
        raw.get("publisherPlatforms")
        or raw.get("platforms")
        or raw.get("publisher_platforms")
        or []
    )

    if isinstance(platforms, str):
        platforms = re.split(r"[,;|]", platforms)

    if not isinstance(platforms, list):
        return []

    return [
        str(value).strip()
        for value in platforms
        if str(value).strip()
    ]


def normalise_apify_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Map an Apify actor record into the project's common ad schema."""

    advertiser = _real_text(
        raw.get("pageName"),
        raw.get("page_name"),
        raw.get("advertiser_name"),
        raw.get("advertiserName"),
        raw.get("advertiser"),
    )

    archive_id = _real_text(
        raw.get("adArchiveId"),
        raw.get("ad_archive_id"),
        raw.get("archive_id"),
        raw.get("id"),
    )

    body_text = _real_text(
        raw.get("bodyText"),
        raw.get("adText"),
        raw.get("ad_text"),
        raw.get("primaryText"),
        raw.get("primary_text"),
        raw.get("body"),
    )

    headline = _real_text(
        raw.get("title"),
        raw.get("headline"),
        raw.get("adTitle"),
    )

    card_texts = _unique_texts(raw.get("cardTexts"))
    creative_parts: list[str] = []
    seen_parts: set[str] = set()

    for part in [body_text, *card_texts]:
        key = part.casefold()
        if part and key not in seen_parts:
            seen_parts.add(key)
            creative_parts.append(part)

    ad_text = "\n".join(creative_parts)

    if not headline and card_texts:
        headline = card_texts[0]

    image_urls = _unique_texts(raw.get("imageUrls"))
    video_urls = _unique_texts(raw.get("videoUrls"))

    archive_url = _real_text(
        raw.get("adLibraryUrl"),
        raw.get("ad_library_url"),
    )

    if not archive_url and archive_id:
        archive_url = (
            "https://www.facebook.com/ads/library/?id="
            + archive_id
        )

    landing_page_url = _real_text(
        raw.get("linkUrl"),
        raw.get("landingPageUrl"),
        raw.get("landing_page_url"),
        raw.get("destinationUrl"),
        raw.get("destination_url"),
        raw.get("link_url"),
    )

    return {
        "advertiser_name": advertiser,
        "ad_archive_id": archive_id or None,
        "ad_text": ad_text,
        "headline": headline,
        "start_date": _real_text(
            raw.get("startDate"),
            raw.get("start_date"),
            raw.get("adStartDate"),
            raw.get("ad_start_date"),
        ) or None,
        "end_date": _real_text(
            raw.get("endDate"),
            raw.get("end_date"),
        ) or None,
        "platforms": _normalise_platforms(raw),
        "media_type": _real_text(
            raw.get("displayFormat"),
            raw.get("mediaType"),
            raw.get("media_type"),
            raw.get("format"),
        ) or None,
        "landing_page_url": landing_page_url or None,
        "ad_library_url": archive_url or None,
        "image_url": image_urls[0] if image_urls else None,
        "image_urls": image_urls,
        "video_urls": video_urls,
        "card_texts": card_texts,
        "cta_text": _real_text(raw.get("ctaText")) or None,
        "cta_type": _real_text(raw.get("ctaType")) or None,
        "link_description": _real_text(
            raw.get("linkDescription")
        ) or None,
        "page_url": _real_text(raw.get("pageUrl")) or None,
        "page_id": _real_text(raw.get("pageId")) or None,
        "page_likes": raw.get("pageLikes"),
        "page_categories": raw.get("pageCategories") or [],
        "is_dynamic_template": bool(
            raw.get("isDynamicTemplate", False)
        ),
        "is_active": raw.get("isActive"),
        "variant_count": raw.get("variantCount"),
        "spend": raw.get("spend"),
        "currency": raw.get("currency"),
        "reach_estimate": raw.get("reachEstimate"),
        "impressions_text": raw.get("impressionsText"),
        "source": "apify_meta_ad_library",
        "source_verified": False,
        "advertiser_match": {
            "status": "pending",
            "method": None,
            "confidence": None,
            "evidence": [],
            "reason": "Advertiser has not been evaluated yet.",
        },
    }


def _candidate_for_llm(
    index: int,
    raw: dict[str, Any],
) -> dict[str, Any]:
    """Send useful, bounded evidence to Gemini; omit image blobs/URLs."""
    return {
        "index": index,
        "pageName": _real_text(raw.get("pageName")),
        "pageUrl": _real_text(raw.get("pageUrl")),
        "pageId": _real_text(raw.get("pageId")),
        "pageCategories": raw.get("pageCategories") or [],
        "adText": _real_text(
            raw.get("bodyText"),
            raw.get("adText"),
            raw.get("ad_text"),
        )[:700],
        "headline": _real_text(raw.get("title"), raw.get("headline"))[:250],
        "linkUrl": _real_text(raw.get("linkUrl"))[:400],
        "linkDescription": _real_text(raw.get("linkDescription"))[:250],
        "archiveId": _real_text(raw.get("adArchiveId")),
        "query": _real_text(raw.get("query")),
    }


def _gemini_credentials() -> tuple[str, str]:
    """Read existing project settings first, then environment variables."""
    api_key = (
        getattr(settings, "gemini_api_key", None)
        or os.getenv("GEMINI_API_KEY")
        or ""
    )

    model = (
        getattr(settings, "gemini_model", None)
        or os.getenv("GEMINI_MODEL")
        or DEFAULT_GEMINI_MODEL
    )

    return str(api_key).strip(), str(model).strip()


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON even if the model wraps it in a Markdown code fence."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Gemini did not return a JSON object.")
        value = json.loads(cleaned[start : end + 1])

    if not isinstance(value, dict):
        raise ValueError("Gemini JSON response was not an object.")

    return value


async def _classify_candidates_with_gemini(
    brand: str,
    raw_candidates: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """
    Classify all candidates in one Gemini request.

    Acceptance requires:
    - explicit same-advertiser decision,
    - confidence >= 0.90,
    - an evidence quote that really appears in pageName or pageUrl,
    - a non-empty page identity,
    - and no explicit contradictory identity.
    """

    api_key, model = _gemini_credentials()
    if not api_key or not raw_candidates:
        return {}

    evidence_candidates = [
        _candidate_for_llm(index, raw)
        for index, raw in enumerate(raw_candidates)
    ]

    prompt = f"""
You are an evidence-based advertiser identity reviewer for a Meta Ad
Library analysis system.

Requested advertiser: {brand!r}

Decide whether each record was published by the requested brand or an
official/clearly identifiable brand account.

Important rules:
1. Ad copy mentioning the requested brand is NOT proof that the advertiser
   is that brand.
2. A related product, reseller, telecom provider, streaming bundle, agency,
   affiliate, or unrelated page is not automatically the requested advertiser.
3. Prefer pageName and pageUrl as identity evidence. Treat ad text and
   linkUrl as secondary evidence only.
4. Do not invent page ownership, official status, aliases, or facts.
5. If evidence is ambiguous, return same_advertiser=false and status
   "uncertain".
6. Return evidence as short exact quotes copied from supplied fields.
7. Confidence is a judgment about the supplied evidence, not an estimate
   of ad performance.
8. A candidate with only a matching word in its ad copy should be rejected.

Return ONLY valid JSON in this format:
{{
  "matches": [
    {{
      "index": 0,
      "same_advertiser": false,
      "confidence": 0.0,
      "status": "confirmed|probable|unrelated|uncertain",
      "evidence": [
        {{
          "field": "pageName",
          "quote": "exact text copied from the supplied record"
        }}
      ],
      "reason": "Brief explanation based only on supplied evidence"
    }}
  ]
}}

Evaluate every candidate exactly once. Use the supplied index.
Candidates:
{json.dumps(evidence_candidates, ensure_ascii=False)}
""".strip()

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    timeout = httpx.Timeout(
        timeout=45.0,
        connect=10.0,
        write=15.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                endpoint,
                params={"key": api_key},
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0,
                        "responseMimeType": "application/json",
                    },
                },
            )

        response.raise_for_status()
        response_json = response.json()

        model_text = (
            response_json["candidates"][0]["content"]["parts"][0]["text"]
        )
        parsed = _extract_json(model_text)
        matches = parsed.get("matches", [])

        if not isinstance(matches, list):
            return {}

        result: dict[int, dict[str, Any]] = {}

        for item in matches:
            if not isinstance(item, dict):
                continue

            try:
                index = int(item.get("index"))
                confidence = float(item.get("confidence", 0))
            except (TypeError, ValueError):
                continue

            if 0 <= index < len(raw_candidates):
                result[index] = {
                    "same_advertiser": item.get("same_advertiser") is True,
                    "confidence": max(0.0, min(1.0, confidence)),
                    "status": str(item.get("status") or "uncertain").lower(),
                    "evidence": (
                        item.get("evidence")
                        if isinstance(item.get("evidence"), list)
                        else []
                    ),
                    "reason": str(item.get("reason") or "")[:500],
                }

        return result

    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        print(
            "[Gemini advertiser matching] Verification unavailable; "
            f"using strict alias fallback. Error type: {type(exc).__name__}"
        )
        return {}


def _validate_llm_evidence(
    raw: dict[str, Any],
    decision: dict[str, Any],
) -> tuple[bool, list[dict[str, str]], str]:
    """
    Check the model's evidence against the actual record.

    At least one exact evidence quote must occur in pageName or pageUrl.
    Quotes only from ad copy or a landing URL are insufficient.
    """

    identity_fields = {
        "pageName": _real_text(raw.get("pageName")),
        "pageUrl": _real_text(raw.get("pageUrl")),
    }

    evidence = decision.get("evidence", [])
    validated: list[dict[str, str]] = []
    has_identity_evidence = False

    if not isinstance(evidence, list):
        evidence = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        field = str(item.get("field") or "").strip()
        quote = str(item.get("quote") or "").strip()

        if not field or not quote:
            continue

        source_value = _real_text(raw.get(field))
        if not source_value:
            continue

        if quote.casefold() not in source_value.casefold():
            continue

        validated.append({"field": field, "quote": quote})

        if field in identity_fields:
            has_identity_evidence = True

    if not has_identity_evidence:
        return (
            False,
            validated,
            "Gemini did not provide a verifiable quote from pageName or pageUrl.",
        )

    # Identity evidence is required, but confidence and the decision are
    # checked separately by the caller.
    return True, validated, "Identity evidence quotes matched the raw record."


def _verified_decision(
    raw: dict[str, Any],
    brand: str,
    llm_decision: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the final matching decision with a reason for the audit trail."""

    advertiser = _real_text(raw.get("pageName"))

    if llm_decision is not None:
        same = llm_decision.get("same_advertiser") is True
        confidence = float(llm_decision.get("confidence") or 0)
        evidence_ok, evidence, evidence_message = _validate_llm_evidence(
            raw,
            llm_decision,
        )

        accepted = (
            same
            and confidence >= 0.90
            and evidence_ok
            and llm_decision.get("status") in {"confirmed", "probable"}
        )

        return {
            "accepted": accepted,
            "match": {
                "status": "accepted" if accepted else "rejected",
                "method": "gemini_evidence",
                "confidence": confidence,
                "evidence": evidence,
                "reason": (
                    llm_decision.get("reason") or evidence_message
                )[:500],
            },
        }

    # Gemini was unavailable or did not return a decision for this candidate.
    # Strict exact aliases are the only fallback; no substring matching.
    fallback_accepted = _strict_alias_match(advertiser, brand)

    return {
        "accepted": fallback_accepted,
        "match": {
            "status": "accepted" if fallback_accepted else "unverified",
            "method": "strict_alias_fallback",
            "confidence": 1.0 if fallback_accepted else 0.0,
            "evidence": (
                [{"field": "pageName", "quote": advertiser}]
                if fallback_accepted
                else []
            ),
            "reason": (
                "Exact match to a configured fallback alias."
                if fallback_accepted
                else "Gemini decision unavailable and advertiser did not "
                "match a configured exact alias."
            ),
        },
    }


async def _run_actor_query(
    client: httpx.AsyncClient,
    brand_query: str,
    actor_id: str,
    country: str,
    max_ads: int,
) -> list[dict[str, Any]]:
    actor_path = actor_id.strip().replace("/", "~").replace(" ", "")
    endpoint = (
        f"{APIFY_API_BASE}/acts/{actor_path}"
        "/run-sync-get-dataset-items"
    )

    actor_input = {
        "queries": [brand_query],
        "country": country,
        "activeStatus": "active",
        "maxAds": max_ads,
    }

    token = getattr(settings, "apify_api_token", None)
    if not token:
        raise RuntimeError(
            "APIFY_API_TOKEN is missing. Add it to the backend .env file."
        )

    response = await client.post(
        endpoint,
        params={"token": token},
        json=actor_input,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code >= 400:
        # Never include the Apify token in this message.
        raise RuntimeError(
            f"Apify query {brand_query!r} failed with HTTP "
            f"{response.status_code}: {response.text[:300]}"
        )

    payload = response.json()

    if not isinstance(payload, list):
        raise RuntimeError(
            f"Apify query {brand_query!r} returned an unexpected response."
        )

    return [item for item in payload if isinstance(item, dict)]


async def collect_brand_ads(
    brand: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Collect candidate ads, verify advertiser identity, and return matches.

    This keeps the function signature used by the existing /analyze route.
    """

    token = getattr(settings, "apify_api_token", None)
    if not token:
        raise RuntimeError(
            "APIFY_API_TOKEN is missing. Add it to the backend .env file."
        )

    actor_id = (
        getattr(settings, "apify_actor_id", None)
        or DEFAULT_ACTOR_ID
    ).strip()

    country = (
        getattr(settings, "apify_country", None) or "IN"
    ).strip().upper()

    max_ads = max(1, min(int(limit), 20))

    # Query expansion is bounded so collection remains practical.
    query_variants = _brand_config(brand)["queries"][:4]
    per_query_limit = max(5, min(max_ads * 2, 15))

    timeout = httpx.Timeout(
        timeout=180.0,
        connect=20.0,
        write=30.0,
        pool=20.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        tasks = [
            _run_actor_query(
                client=client,
                brand_query=query,
                actor_id=actor_id,
                country=country,
                max_ads=per_query_limit,
            )
            for query in query_variants
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

    raw_candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    query_errors: list[str] = []

    for query, result in zip(query_variants, responses):
        if isinstance(result, Exception):
            query_errors.append(
                f"{query}: {type(result).__name__}"
            )
            print(
                f"[Apify] query={query!r} failed: "
                f"{type(result).__name__}"
            )
            continue

        for raw in result:
            status = _real_text(raw.get("status")).casefold()
            if status == "error" or raw.get("errorCode"):
                continue

            archive_id = _real_text(
                raw.get("adArchiveId"),
                raw.get("ad_archive_id"),
                raw.get("archive_id"),
                raw.get("id"),
            )

            dedupe_key = archive_id or (
                _brand_key(_real_text(raw.get("pageName")))
                + ":"
                + _real_text(raw.get("bodyText"))[:100].casefold()
            )

            if dedupe_key in seen_ids:
                continue

            seen_ids.add(dedupe_key)
            raw_candidates.append(raw)

    if not raw_candidates:
        print(
            f"[Apify] brand={brand!r}: no raw candidates from "
            f"{len(query_variants)} queries. Errors={query_errors}"
        )
        return []

    # One Gemini call evaluates the full candidate batch.
    decisions = await _classify_candidates_with_gemini(
        brand,
        raw_candidates,
    )

    accepted_ads: list[dict[str, Any]] = []
    rejection_log: list[dict[str, str]] = []

    for index, raw in enumerate(raw_candidates):
        decision = _verified_decision(
            raw=raw,
            brand=brand,
            llm_decision=decisions.get(index),
        )

        advertiser = _real_text(raw.get("pageName"))
        match = decision["match"]

        if not decision["accepted"]:
            rejection_log.append({
                "pageName": advertiser[:100],
                "pageUrl": _real_text(raw.get("pageUrl"))[:160],
                "query": _real_text(raw.get("query"))[:80],
                "reason": str(match.get("reason") or "")[:160],
            })
            continue

        ad = normalise_apify_ad(raw)
        ad["source_verified"] = True
        ad["advertiser_match"] = match
        accepted_ads.append(ad)

        if len(accepted_ads) >= max_ads:
            break

    # Rejected candidate logging is intentionally compact; do not dump full
    # records, image URLs, credentials, or complete ad payloads to the console.
    print(
        f"[Apify] brand={brand!r}, country={country}, "
        f"queries={len(query_variants)}, "
        f"raw_candidates={len(raw_candidates)}, "
        f"verified_items={len(accepted_ads)}, "
        f"with_text={sum(bool(a['ad_text'] or a['headline']) for a in accepted_ads)}, "
        f"with_images={sum(bool(a['image_urls']) for a in accepted_ads)}, "
        f"gemini_decisions={len(decisions)}, "
        f"query_errors={len(query_errors)}"
    )

    for rejected in rejection_log[:12]:
        print(
            "[Advertiser rejected] "
            f"brand={brand!r}, pageName={rejected['pageName']!r}, "
            f"pageUrl={rejected['pageUrl']!r}, "
            f"query={rejected['query']!r}, "
            f"reason={rejected['reason']!r}"
        )

    return accepted_ads
