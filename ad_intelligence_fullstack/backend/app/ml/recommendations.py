
"""
Gemini-powered competitor creative opportunity analysis.

Python calculates descriptive statistics.
Gemini interprets the observed differences and suggests experiments.

No manually defined theme, CTA, or benefit categories.
"""

import json
import os
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_client = None

FEATURE_FIELDS = (
    "themes",
    "benefit_signals",
    "cta_categories",
    "emotional_triggers",
    "tone",
    "offer_signals",
)


def _get_client():
    """Create the Gemini client lazily."""
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing from the environment."
            )

        _client = genai.Client(api_key=api_key)

    return _client


def _parse_json(text: str) -> dict[str, Any]:
    """Parse a JSON object returned by Gemini."""
    if not text:
        raise ValueError("Gemini returned an empty response.")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    result = json.loads(cleaned)

    if not isinstance(result, dict):
        raise ValueError("Gemini response must be a JSON object.")

    return result


def _collect_brand_features(
    ads: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate categories from previously generated creative_analysis.

    Ads without a successful Gemini analysis are excluded from the
    analyzed denominator so failed analyses do not distort percentages.
    """

    counts: dict[str, Counter[str]] = {
        field: Counter() for field in FEATURE_FIELDS
    }

    analyzed_ads = 0
    failed_ads = 0

    for ad in ads:
        analysis = ad.get("creative_analysis")

        # Require a successful analysis from the new Gemini pipeline.
        if (
            not isinstance(analysis, dict)
            or analysis.get("analysis_method") != "gemini_llm_v1"
            or analysis.get("status") != "ok"
        ):
            failed_ads += 1
            continue

        analyzed_ads += 1

        for field in FEATURE_FIELDS:
            values = analysis.get(field, [])

            if not isinstance(values, list):
                continue

            # Count each category at most once per ad.
            unique_values = {
                value.strip()
                for value in values
                if isinstance(value, str) and value.strip()
            }

            counts[field].update(unique_values)

    distributions = {}

    for field, counter in counts.items():
        distributions[field] = [
            {
                "category": category,
                "ads_with_category": count,
                "sample_size": analyzed_ads,
                "share_pct": round(count / analyzed_ads * 100, 1),
            }
            for category, count in counter.most_common()
        ]

    return {
        "ads_received": len(ads),
        "ads_analyzed": analyzed_ads,
        "ads_without_successful_analysis": failed_ads,
        "distributions": distributions,
    }


def _build_comparison(
    company: str,
    competitor: str,
    brand_a: dict[str, Any],
    brand_b: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Compare categories using only successfully analyzed ads.
    Each category's share uses its own brand's analyzed sample size.
    """

    comparisons = []

    a_n = brand_a["ads_analyzed"]
    b_n = brand_b["ads_analyzed"]

    if not a_n or not b_n:
        return comparisons

    for field in FEATURE_FIELDS:
        a_items = {
            item["category"]: item
            for item in brand_a["distributions"][field]
        }

        b_items = {
            item["category"]: item
            for item in brand_b["distributions"][field]
        }

        all_categories = set(a_items) | set(b_items)

        for category in all_categories:
            a_count = a_items.get(category, {}).get(
                "ads_with_category", 0
            )
            b_count = b_items.get(category, {}).get(
                "ads_with_category", 0
            )

            a_pct = round(a_count / a_n * 100, 1)
            b_pct = round(b_count / b_n * 100, 1)

            comparisons.append({
                "feature_type": field,
                "category": category,
                "difference_percentage_points": round(
                    abs(a_pct - b_pct), 1
                ),
                "company": {
                    "ads_with_category": a_count,
                    "sample_size": a_n,
                    "share_pct": a_pct,
                },
                "competitor": {
                    "ads_with_category": b_count,
                    "sample_size": b_n,
                    "share_pct": b_pct,
                },
            })

    return sorted(
        comparisons,
        key=lambda item: item["difference_percentage_points"],
        reverse=True,
    )


def build_opportunities(
    company: str,
    competitor: str,
    brand_a: list[dict[str, Any]],
    brand_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate competitor creative hypotheses with Gemini.

    Statistics are calculated deterministically in Python.
    Gemini proposes and explains experiments based on those statistics.

    Returns a structured result containing opportunities, evidence,
    sample information, and analysis status.
    """

    if not brand_a or not brand_b:
        return {
            "status": "insufficient_data",
            "message": (
                "A comparison requires collected advertisements "
                "from both brands."
            ),
            "opportunities": [],
            "sample_sizes": {
                company: len(brand_a),
                competitor: len(brand_b),
            },
        }

    try:
        a_data = _collect_brand_features(brand_a)
        b_data = _collect_brand_features(brand_b)

        if not a_data["ads_analyzed"] or not b_data["ads_analyzed"]:
            return {
                "status": "insufficient_data",
                "message": (
                    "Both brands need at least one successfully analyzed "
                    "ad. Run the Gemini creative-analysis pipeline first."
                ),
                "sample_sizes": {
                    company: a_data["ads_analyzed"],
                    competitor: b_data["ads_analyzed"],
                },
                "ads_without_successful_analysis": {
                    company: a_data["ads_without_successful_analysis"],
                    competitor: b_data["ads_without_successful_analysis"],
                },
                "opportunities": [],
            }

        comparisons = _build_comparison(
            company,
            competitor,
            a_data,
            b_data,
        )

        # Avoid sending an unnecessarily large payload to the LLM.
        # This is a computational limit, not a fixed category taxonomy.
        evidence = comparisons[:30]

        if not evidence or all(
            item["difference_percentage_points"] == 0
            for item in evidence
        ):
            return {
                "status": "ok",
                "message": (
                    "No differences in the observed category shares "
                    "were detected in the successfully analyzed sample."
                ),
                "sample_sizes": {
                    company: a_data["ads_analyzed"],
                    competitor: b_data["ads_analyzed"],
                },
                "comparisons": evidence,
                "opportunities": [],
            }

        prompt = f"""
You are a senior advertising strategist for an Ad Intelligence platform.

Your task is to identify useful, testable creative opportunities by
comparing two brands' observed advertising characteristics.

BRANDS:
- Company: {company}
- Competitor: {competitor}

SAMPLE SIZES:
- Company: {a_data["ads_analyzed"]} successfully analyzed ads
- Competitor: {b_data["ads_analyzed"]} successfully analyzed ads

OBSERVED COMPARISON DATA:
{json.dumps(evidence, ensure_ascii=False)}

INSTRUCTIONS:

1. Generate relevant hypotheses from the supplied evidence.
2. Categories were generated dynamically by an LLM. Interpret their
   meaning from their labels and feature_type; do not assume a fixed
   taxonomy.
3. You may return different numbers of opportunities depending on the
   evidence. Prefer a few distinct, actionable hypotheses over redundant
   recommendations.
4. Focus on meaningful differences, underrepresented messaging angles,
   possible positioning contrasts, or useful similarities worth testing.
5. A lower category share is NOT automatically a market gap or a
   competitive advantage.
6. Do not claim that either brand has better performance, more spend,
   higher conversions, or a larger market share. None of these are
   established by the supplied data.
7. Treat the supplied counts and percentages as the evidence. Do not
   invent numerical facts or change these values.
8. Recommend controlled experiments and measurable evaluation criteria.
   Suggested metrics may include CTR, conversion rate, CPA, or ROAS,
   depending on the campaign objective.
9. Explain why the experiment could be worth testing and identify
   relevant uncertainty.
10. If the sample is too small to support a useful conclusion, state
    that limitation instead of inventing an opportunity.
11. Only use categories present in the supplied comparison data.
12. Do not interpret absence from a sample as proof that a brand never
    uses that strategy.

Return valid JSON with this structure:

{{
  "opportunities": [
    {{
      "category": "An exact category from the comparison data",
      "feature_type": "The corresponding feature_type",
      "title": "Concise experiment or opportunity title",
      "rationale": "Evidence-based explanation of the hypothesis",
      "suggested_experiment": "A practical experiment with a control",
      "evaluation_metric": "A measurable campaign KPI",
      "confidence": "exploratory"
    }}
  ],
  "overall_assessment": "A concise, appropriately cautious comparison"
}}

Use an empty opportunities list if no meaningful hypothesis is supported.
Do not include Markdown or text outside the JSON object.
"""

        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        result = _parse_json(response.text or "")
        raw_opportunities = result.get("opportunities", [])

        if not isinstance(raw_opportunities, list):
            raise ValueError(
                "Gemini returned an invalid opportunities field."
            )

        # Only allow recommendations grounded in supplied categories.
        evidence_lookup = {
            (item["feature_type"], item["category"]): item
            for item in evidence
        }

        opportunities = []

        for item in raw_opportunities:
            if not isinstance(item, dict):
                continue

            category = item.get("category")
            feature_type = item.get("feature_type")

            if not isinstance(category, str) or not isinstance(
                feature_type, str
            ):
                continue

            matching_evidence = evidence_lookup.get(
                (feature_type, category)
            )

            if matching_evidence is None:
                continue

            opportunities.append({
                "title": str(item.get("title") or "Creative experiment"),
                "category": category,
                "feature_type": feature_type,
                "rationale": str(item.get("rationale") or ""),
                # Numerical evidence always comes from Python.
                "evidence": matching_evidence,
                "suggested_experiment": str(
                    item.get("suggested_experiment") or ""
                ),
                "evaluation_metric": str(
                    item.get("evaluation_metric")
                    or "Choose a campaign KPI before launch."
                ),
                "confidence": "exploratory",
            })

        return {
            "status": "ok",
            "analysis_method": "gemini_opportunity_analysis_v1",
            "companies": [company, competitor],
            "sample_sizes": {
                company: a_data["ads_analyzed"],
                competitor: b_data["ads_analyzed"],
            },
            "ads_without_successful_analysis": {
                company: a_data["ads_without_successful_analysis"],
                competitor: b_data["ads_without_successful_analysis"],
            },
            "overall_assessment": str(
                result.get("overall_assessment") or ""
            ),
            "comparisons": evidence,
            "opportunities": opportunities,
            "limitations": (
                "Hypotheses are based on collected ad-copy features. "
                "They do not establish market gaps or actual ad performance."
            ),
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "message": str(exc),
            "opportunities": [],
        }
