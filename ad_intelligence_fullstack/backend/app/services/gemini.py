"""Optional Gemini synthesis over observed ad records and computed metrics."""
import json
import httpx
from app.config import settings

async def synthesize_insights(analysis: dict) -> dict:
    if not settings.gemini_api_key:
        return {"enabled": False, "status": "not_configured", "message": "Set GEMINI_API_KEY in backend/.env to enable Gemini synthesis."}

    # Keep the prompt compact: only send observable creative text and computed counts.
    compact = {
        "company": analysis.get("company"),
        "competitor": analysis.get("competitor"),
        "demo_mode": analysis.get("demo_mode"),
        "summary": analysis.get("summary"),
        "comparison": analysis.get("comparison"),
        "opportunities": analysis.get("opportunities"),
        "ads": {
            brand: [{"headline": ad.get("headline", ""), "ad_text": ad.get("ad_text", ""),
                     "themes": ad.get("creative_analysis", {}).get("themes", []),
                     "offers": ad.get("creative_analysis", {}).get("offer_signals", []),
                     "ctas": ad.get("creative_analysis", {}).get("cta_categories", []),
                     "source": ad.get("ad_library_url")}
                    for ad in ads[:15]]
            for brand, ads in analysis.get("ads", {}).items()
        },
    }
    prompt = """You are an evidence-first advertising strategy analyst. Analyze this JSON of public ad-library records and computed sample statistics. Return ONLY valid JSON with keys: executive_summary (string), observed_differences (array of objects with title, observation, evidence, caveat), experiment_plan (array of objects with hypothesis, variant_a, variant_b, primary_metric, guardrail_metric), data_limitations (array of strings). Use only evidence in input. Distinguish observed facts from hypotheses. Do not infer spend, impressions, CTR, conversions, or campaign effectiveness. If demo_mode is true, explicitly say the records are synthetic and do not describe real campaigns. Keep experiment ideas practical and testable.\n\nINPUT:\n""" + json.dumps(compact, ensure_ascii=False)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=15)) as client:
            response = await client.post(url, params={"key": settings.gemini_api_key}, json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
            })
        response.raise_for_status()
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        return {"enabled": True, "status": "completed", **parsed}
    except Exception as exc:
        # Preserve the core analysis if Gemini is unavailable/rate-limited.
        return {"enabled": True, "status": "error", "message": f"Gemini synthesis failed: {str(exc)[:240]}"}
