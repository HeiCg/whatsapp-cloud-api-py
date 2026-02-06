"""Webhook signature verification using HMAC-SHA256."""

from __future__ import annotations

import hashlib
import hmac


def verify_signature(
    *,
    app_secret: str,
    raw_body: bytes | str,
    signature_header: str | None,
) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta webhook requests.

    Args:
        app_secret: Your Meta App Secret.
        raw_body: The raw request body bytes.
        signature_header: Value of the X-Hub-Signature-256 header.

    Returns:
        True if the signature is valid.
    """
    if not signature_header:
        return False

    try:
        if isinstance(raw_body, str):
            raw_body = raw_body.encode("utf-8")

        expected = hmac.new(
            app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        # Header format: "sha256=<hex>"
        received = signature_header.removeprefix("sha256=")

        return hmac.compare_digest(expected, received)
    except Exception:
        return False
