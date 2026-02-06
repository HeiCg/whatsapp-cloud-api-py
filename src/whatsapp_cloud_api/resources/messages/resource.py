"""MessagesResource — all send* methods for WhatsApp message types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...types import SendMessageResponse
from .models import (
    AudioMessage,
    ContactsMessage,
    DocumentMessage,
    ImageMessage,
    InteractiveButtonsMessage,
    InteractiveCatalogMessage,
    InteractiveCtaUrlMessage,
    InteractiveFlowMessage,
    InteractiveListMessage,
    InteractiveLocationRequestMessage,
    InteractiveProductListMessage,
    InteractiveProductMessage,
    LocationMessage,
    MarkReadInput,
    ReactionMessage,
    StickerMessage,
    TemplateMessage,
    TextMessage,
    VideoMessage,
)

if TYPE_CHECKING:
    from ...client import WhatsAppClient


def _to_api_key(s: str) -> str:
    """Convert snake_case to camelCase for Meta API field names (limited scope)."""
    parts = s.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def _serialize(model: Any) -> dict[str, Any]:
    """Dump pydantic model to dict with snake_case keys, excluding None values."""
    return model.model_dump(exclude_none=True)


class MessagesResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

    # ── internal ─────────────────────────────────────────────────

    async def _send(
        self,
        phone_number_id: str,
        msg_type: str,
        payload: dict[str, Any],
    ) -> SendMessageResponse:
        body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": payload.pop("recipient_type", "individual"),
            "to": payload.pop("to"),
            "type": msg_type,
        }

        # move base fields out
        for field in ("context_message_id", "biz_opaque_callback_data"):
            val = payload.pop(field, None)
            if val is not None:
                body[field] = val

        payload.pop("phone_number_id", None)

        # remaining payload is the type-specific data
        if msg_type == "text":
            body["text"] = {
                "body": payload.pop("body"),
                "preview_url": payload.pop("preview_url", False),
            }
        elif msg_type == "reaction":
            body["reaction"] = payload.get("reaction", payload)
        elif msg_type == "interactive":
            body["interactive"] = payload
        else:
            body[msg_type] = payload.get(msg_type, payload)

        resp = await self._client.post(f"{phone_number_id}/messages", json=body)
        return SendMessageResponse.model_validate(resp)

    async def _send_interactive(
        self,
        interactive_type: str,
        phone_number_id: str,
        to: str,
        action: dict[str, Any],
        *,
        body_text: str | None = None,
        footer_text: str | None = None,
        header: dict[str, Any] | None = None,
        recipient_type: str = "individual",
        context_message_id: str | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        interactive: dict[str, Any] = {
            "type": interactive_type,
            "action": action,
        }
        if body_text is not None:
            interactive["body"] = {"text": body_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        if header:
            interactive["header"] = header

        api_body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        if context_message_id:
            api_body["context"] = {"message_id": context_message_id}
        if biz_opaque_callback_data:
            api_body["biz_opaque_callback_data"] = biz_opaque_callback_data

        resp = await self._client.post(f"{phone_number_id}/messages", json=api_body)
        return SendMessageResponse.model_validate(resp)

    # ── text ─────────────────────────────────────────────────────

    async def send_text(self, input: TextMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "text", data)

    # ── media messages ───────────────────────────────────────────

    async def send_image(self, input: ImageMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "image", data)

    async def send_audio(self, input: AudioMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "audio", data)

    async def send_video(self, input: VideoMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "video", data)

    async def send_document(self, input: DocumentMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "document", data)

    async def send_sticker(self, input: StickerMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "sticker", data)

    # ── location ─────────────────────────────────────────────────

    async def send_location(self, input: LocationMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "location", data)

    # ── contacts ─────────────────────────────────────────────────

    async def send_contacts(self, input: ContactsMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "contacts", data)

    # ── reaction ─────────────────────────────────────────────────

    async def send_reaction(self, input: ReactionMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "reaction", data)

    # ── template ─────────────────────────────────────────────────

    async def send_template(self, input: TemplateMessage) -> SendMessageResponse:
        data = _serialize(input)
        return await self._send(input.phone_number_id, "template", data)

    # ── interactive: buttons ─────────────────────────────────────

    async def send_interactive_buttons(
        self, input: InteractiveButtonsMessage
    ) -> SendMessageResponse:
        header = None
        if input.header:
            header = _serialize(input.header)

        action = {
            "buttons": [
                {"type": "reply", "reply": {"id": b.id, "title": b.title}}
                for b in input.buttons
            ]
        }
        return await self._send_interactive(
            "button",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            header=header,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: list ────────────────────────────────────────

    async def send_interactive_list(
        self, input: InteractiveListMessage
    ) -> SendMessageResponse:
        header = None
        if input.header:
            header = _serialize(input.header)

        sections = []
        for s in input.sections:
            rows = [_serialize(r) for r in s.rows]
            sec: dict[str, Any] = {"rows": rows}
            if s.title:
                sec["title"] = s.title
            sections.append(sec)

        action = {"button": input.button_text, "sections": sections}
        return await self._send_interactive(
            "list",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            header=header,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: product ─────────────────────────────────────

    async def send_interactive_product(
        self, input: InteractiveProductMessage
    ) -> SendMessageResponse:
        action = {
            "catalog_id": input.catalog_id,
            "product_retailer_id": input.product_retailer_id,
        }
        return await self._send_interactive(
            "product",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: product list ────────────────────────────────

    async def send_interactive_product_list(
        self, input: InteractiveProductListMessage
    ) -> SendMessageResponse:
        sections = []
        for s in input.sections:
            sections.append({
                "title": s.title,
                "product_items": [_serialize(p) for p in s.product_items],
            })

        action = {"catalog_id": input.catalog_id, "sections": sections}
        header = _serialize(input.header) if input.header else None

        return await self._send_interactive(
            "product_list",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            header=header,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: flow ────────────────────────────────────────

    async def send_interactive_flow(
        self, input: InteractiveFlowMessage
    ) -> SendMessageResponse:
        header = None
        if input.header:
            header = _serialize(input.header)

        params = _serialize(input.parameters)
        action = {"name": "flow", "parameters": params}

        return await self._send_interactive(
            "flow",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            header=header,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: CTA URL ─────────────────────────────────────

    async def send_interactive_cta_url(
        self, input: InteractiveCtaUrlMessage
    ) -> SendMessageResponse:
        header = None
        if input.header:
            header = _serialize(input.header)

        action = {
            "name": "cta_url",
            "parameters": _serialize(input.parameters),
        }
        return await self._send_interactive(
            "cta_url",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            header=header,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: location request ────────────────────────────

    async def send_interactive_location_request(
        self, input: InteractiveLocationRequestMessage
    ) -> SendMessageResponse:
        action = {
            "name": "send_location",
        }
        return await self._send_interactive(
            "location_request_message",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            footer_text=input.footer_text,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: catalog ─────────────────────────────────────

    async def send_interactive_catalog(
        self, input: InteractiveCatalogMessage
    ) -> SendMessageResponse:
        action: dict[str, Any] = {"name": "catalog_message"}
        if input.parameters and input.parameters.thumbnail_product_retailer_id:
            action["parameters"] = _serialize(input.parameters)

        return await self._send_interactive(
            "catalog_message",
            input.phone_number_id,
            input.to,
            action,
            body_text=input.body_text,
            recipient_type=input.recipient_type,
            context_message_id=input.context_message_id,
            biz_opaque_callback_data=input.biz_opaque_callback_data,
        )

    # ── interactive: raw ─────────────────────────────────────────

    async def send_interactive_raw(
        self,
        *,
        phone_number_id: str,
        to: str,
        interactive: dict[str, Any],
        recipient_type: str = "individual",
        context_message_id: str | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> SendMessageResponse:
        body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }
        if context_message_id:
            body["context"] = {"message_id": context_message_id}
        if biz_opaque_callback_data:
            body["biz_opaque_callback_data"] = biz_opaque_callback_data

        resp = await self._client.post(f"{phone_number_id}/messages", json=body)
        return SendMessageResponse.model_validate(resp)

    # ── mark read ────────────────────────────────────────────────

    async def mark_read(self, input: MarkReadInput) -> dict[str, Any]:
        body = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": input.message_id,
        }
        return await self._client.post(f"{input.phone_number_id}/messages", json=body)
