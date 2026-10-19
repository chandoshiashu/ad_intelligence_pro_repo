
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.analyze import router as analyze_router


app = FastAPI(
    title="Ad Intelligence API",
    description="Evidence-aware competitor advertising analysis API.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/")
def root():
    return {
        "name": "Ad Intelligence API",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "tinyfish_configured": bool(settings.tinyfish_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
    }
