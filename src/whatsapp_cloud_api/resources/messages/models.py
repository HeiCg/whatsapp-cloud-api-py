"""Pydantic models for all outbound message types."""

from __future__ import annotations

import re
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_http_url(value: str) -> str:
    """Validate a string is an http/https URL without changing its type.

    Mirrors the JS ``z.string().url()`` intent while keeping the field a plain
    ``str`` on the wire (no ``HttpUrl`` coercion / trailing-slash rewrites).
    """
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("must be a valid http(s) URL")
    return value

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
    # extra="forbid": an unknown field (e.g. a misspelled/dropped `cards`) is a
    # validation error instead of being silently ignored and lost on the wire.
    model_config = ConfigDict(extra="forbid")

    type: str
    sub_type: str | None = None
    index: int | None = None
    parameters: list[dict[str, Any]] = []
    cards: list[TemplateCarouselCard] | None = None

    @model_validator(mode="after")
    def _validate_carousel(self) -> TemplateComponent:
        if self.type == "carousel":
            if not self.cards:
                raise ValueError("carousel component requires a non-empty 'cards' array")
        elif self.cards is not None:
            raise ValueError("'cards' is only allowed on carousel components")
        return self


class TemplateCarouselCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_index: int = Field(ge=0)
    components: list[TemplateComponent] = Field(min_length=1)

    @model_validator(mode="after")
    def _forbid_nested_carousel(self) -> TemplateCarouselCard:
        for component in self.components:
            if component.type == "carousel":
                raise ValueError(
                    "'carousel' is not supported inside carousel cards"
                )
        return self


# Resolve the forward reference between TemplateComponent and TemplateCarouselCard.
TemplateComponent.model_rebuild()


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
    mode: Literal["draft", "published"] | None = None
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


# ── Interactive carousel ─────────────────────────────────────────────

_CAROUSEL_MAX_CARD_BODY_CHARS = 160
_CAROUSEL_MAX_CARD_BODY_LINE_BREAKS = 2
_CAROUSEL_LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")


class CarouselHeaderMediaRef(BaseModel):
    id: str | None = None
    link: str | None = None

    @model_validator(mode="after")
    def _require_id_or_link(self) -> CarouselHeaderMediaRef:
        if not (self.id or self.link):
            raise ValueError("header media requires either id or link")
        return self


class CarouselImageHeader(BaseModel):
    type: Literal["image"] = "image"
    image: CarouselHeaderMediaRef


class CarouselVideoHeader(BaseModel):
    type: Literal["video"] = "video"
    video: CarouselHeaderMediaRef


class CarouselCardCtaAction(BaseModel):
    """CTA-URL action for a carousel card (mirrors the JS cta_url action)."""

    model_config = ConfigDict(extra="forbid")

    display_text: str = Field(min_length=1, max_length=20)
    url: str

    _check_url = field_validator("url")(_validate_http_url)


class CarouselCardQuickReplyAction(BaseModel):
    """Quick-reply action for a carousel card (reuses the reply button model)."""

    model_config = ConfigDict(extra="forbid")

    buttons: list[InteractiveButton] = Field(min_length=1)


class CarouselCard(BaseModel):
    card_index: int = Field(ge=0)
    header: CarouselImageHeader | CarouselVideoHeader
    body_text: str | None = Field(default=None, max_length=_CAROUSEL_MAX_CARD_BODY_CHARS)
    action: CarouselCardCtaAction | CarouselCardQuickReplyAction

    @field_validator("body_text")
    @classmethod
    def _check_body_line_breaks(cls, value: str | None) -> str | None:
        if value is not None:
            breaks = len(_CAROUSEL_LINE_BREAK_RE.findall(value))
            if breaks > _CAROUSEL_MAX_CARD_BODY_LINE_BREAKS:
                raise ValueError(
                    f"card body_text must include at most "
                    f"{_CAROUSEL_MAX_CARD_BODY_LINE_BREAKS} line breaks"
                )
        return value


class InteractiveCarouselMessage(BaseMessage):
    body_text: str = Field(min_length=1, max_length=1024)
    cards: list[CarouselCard] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def _validate_cards(self) -> InteractiveCarouselMessage:
        # 1. card_index must cover exactly 0..n-1 (mirrors the JS sorted check)
        actual = sorted(card.card_index for card in self.cards)
        if actual != list(range(len(self.cards))):
            raise ValueError("card_index values must be sequential from 0")

        # 2. homogeneous action structure across all cards
        def _signature(card: CarouselCard) -> str:
            if isinstance(card.action, CarouselCardCtaAction):
                return "cta_url"
            return f"quick_reply:{len(card.action.buttons)}"

        first_signature = _signature(self.cards[0])
        for card in self.cards:
            if _signature(card) != first_signature:
                raise ValueError("All carousel cards must use the same button structure")

        # 3. quick-reply ids unique across all cards
        quick_reply_ids = [
            button.id
            for card in self.cards
            if isinstance(card.action, CarouselCardQuickReplyAction)
            for button in card.action.buttons
        ]
        if len(set(quick_reply_ids)) != len(quick_reply_ids):
            raise ValueError("quick reply button ids must be unique across carousel cards")

        return self


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


# ── Interactive address ──────────────────────────────────────────────


class SavedAddress(BaseModel):
    id: str
    value: dict[str, Any] | None = None


class AddressParameters(BaseModel):
    country: str
    values: dict[str, Any] | None = None
    saved_addresses: list[SavedAddress] | None = None
    validation_errors: dict[str, Any] | None = None


class InteractiveAddressMessage(BaseMessage):
    body_text: str
    footer_text: str | None = Field(None, max_length=60)
    parameters: AddressParameters


# ── Interactive call permission ─────────────────────────────────────


class CallPermissionParameters(BaseModel):
    phone_number: str
    call_purpose: str | None = None


class InteractiveCallPermissionMessage(BaseMessage):
    body_text: str | None = None
    footer_text: str | None = Field(None, max_length=60)
    parameters: CallPermissionParameters


# ── Raw message (arbitrary payload) ─────────────────────────────────


class RawMessage(BaseModel):
    phone_number_id: str
    payload: dict[str, Any]


# ── Mark read ────────────────────────────────────────────────────────


class MarkReadInput(BaseModel):
    phone_number_id: str
    message_id: str
