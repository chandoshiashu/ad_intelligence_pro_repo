
"""
Gemini-powered, dynamic feature extraction for advertising creatives.

No manually defined themes, benefit categories, CTA categories, or regex rules.
Gemini interprets each ad and generates relevant categories dynamically.
"""

import json
import os
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load environment variables from .env
load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

_client = None


def _get_client():
    """Initialize the Gemini client only when needed."""
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. "
                "Add it to your backend .env file."
            )

        _client = genai.Client(api_key=api_key)

    return _client


def _as_string_list(value: Any) -> list[str]:
    """Safely normalize an LLM-generated list of strings."""
    if not isinstance(value, list):
        return []

    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _extract_json(response_text: str) -> dict[str, Any]:
    """Parse Gemini's JSON response."""
    if not response_text:
        raise ValueError("Gemini returned an empty response.")

    cleaned = response_text.strip()

    # Handle JSON accidentally wrapped in Markdown fences.
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    data = json.loads(cleaned)

    if not isinstance(data, dict):
        raise ValueError("Gemini returned JSON that is not an object.")

    return data


def analyze_creative(ad: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze one advertisement using Gemini.

    Categories are generated dynamically from the actual ad copy.
    The function does not use predefined keyword lists or regex rules.
    """

    headline = str(ad.get("headline") or "").strip()
    ad_text = str(ad.get("ad_text") or "").strip()

    # Include the fields that actually contain the creative copy.
    text = "\n".join(
        part for part in (headline, ad_text) if part
    ).strip()

    if not text:
        return {
            "status": "insufficient_data",
            "message": "This advertisement has no usable headline or ad text.",
            "themes": [],
            "offer_signals": [],
            "cta_categories": [],
            "benefit_signals": [],
            "emotional_triggers": [],
            "tone": [],
            "target_audience": [],
            "messaging_summary": "",
            "evidence": [],
            "text_length": 0,
            "analysis_method": "gemini_llm_v1",
        }

    prompt = f"""
You are an advertising creative analyst working on Ad Intelligence,
a competitor advertising research platform.

Analyze the advertisement below using its actual wording and context.

Generate categories dynamically. Do NOT restrict yourself to a predefined
taxonomy or a fixed number of categories. Create as many distinct,
useful categories as the evidence supports, but avoid redundant categories.

Return one valid JSON object with exactly these fields:

{{
  "themes": [
    "Distinct strategic themes communicated by the ad"
  ],
  "offer_signals": [
    "Specific promotions, incentives, prices, or offer mechanisms
     explicitly communicated in the ad"
  ],
  "cta_categories": [
    "Actions the ad explicitly encourages its audience to take"
  ],
  "benefit_signals": [
    "Distinct functional or emotional benefits promised or emphasized"
  ],
  "emotional_triggers": [
    "Emotional appeals supported by the actual ad wording"
  ],
  "tone": [
    "Distinct characteristics of the ad's communication style"
  ],
  "target_audience": [
    "Audience segments explicitly indicated or reasonably suggested
     by the ad, with uncertainty acknowledged"
  ],
  "messaging_summary": "A concise explanation of the ad's core message.",
  "evidence": [
    "Short exact quotes from the ad that support your analysis"
  ]
}}

Analysis requirements:
1. Generate descriptive, specific categories based on this ad.
2. Do not force the ad into generic categories if more appropriate
   categories emerge from its content.
3. Return empty arrays for categories without sufficient evidence.
4. Do not invent discounts, prices, CTAs, audience segments, or promises.
5. Separate explicit facts from reasonable interpretations.
6. Do not infer actual campaign performance, engagement, conversions,
   advertising budget, or customer behavior from copy alone.
7. Evidence must consist of short quotations copied from the ad.
8. Do not include Markdown, commentary, or extra fields.
9. Every field must have the type shown in the JSON structure.
10. Use concise, business-relevant wording. Avoid near-duplicate labels.

ADVERTISEMENT:
Headline:
{headline or "(not provided)"}

Ad text:
{ad_text or "(not provided)"}
"""

    try:
        client = _get_client()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        result = _extract_json(response.text or "")

        # Normalize fields to a predictable schema for the frontend.
        return {
            "status": "ok",
            "themes": _as_string_list(result.get("themes")),
            "offer_signals": _as_string_list(
                result.get("offer_signals")
            ),
            "cta_categories": _as_string_list(
                result.get("cta_categories")
            ),
            "benefit_signals": _as_string_list(
                result.get("benefit_signals")
            ),
            "emotional_triggers": _as_string_list(
                result.get("emotional_triggers")
            ),
            "tone": _as_string_list(result.get("tone")),
            "target_audience": _as_string_list(
                result.get("target_audience")
            ),
            "messaging_summary": (
                result.get("messaging_summary", "")
                if isinstance(result.get("messaging_summary"), str)
                else ""
            ),
            "evidence": _as_string_list(result.get("evidence")),
            "text_length": len(text),
            "analysis_method": "gemini_llm_v1",
            "limitations": (
                "LLM-generated interpretation of ad copy. "
                "Categories and audience suggestions are inferred, "
                "not verified campaign performance or audience intent."
            ),
        }

    except Exception as exc:
        # Preserve a predictable response instead of crashing the pipeline.
        return {
            "status": "unavailable",
            "message": str(exc),
            "themes": [],
            "offer_signals": [],
            "cta_categories": [],
            "benefit_signals": [],
            "emotional_triggers": [],
            "tone": [],
            "target_audience": [],
            "messaging_summary": "",
            "evidence": [],
            "text_length": len(text),
            "analysis_method": "gemini_llm_v1",
        }


def summarize_features(
    ads: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate dynamically generated Gemini features across advertisements.

    Existing Gemini analyses are reused. Missing or legacy rule-based
    analyses are regenerated using Gemini.
    """

    theme_counts: Counter[str] = Counter()
    cta_counts: Counter[str] = Counter()
    benefit_counts: Counter[str] = Counter()
    emotional_trigger_counts: Counter[str] = Counter()
    tone_counts: Counter[str] = Counter()
    audience_counts: Counter[str] = Counter()

    offer_count = 0
    successful_analyses = 0
    failed_analyses = 0
    analyzed_ads = []

    for ad in ads:
        existing = ad.get("creative_analysis")

        # Do not accidentally reuse the old regex-based output.
        if (
            isinstance(existing, dict)
            and existing.get("analysis_method") == "gemini_llm_v1"
            and existing.get("status") == "ok"
        ):
            analysis = existing
        else:
            analysis = analyze_creative(ad)

        analyzed_ads.append(analysis)

        if analysis.get("status") != "ok":
            failed_analyses += 1
            continue

        successful_analyses += 1

        theme_counts.update(analysis.get("themes", []))
        cta_counts.update(analysis.get("cta_categories", []))
        benefit_counts.update(analysis.get("benefit_signals", []))
        emotional_trigger_counts.update(
            analysis.get("emotional_triggers", [])
        )
        tone_counts.update(analysis.get("tone", []))
        audience_counts.update(analysis.get("target_audience", []))

        # Count an ad once, regardless of how many offers it contains.
        if analysis.get("offer_signals"):
            offer_count += 1

    n = len(ads)

    return {
        "ads_analyzed": n,
        "successful_analyses": successful_analyses,
        "failed_analyses": failed_analyses,
        "ads_with_offer_signals": offer_count,
        "offer_signal_share_pct": (
            round(offer_count / successful_analyses * 100, 1)
            if successful_analyses
            else None
        ),
        "theme_counts": dict(theme_counts.most_common()),
        "cta_counts": dict(cta_counts.most_common()),
        "benefit_counts": dict(benefit_counts.most_common()),
        "emotional_trigger_counts": dict(
            emotional_trigger_counts.most_common()
        ),
        "tone_counts": dict(tone_counts.most_common()),
        "audience_counts": dict(audience_counts.most_common()),
        "individual_analyses": analyzed_ads,
        "sample_size_warning": (
            "Small or incomplete samples may not represent all ads "
            "run by the brand."
            if successful_analyses < 10
            else None
        ),
        "analysis_method": "gemini_llm_v1",
    }
