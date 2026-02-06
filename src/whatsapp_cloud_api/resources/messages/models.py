"""Pydantic models for all outbound message types."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Base ─────────────────────────────────────────────────────────────


class BaseMessage(BaseModel):
    phone_number_id: str
    to: str
    recipient_type: Literal["individual", "group"] = "individual"
    context_message_id: str | None = None
    biz_opaque_callback_data: str | None = Field(None, max_length=512)


# ── Text ─────────────────────────────────────────────────────────────


class TextMessage(BaseMessage):
    body: str
    preview_url: bool = False


# ── Media payloads ───────────────────────────────────────────────────


class MediaById(BaseModel):
    id: str
    caption: str | None = None


class MediaByLink(BaseModel):
    link: str
    caption: str | None = None


class ImageMessage(BaseMessage):
    image: MediaById | MediaByLink


class AudioPayloadById(BaseModel):
    id: str
    voice: bool | None = None


class AudioPayloadByLink(BaseModel):
    link: str
    voice: bool | None = None


class AudioMessage(BaseMessage):
    audio: AudioPayloadById | AudioPayloadByLink


class VideoMessage(BaseMessage):
    video: MediaById | MediaByLink


class DocumentPayloadById(BaseModel):
    id: str
    caption: str | None = None
    filename: str | None = Field(None, max_length=240)


class DocumentPayloadByLink(BaseModel):
    link: str
    caption: str | None = None
    filename: str | None = Field(None, max_length=240)


class DocumentMessage(BaseMessage):
    document: DocumentPayloadById | DocumentPayloadByLink


class StickerById(BaseModel):
    id: str


class StickerByLink(BaseModel):
    link: str


class StickerMessage(BaseMessage):
    sticker: StickerById | StickerByLink


# ── Location ─────────────────────────────────────────────────────────


class LocationPayload(BaseModel):
    latitude: float
    longitude: float
    name: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=300)


class LocationMessage(BaseMessage):
    location: LocationPayload


# ── Contacts ─────────────────────────────────────────────────────────


class ContactName(BaseModel):
    formatted_name: str
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    suffix: str | None = None
    prefix: str | None = None


class ContactAddress(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    country_code: str | None = None
    type: str | None = None


class ContactEmail(BaseModel):
    email: str | None = None
    type: str | None = None


class ContactOrg(BaseModel):
    company: str | None = None
    department: str | None = None
    title: str | None = None


class ContactPhone(BaseModel):
    phone: str | None = None
    wa_id: str | None = None
    type: str | None = None


class ContactUrl(BaseModel):
    url: str | None = None
    type: str | None = None


class Contact(BaseModel):
    name: ContactName
    birthday: str | None = None
    addresses: list[ContactAddress] | None = None
    emails: list[ContactEmail] | None = None
    org: ContactOrg | None = None
    phones: list[ContactPhone] | None = None
    urls: list[ContactUrl] | None = None


class ContactsMessage(BaseMessage):
    contacts: list[Contact]


# ── Reaction ─────────────────────────────────────────────────────────


class ReactionPayload(BaseModel):
    message_id: str
    emoji: str | None = None


class ReactionMessage(BaseMessage):
    reaction: ReactionPayload


# ── Template ─────────────────────────────────────────────────────────


class TemplateLanguage(BaseModel):
    code: str
    policy: str | None = None


class TemplateComponent(BaseModel):
    type: str
    sub_type: str | None = None
    index: int | None = None
    parameters: list[dict[str, Any]] = []


class TemplatePayload(BaseModel):
    name: str
    language: TemplateLanguage
    components: list[TemplateComponent] | None = None


class TemplateMessage(BaseMessage):
    template: TemplatePayload


# ── Interactive common ───────────────────────────────────────────────


class InteractiveHeader(BaseModel):
    type: Literal["text", "image", "video", "document"]
    text: str | None = None
    image: dict[str, str] | None = None
    video: dict[str, str] | None = None
    document: dict[str, str] | None = None


class InteractiveButton(BaseModel):
    id: str = Field(max_length=256)
    title: str = Field(max_length=20)


class InteractiveButtonsMessage(BaseMessage):
    body_text: str = Field(max_length=1024)
    footer_text: str | None = Field(None, max_length=60)
    header: InteractiveHeader | None = None
    buttons: list[InteractiveButton] = Field(min_length=1, max_length=3)


# ── Interactive list ─────────────────────────────────────────────────


class ListRow(BaseModel):
    id: str = Field(max_length=200)
    title: str = Field(max_length=24)
    description: str | None = Field(None, max_length=72)


class ListSection(BaseModel):
    title: str | None = Field(None, max_length=24)
    rows: list[ListRow] = Field(min_length=1, max_length=10)


class InteractiveListMessage(BaseMessage):
    body_text: str = Field(max_length=4096)
    button_text: str = Field(max_length=20)
    header: InteractiveHeader | None = None
    footer_text: str | None = Field(None, max_length=60)
    sections: list[ListSection] = Field(min_length=1, max_length=10)


# ── Interactive product ──────────────────────────────────────────────


class InteractiveProductMessage(BaseMessage):
    body_text: str | None = Field(None, max_length=1024)
    footer_text: str | None = Field(None, max_length=60)
    catalog_id: str
    product_retailer_id: str


class ProductItem(BaseModel):
    product_retailer_id: str


class ProductSection(BaseModel):
    title: str = Field(max_length=24)
    product_items: list[ProductItem] = Field(min_length=1, max_length=30)


class InteractiveProductListMessage(BaseMessage):
    body_text: str = Field(max_length=1024)
    footer_text: str | None = None
    header: InteractiveHeader
    catalog_id: str
    sections: list[ProductSection] = Field(min_length=1, max_length=10)


# ── Interactive flow ─────────────────────────────────────────────────


class FlowParameters(BaseModel):
    flow_id: str
    flow_cta: str = Field(max_length=20)
    flow_message_version: str = "3"
    flow_token: str | None = None
    flow_action: Literal["navigate", "data_exchange"] | None = None
    flow_action_payload: dict[str, Any] | None = None


class InteractiveFlowMessage(BaseMessage):
    body_text: str = Field(max_length=1024)
    footer_text: str | None = None
    header: InteractiveHeader | None = None
    parameters: FlowParameters


# ── Interactive CTA URL ──────────────────────────────────────────────


class CtaUrlParameters(BaseModel):
    display_text: str = Field(max_length=20)
    url: str


class InteractiveCtaUrlMessage(BaseMessage):
    body_text: str = Field(max_length=1024)
    header: InteractiveHeader | None = None
    footer_text: str | None = None
    parameters: CtaUrlParameters


# ── Interactive location request ─────────────────────────────────────


class LocationRequestParameters(BaseModel):
    request_message: str = Field(max_length=1024)


class InteractiveLocationRequestMessage(BaseMessage):
    body_text: str = Field(max_length=1024)
    footer_text: str | None = None
    parameters: LocationRequestParameters


# ── Interactive catalog ──────────────────────────────────────────────


class CatalogParameters(BaseModel):
    thumbnail_product_retailer_id: str | None = None


class InteractiveCatalogMessage(BaseMessage):
    body_text: str | None = Field(None, max_length=1024)
    parameters: CatalogParameters | None = None


# ── Mark read ────────────────────────────────────────────────────────


class MarkReadInput(BaseModel):
    phone_number_id: str
    message_id: str
