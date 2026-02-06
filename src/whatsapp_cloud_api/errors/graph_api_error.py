from __future__ import annotations

from typing import Any

from .categorize import ErrorCategory, categorize_error
from .retry import RetryHint, get_retry_hint


class GraphApiError(Exception):
    __slots__ = (
        "category",
        "code",
        "details",
        "error_data",
        "error_subcode",
        "fbtrace_id",
        "http_status",
        "raw",
        "retry",
        "type",
    )

    def __init__(
        self,
        message: str,
        *,
        http_status: int = 0,
        code: int | None = None,
        type_: str = "",
        details: str | None = None,
        error_subcode: int | None = None,
        fbtrace_id: str | None = None,
        error_data: dict[str, Any] | None = None,
        retry_after_header: str | None = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.type = type_
        self.details = details
        self.error_subcode = error_subcode
        self.fbtrace_id = fbtrace_id
        self.error_data = error_data
        self.raw = raw

        self.category: ErrorCategory = categorize_error(code, http_status)
        self.retry: RetryHint = get_retry_hint(self.category, retry_after_header)

    # ── helpers ──────────────────────────────────────────────────

    def is_auth_error(self) -> bool:
        return self.category == "authorization"

    def is_rate_limit(self) -> bool:
        return self.category == "throttling"

    def is_template_error(self) -> bool:
        return self.category == "template"

    def requires_token_refresh(self) -> bool:
        return self.retry.action == "refresh_token"

    # ── serialization ────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": str(self),
            "http_status": self.http_status,
            "code": self.code,
            "type": self.type,
            "category": self.category,
            "retry": {"action": self.retry.action, "retry_after_ms": self.retry.retry_after_ms},
            "fbtrace_id": self.fbtrace_id,
        }

    @classmethod
    def from_response(
        cls,
        http_status: int,
        body: dict[str, Any],
        *,
        retry_after_header: str | None = None,
    ) -> GraphApiError:
        err = body.get("error", body)
        return cls(
            message=err.get("message", "Unknown Graph API error"),
            http_status=http_status,
            code=err.get("code"),
            type_=err.get("type", ""),
            details=err.get("error_user_msg") or err.get("details"),
            error_subcode=err.get("error_subcode"),
            fbtrace_id=err.get("fbtrace_id"),
            error_data=err.get("error_data"),
            retry_after_header=retry_after_header,
            raw=body,
        )
