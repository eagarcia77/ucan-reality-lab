from app.cloud import masked_database_target, normalize_database_url


def test_normalize_render_postgresql_url() -> None:
    raw = "postgresql://ucan:secret@internal-host/ucan"
    assert normalize_database_url(raw) == "postgresql+psycopg://ucan:secret@internal-host/ucan"


def test_normalize_legacy_postgres_url() -> None:
    raw = "postgres://ucan:secret@internal-host/ucan"
    assert normalize_database_url(raw) == "postgresql+psycopg://ucan:secret@internal-host/ucan"


def test_preserve_sqlite_url() -> None:
    assert normalize_database_url("sqlite:///./test.db") == "sqlite:///./test.db"


def test_mask_database_target() -> None:
    target = masked_database_target("postgresql+psycopg://ucan:secret@internal-host:5432/ucan")
    assert "secret" not in target
    assert "internal-host:5432/ucan" in target
