from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Literal

from .categorize import ErrorCategory

RetryAction = Literal[
    "retry",
    "retry_after",
    "fix_and_retry",
    "do_not_retry",
    "refresh_token",
]


@dataclass(frozen=True, slots=True)
class RetryHint:
    action: RetryAction
    retry_after_ms: int | None = None


_CATEGORY_RETRY: dict[ErrorCategory, RetryAction] = {
    "authorization": "refresh_token",
    "permission": "fix_and_retry",
    "parameter": "fix_and_retry",
    "throttling": "retry_after",
    "template": "fix_and_retry",
    "media": "fix_and_retry",
    "phone_registration": "fix_and_retry",
    "integrity": "do_not_retry",
    "business_eligibility": "do_not_retry",
    "reengagement_window": "do_not_retry",
    "waba_config": "fix_and_retry",
    "flow": "fix_and_retry",
    "synchronization": "retry",
    "server": "retry",
    "unknown": "retry",
}


def get_retry_hint(
    category: ErrorCategory,
    retry_after_header: str | None = None,
) -> RetryHint:
    action = _CATEGORY_RETRY.get(category, "retry")

    retry_after_ms: int | None = None
    if retry_after_header is not None:
        with contextlib.suppress(ValueError, TypeError):
            retry_after_ms = int(float(retry_after_header) * 1000)

    if action == "retry_after" and retry_after_ms is None:
        retry_after_ms = 60_000  # default 60s

    return RetryHint(action=action, retry_after_ms=retry_after_ms)
