"""Audio storage backend: local disk or S3-compatible object storage.

The TTS providers always write to a local file first (they need a real
path). This module then decides what happens next:

  - backend "local" (default): the file already lives under the static
    storage dir; we just build the CDN URL.
  - backend "s3": upload the file to the configured bucket and return a
    public URL (CDN base + object key).

`cdn_base_url` is the public prefix in both cases (e.g. a CloudFront
distribution pointing at the bucket, or the static mount on the API host).
"""

from __future__ import annotations

from pathlib import Path

from config.logging_config import get_logger
from config.settings import get_settings

_logger = get_logger("storage.audio")

_settings = get_settings()


def public_audio_url(script_id: str, filename: str) -> str:
    """Client-facing URL for an audio object."""
    base = _settings.cdn_base_url.rstrip("/")
    return f"{base}/{script_id}/{filename}"


def publish_audio(local_path: Path, script_id: str) -> str:
    """Publish a synthesized file and return its public URL."""
    filename = local_path.name
    if _settings.storage_backend == "s3":
        key = f"{script_id}/{filename}"
        _upload_to_s3(local_path, key)
        _logger.info("audio_uploaded_to_s3", key=key, bucket=_settings.aws_s3_bucket)
    return public_audio_url(script_id, filename)


def _upload_to_s3(local_path: Path, key: str) -> None:
    """Upload one file to the configured S3 bucket.

    boto3 is imported lazily so the S3 SDK is only required when the
    backend is s3.
    """
    import boto3  # noqa: PLC0415 - lazy import, S3-only dependency

    s3 = boto3.client(
        "s3",
        region_name=_settings.aws_s3_region,
        aws_access_key_id=_settings.aws_access_key_id,
        aws_secret_access_key=_settings.aws_secret_access_key,
    )
    s3.upload_file(str(local_path), _settings.aws_s3_bucket, key)
