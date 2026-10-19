"""TinyFish Web Agent adapter. Uses the documented synchronous run endpoint."""

import json
import re
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings

TINYFISH_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"


def _meta_library_url(brand: str) -> str:
    query = urlencode(
        {
            "active_status": "active",
            "ad_type": "ALL",
            "country": "IN",
            "search_type": "keyword_unordered",
            "q": brand,
        }
    )
    return f"{settings.meta_ad_library_base_url}?{query}"


def _parse_jsonish(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return value


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    payload = _parse_jsonish(payload)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("ads", "advertisements", "records", "results", "data", "items"):
        value = payload.get(key)
        parsed = _parse_jsonish(value)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            found = _extract_records(parsed)
            if found:
                return found
    # Sometimes the agent nests the requested JSON inside a result/output field.
    for key in ("result", "output", "response", "content"):
        if key in payload:
            found = _extract_records(payload[key])
            if found:
                return found
    return []


async def collect_brand_ads(brand: str, limit: int = 20) -> list[dict[str, Any]]:
    if not settings.tinyfish_api_key:
        raise RuntimeError("TINYFISH_API_KEY is not configured. Set it in backend/.env.")

    url = _meta_library_url(brand)
#     goal = f"""
# Open the public Meta Ad Library page for the search term {brand!r} in India.
# Collect up to {limit} advertisements that clearly belong to this exact advertiser/brand.
# Do not include similarly named unrelated advertisers. Only return information visible on the public page.
# Return JSON only in this schema:
# {{
#   "ads": [
#     {{
#       "advertiser_name": "visible advertiser name",
#       "ad_archive_id": "archive ID if visible, otherwise null",
#       "ad_text": "primary text if visible, otherwise empty string",
#       "headline": "headline if visible, otherwise empty string",
#       "start_date": "visible start date if available, otherwise null",
#       "platforms": ["Facebook", "Instagram"],
#       "media_type": "image, video, carousel, or unknown if visible",
#       "landing_page_url": "destination URL if visible, otherwise null",
#       "ad_library_url": "direct URL to the specific ad if available",
#       "image_url": "public creative image URL if available, otherwise null"
#     }}
#   ],
#   "notes": ["limitations or missing information"]
# }}
# Do not invent unavailable fields or performance metrics such as impressions, clicks, CTR, spend, or conversions.
# If no matching ads are available, return {{"ads": [], "notes": ["explain why if visible"]}}.
# """.strip()

    

    goal = f"""
    Open this Meta Ad Library search page:
    {url}

    TASK:
    Find up to {limit} ads published by the advertiser whose name is
    exactly or clearly identifiable as "{brand}".

    IMPORTANT:
    - Search for the advertiser/page name, not merely the keyword.
    - Inspect the advertiser name displayed on each ad.
    - Do not return ads just because "{brand}" appears in the ad text,
      headline, destination URL, or unrelated metadata.
    - Exclude unrelated advertisers, charities, resellers, and other pages.
    - If you cannot verify the advertiser name, exclude that ad.
    - Return only information actually visible on the page.
    - Stop after collecting {limit} verified ads.

    Return JSON only:
    {{
      "ads": [
        {{
          "advertiser_name": "visible advertiser name",
          "ad_archive_id": "visible ID or null",
          "ad_text": "visible primary text or empty string",
          "headline": "visible headline or empty string"
        }}
      ],
      "notes": ["explain any collection limitations"]
    }}

    If no matching advertiser ads are found, return:
    {{"ads": [], "notes": ["No verified matching ads found"]}}
    """.strip()



    timeout = httpx.Timeout(
        timeout=240.0,   # Default/read timeout
        connect=20.0,
        write=30.0,
        pool=20.0,
    )


    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = await client.post(
                TINYFISH_RUN_URL,
                headers={
                    "X-API-Key": settings.tinyfish_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "goal": goal,
                    "browser_profile": "lite",
                },
            )
    except httpx.ReadTimeout as exc:
        raise RuntimeError(
            f"TinyFish did not return a response within "
            f"{timeout.read} seconds. The browser task may be slow "
            "or the API may be unresponsive."
        ) from exc
    except httpx.ConnectTimeout as exc:
        raise RuntimeError(
            "Could not establish a connection to TinyFish in time."
        ) from exc



    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f"TinyFish returned HTTP {response.status_code}: {detail}")

    result = response.json()

    print("\n===== TINYFISH DEBUG =====")
    print("HTTP:", response.status_code)
    print("Top-level keys:", list(result.keys()))
    print("Run status:", result.get("status"))
    print("Run ID:", result.get("run_id"))
    print("Error:", result.get("error"))
    print("Result payload:", repr(result.get("result"))[:6000])
    print("==========================\n")
        
    status = str(result.get("status", "")).upper()
    if status and status not in {"COMPLETED", "SUCCESS", "SUCCEEDED"}:
        raise RuntimeError(f"TinyFish run did not complete successfully (status={status}).")

    payload = result.get("result", result.get("resultJson", result))
    records = _extract_records(payload)
    if not records and isinstance(payload, str):
        raise RuntimeError("TinyFish completed, but its response could not be parsed into an ads array.")
    return records[:limit]
