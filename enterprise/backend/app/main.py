from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = "11.0.0-standalone"

app = FastAPI(
    title="UCAN Reality Lab Standalone API",
    version=APP_VERSION,
    description="Backend stateless para autoría con IA. No utiliza login ni base de datos.",
)

configured_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
production_origins = [
    "https://ucan-reality-lab-web-v7.onrender.com",
    "https://eagarcia77.github.io",
    "http://localhost:8170",
    "http://127.0.0.1:8170",
]
allowed_origins = list(dict.fromkeys(configured_origins + production_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://[a-z0-9-]*ucan-reality-lab[a-z0-9-]*\.onrender\.com",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "ucan-reality-lab-standalone-api",
        "version": APP_VERSION,
        "database": "not-used",
        "authentication": "not-required",
        "ai_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "mode": "standalone-local-projects",
    }
