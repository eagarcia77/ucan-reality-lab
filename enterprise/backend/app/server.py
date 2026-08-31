import os

from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .main import app
from .ai_routes import router as ai_router
from .authoring_routes import router as authoring_router
from .password_routes import router as password_router
from .admin_routes import projects_router as admin_projects_router
from .admin_routes import router as admin_router
from .database import get_db

# Production-safe CORS. This outer middleware complements the base configuration
# in main.py and prevents Render/GitHub Pages deployments from being blocked when
# CORS_ORIGINS was not updated in the environment after a frontend rename.
configured_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-UCAN-Version"],
)

app.include_router(ai_router)
app.include_router(authoring_router)
app.include_router(password_router)
app.include_router(admin_router)
app.include_router(admin_projects_router)


@app.get("/api/auth/login-readiness", tags=["Authentication"])
def login_readiness(db: Session = Depends(get_db)) -> dict:
    """Small unauthenticated diagnostic used by the login screen.

    It intentionally returns no secrets or account existence information.
    """
    db.execute(text("SELECT 1"))
    return {
        "ok": True,
        "authentication": "ready",
        "database": "connected",
        "frontend_origin_allowed": True,
    }
