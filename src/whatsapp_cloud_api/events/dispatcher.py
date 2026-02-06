"""Dispatch normalized webhook payloads as typed pyventus events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..types import NormalizedWebhook, WebhookMessage
from .events import (
    AudioReceived,
    ButtonReply,
    ContactsReceived,
    DocumentReceived,
    FlowResponse,
    ImageReceived,
    ListReply,
    LocationReceived,
    MessageDelivered,
    MessageFailed,
    MessageRead,
    MessageSent,
    OrderReceived,
    ReactionReceived,
    StickerReceived,
    TextReceived,
    UnknownMessageReceived,
    VideoReceived,
    WhatsAppEvent,
)

if TYPE_CHECKING:
    from pyventus.events import EventEmitter


def _base_kwargs(msg: WebhookMessage, phone_number_id: str | None) -> dict[str, Any]:
    ctx = None
    if msg.context:
        ctx = msg.context.model_dump(exclude_none=True)

    return {
        "phone_number_id": phone_number_id,
        "message_id": msg.id,
        "timestamp": msg.timestamp,
        "from_number": msg.from_ or "",
        "context": ctx or None,
    }


def _map_message(msg: WebhookMessage, phone_number_id: str | None) -> WhatsAppEvent:
    """Convert a single WebhookMessage into a typed event."""
    base = _base_kwargs(msg, phone_number_id)

    match msg.type:
        case "text":
            text = msg.text or {}
            return TextReceived(**base, body=text.get("body", ""))

        case "image":
            img = msg.image or {}
            return ImageReceived(
                **base,
                image_id=img.get("id", ""),
                mime_type=img.get("mime_type", ""),
                sha256=img.get("sha256", ""),
                caption=img.get("caption"),
            )

        case "video":
            vid = msg.video or {}
            return VideoReceived(
                **base,
                video_id=vid.get("id", ""),
                mime_type=vid.get("mime_type", ""),
                sha256=vid.get("sha256", ""),
                caption=vid.get("caption"),
            )

        case "audio":
            aud = msg.audio or {}
            return AudioReceived(
                **base,
                audio_id=aud.get("id", ""),
                mime_type=aud.get("mime_type", ""),
                sha256=aud.get("sha256", ""),
                voice=aud.get("voice", False),
            )

        case "document":
            doc = msg.document or {}
            return DocumentReceived(
                **base,
                document_id=doc.get("id", ""),
                mime_type=doc.get("mime_type", ""),
                sha256=doc.get("sha256", ""),
                filename=doc.get("filename"),
                caption=doc.get("caption"),
            )

        case "sticker":
            stk = msg.sticker or {}
            return StickerReceived(
                **base,
                sticker_id=stk.get("id", ""),
                mime_type=stk.get("mime_type", ""),
                animated=stk.get("animated", False),
            )

        case "location":
            loc = msg.location or {}
            return LocationReceived(
                **base,
                latitude=loc.get("latitude", 0.0),
                longitude=loc.get("longitude", 0.0),
                name=loc.get("name"),
                address=loc.get("address"),
            )

        case "contacts":
            return ContactsReceived(**base, contacts=msg.contacts or [])

        case "reaction":
            rxn = msg.reaction or {}
            return ReactionReceived(
                **base,
                emoji=rxn.get("emoji"),
                reacted_message_id=rxn.get("message_id", ""),
            )

        case "interactive":
            return _map_interactive(msg, base)

        case "order":
            order = msg.order or {}
            return OrderReceived(
                **base,
                catalog_id=order.get("catalog_id", ""),
                product_items=order.get("product_items", []),
                order_text=order.get("order_text"),
            )

        case _:
            return UnknownMessageReceived(
                **base,
                raw_type=msg.type,
                raw_data=msg.model_dump(exclude_none=True),
            )


def _map_interactive(msg: WebhookMessage, base: dict[str, Any]) -> WhatsAppEvent:
    """Map interactive reply messages to specific event types."""
    interactive = msg.interactive or {}
    itype = interactive.get("type", "")

    if itype == "button_reply":
        reply = interactive.get("button_reply", {})
        return ButtonReply(
            **base,
            button_id=reply.get("id", ""),
            button_title=reply.get("title", ""),
        )

    if itype == "list_reply":
        reply = interactive.get("list_reply", {})
        return ListReply(
            **base,
            list_id=reply.get("id", ""),
            list_title=reply.get("title", ""),
            list_description=reply.get("description"),
        )

    if itype == "nfm_reply":
        reply = interactive.get("nfm_reply", {})
        response_json = reply.get("response_json", {})
        if isinstance(response_json, str):
            import json

            try:
                response_json = json.loads(response_json)
            except (json.JSONDecodeError, TypeError):
                response_json = {}
        return FlowResponse(
            **base,
            response_json=response_json,
            flow_token=reply.get("flow_token"),
        )

    return UnknownMessageReceived(
        **base,
        raw_type=f"interactive:{itype}",
        raw_data=interactive,
    )


def dispatch_webhook(webhook: NormalizedWebhook, emitter: EventEmitter) -> None:
    """Dispatch all events from a normalized webhook payload.

    Args:
        webhook: The normalized webhook payload from ``normalize_webhook()``.
        emitter: A pyventus ``EventEmitter`` instance (e.g. ``AsyncIOEventEmitter()``
                 or ``FastAPIEventEmitter``).
    """
    pid = webhook.phone_number_id

    # Messages
    for msg in webhook.messages:
        event = _map_message(msg, pid)
        emitter.emit(event)

    # Statuses
    for status in webhook.statuses:
        base = {
            "phone_number_id": pid,
            "message_id": status.id,
            "timestamp": status.timestamp,
            "recipient_id": status.recipient_id or "",
            "conversation": status.conversation,
            "pricing": status.pricing,
        }

        match status.status:
            case "sent":
                emitter.emit(MessageSent(**base))
            case "delivered":
                emitter.emit(MessageDelivered(**base))
            case "read":
                emitter.emit(MessageRead(**base))
            case "failed":
                emitter.emit(MessageFailed(**base, errors=status.errors or []))
            case _:
                emitter.emit(MessageSent(**base))
