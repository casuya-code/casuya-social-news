"""Tests for the storage backend (local disk + S3-compatible uploads)."""

from pathlib import Path

import pytest


def test_public_audio_url_builds_cdn_path():
    from storage.audio_store import public_audio_url

    url = public_audio_url("abc123", "00.wav")
    assert url == "http://localhost:8000/storage/abc123/00.wav"


def test_public_audio_url_ignores_trailing_slash():
    from storage.audio_store import public_audio_url

    url = public_audio_url("x", "01.wav")
    assert not url.startswith("//")
    assert "storage" in url


def test_publish_local_backend_returns_local_url(monkeypatch, tmp_path):
    """Default backend keeps the file local and returns the CDN URL."""
    from storage import audio_store

    monkeypatch.setattr(audio_store._settings, "storage_backend", "local")
    local = tmp_path / "00.wav"
    local.write_bytes(b"fake-wav")

    url = audio_store.publish_audio(local, "script-1")
    assert url == "http://localhost:8000/storage/script-1/00.wav"


def test_publish_s3_backend_uploads_and_returns_url(monkeypatch, tmp_path):
    """S3 backend uploads the file and returns the public URL."""
    from storage import audio_store

    monkeypatch.setattr(audio_store._settings, "storage_backend", "s3")
    monkeypatch.setattr(audio_store._settings, "aws_s3_bucket", "casuya-audio")
    local = tmp_path / "01.wav"
    local.write_bytes(b"fake-wav")

    uploaded: list[tuple[str, str, str]] = []

    def fake_upload(local_path: Path, key: str) -> None:
        uploaded.append((local_path.name, key, "casuya-audio"))

    monkeypatch.setattr(audio_store, "_upload_to_s3", fake_upload)

    url = audio_store.publish_audio(local, "script-9")
    assert url == "http://localhost:8000/storage/script-9/01.wav"
    assert uploaded == [("01.wav", "script-9/01.wav", "casuya-audio")]


def test_s3_upload_builds_client_and_uploads(monkeypatch, tmp_path):
    """The real uploader creates a boto3 client with the right args."""
    import importlib.util

    import storage.audio_store as audio_store

    has_boto3 = importlib.util.find_spec("boto3") is not None
    if not has_boto3:
        pytest.skip("boto3 not installed")

    local = tmp_path / "02.wav"
    local.write_bytes(b"fake-wav")

    calls = {}

    class FakeS3:
        def upload_file(self, path, bucket, key):
            calls.update(path=path, bucket=bucket, key=key)

    import boto3

    class FakeBoto3:
        @staticmethod
        def client(service, **kwargs):
            calls["service"] = service
            calls["kwargs"] = kwargs
            return FakeS3()

    monkeypatch.setattr(boto3, "client", FakeBoto3.client)
    monkeypatch.setattr(audio_store._settings, "aws_s3_bucket", "bkt")
    monkeypatch.setattr(audio_store._settings, "aws_s3_region", "eu-west-2")
    monkeypatch.setattr(audio_store._settings, "aws_access_key_id", "AKIA")
    monkeypatch.setattr(audio_store._settings, "aws_secret_access_key", "secret")

    audio_store._upload_to_s3(local, "script-1/02.wav")

    assert calls["service"] == "s3"
    assert calls["kwargs"]["region_name"] == "eu-west-2"
    assert calls["kwargs"]["aws_access_key_id"] == "AKIA"
    assert calls["kwargs"]["aws_secret_access_key"] == "secret"
    assert calls["path"] == str(local)
    assert calls["bucket"] == "bkt"
    assert calls["key"] == "script-1/02.wav"


def test_publish_s3_backend_requires_sdk(monkeypatch, tmp_path):
    """Without the S3 SDK installed, the uploader must fail loudly."""
    import importlib.util

    from storage import audio_store

    if importlib.util.find_spec("boto3") is not None:
        pytest.skip("boto3 installed; not exercising the missing-SDK path")

    monkeypatch.setattr(audio_store._settings, "storage_backend", "s3")
    local = tmp_path / "03.wav"
    local.write_bytes(b"fake-wav")

    with pytest.raises(ModuleNotFoundError):
        audio_store.publish_audio(local, "script-2")
