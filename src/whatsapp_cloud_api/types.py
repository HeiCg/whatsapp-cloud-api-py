from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )


# ── Send message response ──────────────────────────────────────────


class ContactInfo(CamelModel):
    input: str
    wa_id: str


class MessageInfo(CamelModel):
    id: str
    message_status: str | None = None


class SendMessageResponse(CamelModel):
    messaging_product: Literal["whatsapp"] = "whatsapp"
    contacts: list[ContactInfo] = []
    messages: list[MessageInfo] = []


# ── Paging ──────────────────────────────────────────────────────────


class PagingCursors(CamelModel):
    before: str | None = None
    after: str | None = None


class Paging(CamelModel):
    cursors: PagingCursors = PagingCursors()
    next: str | None = None
    previous: str | None = None


class PagedResponse(CamelModel):
    data: list[dict[str, Any]] = []
    paging: Paging = Paging()


# ── Media ───────────────────────────────────────────────────────────


class MediaUploadResponse(CamelModel):
    id: str


class MediaMetadata(CamelModel):
    messaging_product: Literal["whatsapp"] = "whatsapp"
    url: str
    mime_type: str
    sha256: str
    file_size: str
    id: str


# ── Templates ───────────────────────────────────────────────────────


class MessageTemplate(CamelModel):
    id: str
    name: str
    category: str | None = None
    language: str | None = None
    status: str | None = None
    components: list[dict[str, Any]] | None = None
    quality_score_category: str | None = None
    last_updated_time: str | None = None


class TemplateListResponse(CamelModel):
    data: list[MessageTemplate] = []
    paging: Paging = Paging()


class TemplateCreateResponse(CamelModel):
    id: str
    status: str | None = None
    category: str | None = None


class TemplateDeleteResponse(CamelModel):
    success: bool


# ── Phone numbers ───────────────────────────────────────────────────


class BusinessProfile(CamelModel):
    about: str | None = None
    address: str | None = None
    description: str | None = None
    email: str | None = None
    profile_picture_url: str | None = None
    websites: list[str] | None = None
    vertical: str | None = None
    messaging_product: str | None = None


class BusinessProfileResponse(CamelModel):
    data: list[BusinessProfile] = []


# ── Webhooks ────────────────────────────────────────────────────────


class WebhookContact(CamelModel):
    wa_id: str | None = None
    profile: dict[str, Any] | None = None


class WebhookMessageContext(CamelModel):
    id: str | None = None
    from_: str | None = None
    referred_product: dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
    )


class WebhookMessage(CamelModel):
    id: str
    type: str
    timestamp: str
    from_: str | None = None
    to: str | None = None
    context: WebhookMessageContext | None = None
    text: dict[str, Any] | None = None
    image: dict[str, Any] | None = None
    video: dict[str, Any] | None = None
    audio: dict[str, Any] | None = None
    document: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    interactive: dict[str, Any] | None = None
    template: dict[str, Any] | None = None
    order: dict[str, Any] | None = None
    sticker: dict[str, Any] | None = None
    contacts: list[dict[str, Any]] | None = None
    reaction: dict[str, Any] | None = None
    button: dict[str, Any] | None = None
    referral: dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        extra="allow",
    )


class MessageStatusUpdate(CamelModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str | None = None
    conversation: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        extra="allow",
    )


class NormalizedWebhook(CamelModel):
    object: str | None = None
    phone_number_id: str | None = None
    display_phone_number: str | None = None
    contacts: list[dict[str, Any]] = []
    messages: list[WebhookMessage] = []
    statuses: list[MessageStatusUpdate] = []
    raw: dict[str, list[dict[str, Any]]] = {}

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        extra="allow",
    )


# ── Calls ───────────────────────────────────────────────────────────


class CallConnectResponse(CamelModel):
    id: str | None = None
    session: dict[str, Any] | None = None


class CallActionResponse(CamelModel):
    success: bool = True
