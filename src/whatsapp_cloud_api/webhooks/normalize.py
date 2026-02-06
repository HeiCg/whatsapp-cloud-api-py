"""Normalize Meta webhook payloads into a flat, easy-to-consume structure."""

from __future__ import annotations

from typing import Any

from ..types import MessageStatusUpdate, NormalizedWebhook, WebhookMessage
from ..utils.case import to_snake_deep


def normalize_webhook(payload: Any) -> NormalizedWebhook:
    """Normalize a raw Meta webhook payload into a unified structure.

    Flattens the deeply nested Graph API webhook format into top-level lists
    of messages, statuses, and contacts. All keys are converted to snake_case.

    Args:
        payload: The parsed JSON body of the webhook request.

    Returns:
        NormalizedWebhook with messages, statuses, contacts, and raw fields.
    """
    if not isinstance(payload, dict):
        return NormalizedWebhook()

    obj = payload.get("object")
    entries = payload.get("entry", [])

    all_messages: list[WebhookMessage] = []
    all_statuses: list[MessageStatusUpdate] = []
    all_contacts: list[dict[str, Any]] = []
    raw: dict[str, list[dict[str, Any]]] = {}
    phone_number_id: str | None = None
    display_phone_number: str | None = None

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            field = change.get("field", "")

            if field != "messages":
                raw.setdefault(field, []).append(to_snake_deep(value))
                continue

            metadata = value.get("metadata", {})
            if not phone_number_id:
                phone_number_id = metadata.get("phone_number_id")
                display_phone_number = metadata.get("display_phone_number")

            # Contacts
            for c in value.get("contacts", []):
                all_contacts.append(to_snake_deep(c))

            # Messages
            for msg in value.get("messages", []):
                normalized = to_snake_deep(msg)
                # Determine direction
                if "from" in normalized:
                    normalized.setdefault("from_", normalized.pop("from", None))

                all_messages.append(WebhookMessage.model_validate(normalized))

            # Statuses
            for status in value.get("statuses", []):
                normalized = to_snake_deep(status)
                all_statuses.append(MessageStatusUpdate.model_validate(normalized))

    return NormalizedWebhook(
        object=obj,
        phone_number_id=phone_number_id,
        display_phone_number=display_phone_number,
        contacts=all_contacts,
        messages=all_messages,
        statuses=all_statuses,
        raw=raw,
    )
