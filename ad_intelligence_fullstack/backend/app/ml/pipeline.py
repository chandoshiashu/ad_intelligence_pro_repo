
"""Central orchestration pipeline for Ad Intelligence."""

from typing import Any

from app.ml.clustering import cluster_creatives
from app.ml.features import analyze_creative, summarize_features
from app.ml.recommendations import build_opportunities


def _prepare_ads(
    ads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deduplicate advertisements and attach Gemini-based creative analysis.

    Successful Gemini analyses are reused to avoid unnecessary API calls.
    Legacy rule-based analyses are regenerated using the current pipeline.
    """

    prepared: list[dict[str, Any]] = []
    seen: set[str] = set()

    for ad in ads:
        if not isinstance(ad, dict):
            continue

        archive_id = str(ad.get("ad_archive_id") or "").strip()

        dedupe_key = archive_id or "|".join([
            str(ad.get("advertiser_name") or "").strip().lower(),
            str(ad.get("headline") or "").strip().lower(),
            str(ad.get("ad_text") or "").strip().lower(),
        ])

        # Ignore records without an identifiable ID or usable text.
        if not dedupe_key.strip("|") or dedupe_key in seen:
            continue

        if not archive_id and not (
            str(ad.get("headline") or "").strip()
            or str(ad.get("ad_text") or "").strip()
        ):
            continue

        seen.add(dedupe_key)

        # Copy rather than modifying the caller's original dictionary.
        item = dict(ad)

        existing = item.get("creative_analysis")

        # Reuse only successful analyses from the current Gemini pipeline.
        if not (
            isinstance(existing, dict)
            and existing.get("analysis_method") == "gemini_llm_v1"
            and existing.get("status") == "ok"
        ):
            item["creative_analysis"] = analyze_creative(item)

        prepared.append(item)

    return prepared


def _theme_distribution(
    ads: list[dict[str, Any]],
) -> tuple[dict[str, int], int]:
    """
    Count the number of successfully analyzed ads containing each theme.

    Each theme is counted at most once per ad. Failed analyses are excluded.
    """

    counts: dict[str, int] = {}
    analyzed_ads = 0

    for ad in ads:
        analysis = ad.get("creative_analysis")

        if (
            not isinstance(analysis, dict)
            or analysis.get("analysis_method") != "gemini_llm_v1"
            or analysis.get("status") != "ok"
        ):
            continue

        analyzed_ads += 1

        themes = analysis.get("themes", [])

        if not isinstance(themes, list):
            continue

        unique_themes = {
            theme.strip()
            for theme in themes
            if isinstance(theme, str) and theme.strip()
        }

        for theme in unique_themes:
            counts[theme] = counts.get(theme, 0) + 1

    return counts, analyzed_ads


def run_pipeline(
    company: str,
    competitor: str,
    company_ads: list[dict[str, Any]],
    competitor_ads: list[dict[str, Any]],
    demo_mode: bool = False,
) -> dict[str, Any]:
    """
    Run the complete Ad Intelligence analysis.

    Flow:
        Raw ads
        -> deduplication
        -> Gemini creative analysis
        -> feature summaries
        -> competitor comparison
        -> Gemini opportunity recommendations
        -> TF-IDF + KMeans clustering
        -> final JSON-compatible result
    """

    # 1. Deduplicate ads and analyze each creative.
    brand_a = _prepare_ads(company_ads)
    brand_b = _prepare_ads(competitor_ads)

    # 2. Aggregate the dynamically generated Gemini features.
    summary_a = summarize_features(brand_a)
    summary_b = summarize_features(brand_b)

    # 3. Build comparable theme distributions.
    themes_a, analyzed_a = _theme_distribution(brand_a)
    themes_b, analyzed_b = _theme_distribution(brand_b)

    all_themes = sorted(set(themes_a) | set(themes_b))

    theme_comparison = []

    for theme in all_themes:
        a_count = themes_a.get(theme, 0)
        b_count = themes_b.get(theme, 0)

        theme_comparison.append({
            "theme": theme,
            "company_count": a_count,
            "competitor_count": b_count,
            "company_share_pct": (
                round(a_count / analyzed_a * 100, 1)
                if analyzed_a
                else None
            ),
            "competitor_share_pct": (
                round(b_count / analyzed_b * 100, 1)
                if analyzed_b
                else None
            ),
        })

    # 4. Generate warnings.
    warnings: list[str] = []

    if demo_mode:
        warnings.append(
            "DEMO MODE: advertisements are illustrative sample records, "
            "not verified live Meta Ad Library results."
        )

    if not brand_a or not brand_b:
        warnings.append(
            "At least one brand returned no usable advertisements. "
            "Comparison results may be unavailable or incomplete."
        )

    if not analyzed_a or not analyzed_b:
        warnings.append(
            "At least one brand has no successfully analyzed ads. "
            "Check Gemini configuration, API errors, and analysis results."
        )

    if analyzed_a < 10 or analyzed_b < 10:
        warnings.append(
            "Small sample: results describe only successfully analyzed "
            "records and may not represent all advertising activity."
        )

    failed_a = summary_a.get("failed_analyses", 0)
    failed_b = summary_b.get("failed_analyses", 0)

    if failed_a or failed_b:
        warnings.append(
            f"Gemini analysis failed for {failed_a} {company} ads "
            f"and {failed_b} {competitor} ads. Failed records are excluded "
            "from creative-feature percentages."
        )

    # 5. Ask Gemini to interpret the observed differences.
    opportunities = build_opportunities(
        company,
        competitor,
        brand_a,
        brand_b,
    )

    if opportunities.get("status") == "unavailable":
        warnings.append(
            "Opportunity generation failed. Inspect the returned error "
            "and backend logs."
        )
    elif opportunities.get("status") == "insufficient_data":
        warnings.append(
            "There is insufficient successfully analyzed data to "
            "generate competitor opportunities."
        )

    # 6. Cluster the ad texts independently of Gemini feature analysis.
    clusters_a = cluster_creatives(brand_a)
    clusters_b = cluster_creatives(brand_b)

    # 7. Return the complete result for the FastAPI backend.
    return {
        "company": company,
        "competitor": competitor,
        "demo_mode": demo_mode,
        "collection_status": (
            "completed" if brand_a and brand_b else "partial"
        ),
        "analysis_status": (
            "completed"
            if analyzed_a == len(brand_a)
            and analyzed_b == len(brand_b)
            and analyzed_a > 0
            and analyzed_b > 0
            else "partial"
        ),
        "warnings": warnings,
        "summary": {
            "company": summary_a,
            "competitor": summary_b,
            "ads_analyzed_total": len(brand_a) + len(brand_b),
            "successfully_analyzed_total": analyzed_a + analyzed_b,
        },
        "comparison": {
            "theme_distribution": theme_comparison,
            "cta_counts": {
                company: summary_a.get("cta_counts", {}),
                competitor: summary_b.get("cta_counts", {}),
            },
            "benefit_counts": {
                company: summary_a.get("benefit_counts", {}),
                competitor: summary_b.get("benefit_counts", {}),
            },
            "emotional_trigger_counts": {
                company: summary_a.get("emotional_trigger_counts", {}),
                competitor: summary_b.get("emotional_trigger_counts", {}),
            },
            "tone_counts": {
                company: summary_a.get("tone_counts", {}),
                competitor: summary_b.get("tone_counts", {}),
            },
            "offer_signal_share_pct": {
                company: summary_a.get("offer_signal_share_pct"),
                competitor: summary_b.get("offer_signal_share_pct"),
            },
        },
        "opportunities": opportunities,
        "ads": {
            company: brand_a,
            competitor: brand_b,
        },
        "clusters": {
            company: clusters_a,
            competitor: clusters_b,
        },
    }
