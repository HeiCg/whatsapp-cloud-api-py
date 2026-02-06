"""Dataclass events for WhatsApp webhook dispatching via pyventus."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Base ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class WhatsAppEvent:
    """Base for all WhatsApp webhook events."""

    phone_number_id: str | None = None


# ── Message events ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class MessageEvent(WhatsAppEvent):
    """Base for all inbound message events."""

    message_id: str = ""
    timestamp: str = ""
    from_number: str = ""
    context: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TextReceived(MessageEvent):
    body: str = ""
    preview_url: bool = False


@dataclass(frozen=True, slots=True)
class ImageReceived(MessageEvent):
    image_id: str = ""
    mime_type: str = ""
    sha256: str = ""
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class VideoReceived(MessageEvent):
    video_id: str = ""
    mime_type: str = ""
    sha256: str = ""
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class AudioReceived(MessageEvent):
    audio_id: str = ""
    mime_type: str = ""
    sha256: str = ""
    voice: bool = False


@dataclass(frozen=True, slots=True)
class DocumentReceived(MessageEvent):
    document_id: str = ""
    mime_type: str = ""
    sha256: str = ""
    filename: str | None = None
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class StickerReceived(MessageEvent):
    sticker_id: str = ""
    mime_type: str = ""
    animated: bool = False


@dataclass(frozen=True, slots=True)
class LocationReceived(MessageEvent):
    latitude: float = 0.0
    longitude: float = 0.0
    name: str | None = None
    address: str | None = None


@dataclass(frozen=True, slots=True)
class ContactsReceived(MessageEvent):
    contacts: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ReactionReceived(MessageEvent):
    emoji: str | None = None
    reacted_message_id: str = ""


# ── Interactive reply events ─────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ButtonReply(MessageEvent):
    button_id: str = ""
    button_title: str = ""


@dataclass(frozen=True, slots=True)
class ListReply(MessageEvent):
    list_id: str = ""
    list_title: str = ""
    list_description: str | None = None


@dataclass(frozen=True, slots=True)
class FlowResponse(MessageEvent):
    response_json: dict[str, Any] = field(default_factory=dict)
    flow_token: str | None = None


# ── Order ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class OrderReceived(MessageEvent):
    catalog_id: str = ""
    product_items: list[dict[str, Any]] = field(default_factory=list)
    order_text: str | None = None


# ── Status events ────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class StatusEvent(WhatsAppEvent):
    """Base for message status update events."""

    message_id: str = ""
    timestamp: str = ""
    recipient_id: str = ""
    conversation: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MessageSent(StatusEvent):
    pass


@dataclass(frozen=True, slots=True)
class MessageDelivered(StatusEvent):
    pass


@dataclass(frozen=True, slots=True)
class MessageRead(StatusEvent):
    pass


@dataclass(frozen=True, slots=True)
class MessageFailed(StatusEvent):
    errors: list[dict[str, Any]] = field(default_factory=list)


# ── System / catch-all ───────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class UnknownMessageReceived(MessageEvent):
    """Fired for any message type not explicitly mapped."""

    raw_type: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)
