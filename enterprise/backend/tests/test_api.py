import os
from pathlib import Path

TEST_DB = Path("./test_ucan_enterprise.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-key-for-automated-tests"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["ADMIN_SYNC_PASSWORD"] = "true"
os.environ["ALLOWED_EMAIL_DOMAINS"] = "test.local"

from fastapi.testclient import TestClient  # noqa: E402
from app.server import app  # noqa: E402


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_auth_roles_and_persistent_project_lifecycle() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True
        assert health.json()["version"] == "8.0.0-lts"
        assert health.json()["increment"] == "v8-lts-auth-and-authoring"

        assert client.get("/api/projects").status_code == 401
        admin_headers = login(client, "admin@test.local", "TestPassword123!")

        professor = client.post(
            "/api/users",
            headers=admin_headers,
            json={"email": "professor@test.local", "full_name": "Profesora Prueba", "password": "Professor123!", "role": "professor"},
        )
        assert professor.status_code == 201
        professor_headers = login(client, "professor@test.local", "Professor123!")

        created = client.post(
            "/api/projects",
            headers=professor_headers,
            json={"title": "Actividad de anatomía", "course": "BIOL 1101", "description": "Proyecto piloto.", "academic_level": "Subgraduado"},
        )
        assert created.status_code == 201
        project = created.json()
        project_id = project["id"]
        assert project["status"] == "draft"
        assert project["version"] == 1

        workspace = client.put(
            f"/api/projects/{project_id}/workspace",
            headers=professor_headers,
            json={"content": {"activityTitle": "Actividad creada"}, "quality_score": 90},
        )
        assert workspace.status_code == 200
        assert workspace.json()["content"]["activityTitle"] == "Actividad creada"

        updated = client.patch(
            f"/api/projects/{project_id}",
            headers=professor_headers,
            json={"status": "in_review", "title": "Actividad de anatomía revisada"},
        )
        assert updated.status_code == 200
        assert updated.json()["version"] >= 2

        deleted = client.delete(f"/api/projects/{project_id}", headers=professor_headers)
        assert deleted.status_code == 204

    if TEST_DB.exists():
        TEST_DB.unlink()
