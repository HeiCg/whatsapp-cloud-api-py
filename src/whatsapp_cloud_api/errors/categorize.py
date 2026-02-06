from __future__ import annotations

from typing import Literal

ErrorCategory = Literal[
    "authorization",
    "permission",
    "parameter",
    "throttling",
    "template",
    "media",
    "phone_registration",
    "integrity",
    "business_eligibility",
    "reengagement_window",
    "waba_config",
    "flow",
    "synchronization",
    "server",
    "unknown",
]

_CODE_TO_CATEGORY: dict[int, ErrorCategory] = {
    # Authorization
    0: "authorization",
    190: "authorization",
    # Permission
    10: "permission",
    200: "permission",
    299: "permission",
    # Throttling / rate-limit
    4: "throttling",
    80007: "throttling",
    130429: "throttling",
    131048: "throttling",
    131056: "throttling",
    # Parameter
    33: "parameter",
    100: "parameter",
    130472: "parameter",
    131008: "parameter",
    131009: "parameter",
    131021: "parameter",
    131026: "parameter",
    135000: "parameter",
    # Media
    131051: "media",
    131052: "media",
    131053: "media",
    # Template
    132000: "template",
    132001: "template",
    132005: "template",
    132007: "template",
    132012: "template",
    132015: "template",
    132016: "template",
    # Flow
    132068: "flow",
    132069: "flow",
    # Phone registration
    133000: "phone_registration",
    133004: "phone_registration",
    133005: "phone_registration",
    133006: "phone_registration",
    133008: "phone_registration",
    133009: "phone_registration",
    133010: "phone_registration",
    133015: "phone_registration",
    133016: "phone_registration",
    # Re-engagement window
    131047: "reengagement_window",
    # Integrity
    368: "integrity",
    130497: "integrity",
    131031: "integrity",
}


def categorize_error(code: int | None, http_status: int | None = None) -> ErrorCategory:
    if code is not None and code in _CODE_TO_CATEGORY:
        return _CODE_TO_CATEGORY[code]
    if http_status is not None and http_status >= 500:
        return "server"
    return "unknown"
