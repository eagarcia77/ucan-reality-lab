import os
from pathlib import Path

TEST_DB = Path("./test_ucan_enterprise.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_and_persistent_project_lifecycle() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True
        assert health.json()["database"] == "connected"

        created = client.post(
            "/api/projects",
            json={
                "title": "Actividad de anatomía",
                "course": "BIOL 1101",
                "description": "Proyecto piloto de la plataforma Enterprise.",
                "academic_level": "Subgraduado",
            },
        )
        assert created.status_code == 201
        project = created.json()
        project_id = project["id"]
        assert project["status"] == "draft"
        assert project["version"] == 1

        updated = client.patch(
            f"/api/projects/{project_id}",
            json={"status": "in_review", "title": "Actividad de anatomía revisada"},
        )
        assert updated.status_code == 200
        assert updated.json()["version"] == 2
        assert updated.json()["status"] == "in_review"

        fetched = client.get(f"/api/projects/{project_id}")
        assert fetched.status_code == 200
        assert fetched.json()["title"] == "Actividad de anatomía revisada"

        listed = client.get("/api/projects")
        assert listed.status_code == 200
        assert any(item["id"] == project_id for item in listed.json())

        deleted = client.delete(f"/api/projects/{project_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/projects/{project_id}").status_code == 404

    if TEST_DB.exists():
        TEST_DB.unlink()
