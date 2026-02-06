"""Tests for webhooks/verify.py — HMAC-SHA256 signature verification."""

import hashlib
import hmac

from whatsapp_cloud_api.webhooks.verify import verify_signature

APP_SECRET = "test_secret_key"


def _sign(body: bytes) -> str:
    """Compute the expected sha256=<hex> header value."""
    digest = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


class TestVerifySignature:
    def test_valid_signature(self):
        body = b'{"test": "data"}'
        sig = _sign(body)
        assert verify_signature(app_secret=APP_SECRET, raw_body=body, signature_header=sig) is True

    def test_invalid_signature(self):
        body = b'{"test": "data"}'
        assert (
            verify_signature(
                app_secret=APP_SECRET, raw_body=body, signature_header="sha256=badhex"
            )
            is False
        )

    def test_none_signature_header(self):
        assert (
            verify_signature(app_secret=APP_SECRET, raw_body=b"body", signature_header=None)
            is False
        )

    def test_empty_signature_header(self):
        assert (
            verify_signature(app_secret=APP_SECRET, raw_body=b"body", signature_header="") is False
        )

    def test_raw_body_as_string(self):
        body_str = '{"test": "data"}'
        body_bytes = body_str.encode("utf-8")
        sig = _sign(body_bytes)
        assert (
            verify_signature(app_secret=APP_SECRET, raw_body=body_str, signature_header=sig)
            is True
        )

    def test_signature_without_prefix(self):
        body = b"data"
        digest = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
        # Passing just the hex without sha256= prefix
        assert (
            verify_signature(app_secret=APP_SECRET, raw_body=body, signature_header=digest) is True
        )

    def test_wrong_secret(self):
        body = b"data"
        sig = _sign(body)
        assert (
            verify_signature(app_secret="wrong_secret", raw_body=body, signature_header=sig)
            is False
        )
