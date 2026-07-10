from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["phase"] == 1


def test_project_lifecycle() -> None:
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

    listed = client.get("/api/projects")
    assert listed.status_code == 200
    assert any(item["id"] == project_id for item in listed.json())

    deleted = client.delete(f"/api/projects/{project_id}")
    assert deleted.status_code == 204
