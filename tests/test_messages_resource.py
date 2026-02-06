"""Tests for resources/messages/resource.py — MessagesResource send methods."""

from __future__ import annotations

import httpx
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.messages.models import (
    CatalogParameters,
    ImageMessage,
    InteractiveButton,
    InteractiveButtonsMessage,
    InteractiveCatalogMessage,
    InteractiveListMessage,
    ListRow,
    ListSection,
    MarkReadInput,
    MediaById,
    MediaByLink,
    TextMessage,
)
from whatsapp_cloud_api.resources.messages.resource import MessagesResource

BASE = "https://api.kapso.ai/meta/whatsapp/v23.0"
PHONE = "1234567890"
MSG_URL = f"{BASE}/{PHONE}/messages"

SEND_RESPONSE = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": "5511999999999", "wa_id": "5511999999999"}],
    "messages": [{"id": "wamid.test"}],
}


class TestSendText:
    @respx.mock
    async def test_body_structure(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            result = await resource.send_text(
                TextMessage(phone_number_id=PHONE, to="5511999999999", body="Hello")
            )
        assert result.messages[0].id == "wamid.test"
        body = route.calls[0].request.content
        import json
        sent = json.loads(body)
        assert sent["type"] == "text"
        assert sent["text"]["body"] == "Hello"
        assert sent["text"]["preview_url"] is False
        assert sent["messaging_product"] == "whatsapp"
        assert sent["to"] == "5511999999999"

    @respx.mock
    async def test_preview_url_true(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_text(
                TextMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body="https://example.com",
                    preview_url=True,
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["text"]["preview_url"] is True


class TestSendImage:
    @respx.mock
    async def test_image_by_id(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_image(
                ImageMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    image=MediaById(id="media123", caption="pic"),
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["type"] == "image"
        assert sent["image"]["id"] == "media123"
        assert sent["image"]["caption"] == "pic"

    @respx.mock
    async def test_image_by_link(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_image(
                ImageMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    image=MediaByLink(link="https://example.com/img.jpg"),
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["image"]["link"] == "https://example.com/img.jpg"


class TestSendInteractiveButtons:
    @respx.mock
    async def test_button_format(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_buttons(
                InteractiveButtonsMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body_text="Choose",
                    buttons=[
                        InteractiveButton(id="1", title="Yes"),
                        InteractiveButton(id="2", title="No"),
                    ],
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["type"] == "interactive"
        interactive = sent["interactive"]
        assert interactive["type"] == "button"
        assert interactive["body"]["text"] == "Choose"
        buttons = interactive["action"]["buttons"]
        assert len(buttons) == 2
        assert buttons[0] == {"type": "reply", "reply": {"id": "1", "title": "Yes"}}
        assert buttons[1] == {"type": "reply", "reply": {"id": "2", "title": "No"}}


class TestSendInteractiveList:
    @respx.mock
    async def test_list_structure(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_list(
                InteractiveListMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body_text="Pick one",
                    button_text="Menu",
                    sections=[
                        ListSection(
                            title="Section 1",
                            rows=[
                                ListRow(id="r1", title="Row 1", description="Desc 1"),
                            ],
                        )
                    ],
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        interactive = sent["interactive"]
        assert interactive["type"] == "list"
        action = interactive["action"]
        assert action["button"] == "Menu"
        assert len(action["sections"]) == 1
        assert action["sections"][0]["title"] == "Section 1"
        assert action["sections"][0]["rows"][0]["id"] == "r1"


class TestSendInteractiveCatalog:
    @respx.mock
    async def test_without_thumbnail(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_catalog(
                InteractiveCatalogMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body_text="Browse",
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        action = sent["interactive"]["action"]
        assert action["name"] == "catalog_message"
        assert "parameters" not in action

    @respx.mock
    async def test_with_thumbnail(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_catalog(
                InteractiveCatalogMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    parameters=CatalogParameters(thumbnail_product_retailer_id="prod1"),
                )
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        action = sent["interactive"]["action"]
        assert action["parameters"]["thumbnail_product_retailer_id"] == "prod1"


class TestSendInteractiveRaw:
    @respx.mock
    async def test_raw_passthrough(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        raw_interactive = {"type": "custom", "action": {"name": "test"}}
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_raw(
                phone_number_id=PHONE,
                to="5511999999999",
                interactive=raw_interactive,
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["interactive"] == raw_interactive
        assert sent["type"] == "interactive"


class TestMarkRead:
    @respx.mock
    async def test_body_structure(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            result = await resource.mark_read(
                MarkReadInput(phone_number_id=PHONE, message_id="wamid.1")
            )
        import json
        sent = json.loads(route.calls[0].request.content)
        assert sent["messaging_product"] == "whatsapp"
        assert sent["status"] == "read"
        assert sent["message_id"] == "wamid.1"
        assert result == {"success": True}
