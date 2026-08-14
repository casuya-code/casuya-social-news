"""End-to-end API tests using FastAPI TestClient."""

import os

os.environ.setdefault("API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)

AUTH = {"X-API-Key": "test-key"}
NEWS = {
    "headline": "Bei ya mafuta ya kupanda wiki hii",
    "source": "Habari Leo",
    "url": "https://example.com/bei-mafuta",
}


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "casuya-social-news"


def test_health_requires_key():
    r = client.get("/api/v1/health")
    assert r.status_code == 401
    assert r.json()["error_code"] == "E4001"


def test_generate_requires_key():
    r = client.post("/api/v1/scripts/generate", json=NEWS)
    assert r.status_code == 401


def test_generate_with_operator_jwt():
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    r = client.post(
        "/api/v1/scripts/generate",
        json=NEWS,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["script"]["news_ref"]["headline"] == NEWS["headline"]


def test_generate_script():
    r = client.post("/api/v1/scripts/generate", json=NEWS, headers=AUTH)
    assert r.status_code == 200
    script = r.json()["script"]
    assert script["version"] == "1.0"
    assert script["news_ref"]["headline"] == NEWS["headline"]


def test_generate_audio():
    gen = client.post("/api/v1/scripts/generate", json=NEWS, headers=AUTH)
    script = gen.json()["script"]
    r = client.post("/api/v1/scripts/generate-audio", json={"script": script}, headers=AUTH)
    assert r.status_code == 200
    lines = r.json()["lines"]
    assert len(lines) == len(script["lines"])
    for line in lines:
        assert "audio_url" in line


def test_generate_audio_accepts_float_line_indices():
    """GDScript clients send floats for JSON ints — indices must be coerced."""
    gen = client.post("/api/v1/scripts/generate", json=NEWS, headers=AUTH)
    script = gen.json()["script"]
    for line in script["lines"]:
        line["index"] = float(line["index"])
    r = client.post("/api/v1/scripts/generate-audio", json={"script": script}, headers=AUTH)
    assert r.status_code == 200
    lines = r.json()["lines"]
    assert len(lines) == len(script["lines"])
    for line in lines:
        assert isinstance(line["index"], int)
        assert "audio_url" in line


def test_news_latest_requires_key():
    r = client.get("/api/v1/news/latest")
    assert r.status_code == 401


def test_news_latest_ok():
    r = client.get("/api/v1/news/latest", headers=AUTH)
    assert r.status_code == 200
    assert "articles" in r.json()


def test_news_refresh_ok():
    r = client.post("/api/v1/news/refresh", headers=AUTH)
    assert r.status_code == 200
    assert "scripts" in r.json()
