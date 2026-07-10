from fastapi.testclient import TestClient
from app.main import app, extract_sketchfab_url_from_embed, default_rubric

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "6.0"
    assert payload["uploads_writable"] is True
    assert payload["scorm_writable"] is True


def test_home_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "UCAN Reality Lab" in response.text


def test_rubric_totals_100():
    assert sum(row["points"] for row in default_rubric()) == 100


def test_sketchfab_embed_is_normalized():
    uid = "1234567890abcdef1234567890abcdef"
    embed = f'<iframe src="https://sketchfab.com/models/{uid}/embed"></iframe>'
    result = extract_sketchfab_url_from_embed(embed)
    assert f"/models/{uid}/embed" in result
