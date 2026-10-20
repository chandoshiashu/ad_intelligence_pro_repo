# Ad Intelligence — frontend + FastAPI + ML starter
Live website: https://frontend-eight-iota-0g6bcbi637.vercel.app/

This project bundle contains a runnable end-to-end starter:

- `frontend/app/page.tsx`: Ember Orange Next.js UI wired to `POST /analyze`.
- `backend/app/main.py`: FastAPI application and CORS.
- `backend/app/services/tinyfish.py`: TinyFish Web Agent adapter for public Meta Ad Library collection.
- `backend/app/services/gemini.py`: optional Gemini evidence-grounded synthesis and experiment plans.
- `backend/app/ml/features.py`: explainable rule-based creative feature extraction.
- `backend/app/ml/clustering.py`: exploratory TF-IDF + KMeans clusters (only when there is enough text).
- `backend/app/ml/recommendations.py`: sample-based experiment hypotheses.
- `backend/app/ml/pipeline.py`: orchestrates the analysis and returns structured JSON.

## 1. Run the backend locally

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The default `.env.example` uses `DEMO_MODE=true`, so the API can be tested without TinyFish credentials. Demo records are synthetic and are labelled as demo data in the response/UI.

Open `http://localhost:8000/docs` and try `POST /analyze` with:

```json
{"company":"Swiggy","competitor":"Zomato"}
```

## 2. Enable live TinyFish collection

1. Add your TinyFish API key to `backend/.env` as `TINYFISH_API_KEY=...`.
2. Set `DEMO_MODE=false`.
3. Restart FastAPI.

The adapter calls `POST https://agent.tinyfish.ai/v1/automation/run` with `X-API-Key`, a public Meta Ad Library search URL, and a structured extraction goal. Live results depend on TinyFish access, site behaviour, available public ads and the extraction response. A completed agent run does not guarantee that ads were found; inspect the response and warnings.

## 3. Enable Gemini strategic synthesis

1. Set `GEMINI_API_KEY` in `backend/.env`.
2. Optionally set `GEMINI_MODEL=gemini-2.5-flash` (or a model available to your key).
3. Restart FastAPI and run an analysis.

Gemini receives the collected ad text, computed summaries, and source URLs to generate a brief, evidence-linked observations, caveats and testable A/B experiment ideas. If Gemini is unavailable or rate-limited, the core analysis still returns with a status message. Never put API keys in frontend variables.

Do not expose `TINYFISH_API_KEY` in frontend variables. It must remain on the backend.

## 4. Run the frontend (this folder is a complete Next.js app)

Open a **second terminal** and run these commands from the project root:

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Open `http://localhost:3000`. Keep the backend running in the first terminal at `http://localhost:8000`. The `.env.local` file points the UI at the backend. If you use a non-default backend port, update `NEXT_PUBLIC_API_URL` and restart the frontend.

The frontend folder includes `package.json`, the Next.js App Router layout, global CSS, TypeScript, Tailwind, PostCSS and Next.js configuration. You do not need to create these files manually. On Windows you can also run `./start_frontend.ps1` from PowerShell; for the backend use `./start_backend.ps1`.

If package downloads time out, retry `npm install`; do not delete the source files.

## 5. Important limitations

- The rule-based NLP feature extractor is an explainable baseline, not a supervised performance-prediction model. TF-IDF/KMeans is fit to each collected batch rather than a pretrained domain model.
- TF-IDF/KMeans is exploratory clustering and can be unstable on small samples.
- No CTR, impressions, ad spend, conversions or ROI are fabricated or predicted.
- Public Meta Ad Library coverage is not guaranteed. The TinyFish agent may return no ads or incomplete fields; review live responses before a demo.
- Brand validation currently uses normalized name matching. Brands with complex naming/parent companies may require a stronger validation step.
- Demo mode returns clearly synthetic examples, never live advertiser facts.
- Google sign-in in the frontend is still a UI-only demo toggle. It does not authenticate a user; implement OAuth separately before production.
- Analyses are not persisted to a database in this release.

## API endpoints

- `GET /` — API status
- `GET /health` — configuration status (does not reveal the key)
- `POST /analyze` — collect/sample ads, normalize, analyze and compare
- `GET /docs` — interactive Swagger API docs
