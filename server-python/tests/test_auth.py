"""Tests for JWT authentication (login / refresh / me)."""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from api.handlers import register_exception_handlers
from api.routes.v1.auth_routes import router
from config.settings import get_settings


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/auth")
    return app


@pytest.fixture()
def client():
    return TestClient(_build_app())


def _login(client, username="admin", password="admin"):
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


def test_login_returns_token_pair(client):
    response = _login(client)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_in"] == get_settings().jwt_access_token_expire_minutes * 60


def test_login_rejects_bad_credentials(client):
    response = _login(client, username="admin", password="wrong")
    assert response.status_code == 401
    assert response.json()["error_code"] == "E4001"


def test_me_with_valid_access_token(client):
    token = _login(client).json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["sub"] == "casuya-operator"


def test_me_rejects_missing_or_bad_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "E4001"


def test_me_rejects_expired_token(client):
    settings = get_settings()
    expired = jose_jwt.encode(
        {
            "sub": "casuya-operator",
            "type": "access",
            "iat": int(time.time()) - 3600,
            "exp": int(time.time()) - 60,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "E4002"


def test_refresh_rotates_token_pair(client):
    refresh_token = _login(client).json()["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"] != refresh_token


def test_refresh_rejects_access_token(client):
    access_token = _login(client).json()["access_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "E4001"


def test_refresh_requires_bearer(client):
    assert client.post("/api/v1/auth/refresh").status_code == 401
