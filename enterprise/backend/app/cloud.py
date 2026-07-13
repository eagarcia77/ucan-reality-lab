from __future__ import annotations

import os
import time
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def normalize_database_url(raw_url: str | None) -> str:
    """Normalize database URLs supplied by cloud providers for SQLAlchemy + psycopg 3."""
    value = (raw_url or "").strip()
    if not value:
        return "sqlite:///./ucan_enterprise.db"
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://"):]
    return value


def masked_database_target(database_url: str) -> str:
    """Return a safe database target for logs without exposing credentials."""
    if database_url.startswith("sqlite"):
        return "sqlite-local"
    parsed = urlsplit(database_url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return urlunsplit((parsed.scheme, f"{host}{port}", f"/{database}", "", ""))


def wait_for_database(engine, attempts: int | None = None, delay_seconds: float | None = None) -> None:
    """Wait for a managed database to become reachable before application startup."""
    max_attempts = attempts or int(os.getenv("DB_CONNECT_ATTEMPTS", "12"))
    delay = delay_seconds or float(os.getenv("DB_CONNECT_DELAY_SECONDS", "5"))
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(delay)
    raise RuntimeError(f"No fue posible conectar con la base de datos después de {max_attempts} intentos") from last_error
