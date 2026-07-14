import os
from pathlib import Path

TEST_DB = Path("./test_ucan_password_workspace.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-key-for-password-workspace"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["ALLOWED_EMAIL_DOMAINS"] = "test.local"
os.environ.pop("SMTP_HOST", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.password_routes import _create_reset_token  # noqa: E402
from app.server import app  # noqa: E402


def test_password_reset_and_workspace_lifecycle() -> None:
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": "professor@test.local", "full_name": "Profesor Prueba", "password": "OriginalPass123!"},
        )
        assert registered.status_code == 201
        token = registered.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        forgot = client.post("/api/auth/forgot-password", json={"email": "professor@test.local"})
        assert forgot.status_code == 200
        assert "recibirá instrucciones" in forgot.json()["message"]
        assert forgot.json()["email_delivery_configured"] is False

        from app.database import SessionLocal
        from app.models import UserModel

        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.email == "professor@test.local").one()
            reset_token = _create_reset_token(user)

        reset = client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "NewPassword456!"})
        assert reset.status_code == 200
        assert client.post("/api/auth/login", json={"email": "professor@test.local", "password": "OriginalPass123!"}).status_code == 401
        assert client.post("/api/auth/login", json={"email": "professor@test.local", "password": "NewPassword456!"}).status_code == 200
        assert client.post("/api/auth/reset-password", json={"token": reset_token, "new_password": "AnotherPass789!"}).status_code == 400

        project = client.post(
            "/api/projects",
            headers=headers,
            json={"title": "Actividad visual", "course": "BIOL 1101", "description": "Célula", "academic_level": "Subgraduado"},
        ).json()
        project_id = project["id"]
        saved = client.put(
            f"/api/projects/{project_id}/workspace",
            headers=headers,
            json={"content": {"activityTitle": "Partes de la célula", "rubric": [{"name": "Contenido", "points": 100}]}, "quality_score": 90},
        )
        assert saved.status_code == 200
        assert saved.json()["quality_score"] == 90
        loaded = client.get(f"/api/projects/{project_id}/workspace", headers=headers)
        assert loaded.status_code == 200
        assert loaded.json()["content"]["activityTitle"] == "Partes de la célula"

    if TEST_DB.exists():
        TEST_DB.unlink()
