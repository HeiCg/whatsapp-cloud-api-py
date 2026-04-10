"""Tests for compatibility gap fixes: sendRaw, address, call_permission, media auth, flow caching."""

from __future__ import annotations

import json

import httpx
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.flows import FlowsResource, _compute_flow_hash
from whatsapp_cloud_api.resources.media import MediaResource
from whatsapp_cloud_api.resources.messages.models import (
    AddressParameters,
    CallPermissionParameters,
    InteractiveAddressMessage,
    InteractiveCallPermissionMessage,
    RawMessage,
)
from whatsapp_cloud_api.resources.messages.resource import MessagesResource

BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
PHONE = "1234567890"
MSG_URL = f"{BASE}/{PHONE}/messages"

SEND_RESPONSE = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": "5511999999999", "wa_id": "5511999999999"}],
    "messages": [{"id": "wamid.test"}],
}


# ── send_raw ─────────────────────────────────────────────────────────


class TestSendRaw:
    @respx.mock
    async def test_raw_payload_passthrough(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            result = await resource.send_raw(
                RawMessage(
                    phone_number_id=PHONE,
                    payload={
                        "to": "5511999999999",
                        "type": "text",
                        "text": {"body": "raw hello"},
                    },
                )
            )
        assert result.messages[0].id == "wamid.test"
        sent = json.loads(route.calls[0].request.content)
        assert sent["messaging_product"] == "whatsapp"
        assert sent["type"] == "text"
        assert sent["text"]["body"] == "raw hello"


# ── send_interactive_address ─────────────────────────────────────────


class TestSendInteractiveAddress:
    @respx.mock
    async def test_address_structure(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_address(
                InteractiveAddressMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body_text="Enter your address",
                    parameters=AddressParameters(country="BR"),
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["type"] == "interactive"
        interactive = sent["interactive"]
        assert interactive["type"] == "address_message"
        assert interactive["body"]["text"] == "Enter your address"
        assert interactive["action"]["parameters"]["country"] == "BR"


# ── send_interactive_call_permission ─────────────────────────────────


class TestSendInteractiveCallPermission:
    @respx.mock
    async def test_call_permission_structure(self):
        route = respx.post(MSG_URL).mock(
            return_value=httpx.Response(200, json=SEND_RESPONSE)
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MessagesResource(client)
            await resource.send_interactive_call_permission(
                InteractiveCallPermissionMessage(
                    phone_number_id=PHONE,
                    to="5511999999999",
                    body_text="Can we call you?",
                    parameters=CallPermissionParameters(
                        phone_number="+5511999999999",
                        call_purpose="support",
                    ),
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["type"] == "interactive"
        interactive = sent["interactive"]
        assert interactive["type"] == "call_permission"
        assert interactive["action"]["parameters"]["phone_number"] == "+5511999999999"
        assert interactive["action"]["parameters"]["call_purpose"] == "support"


# ── media download auth modes ────────────────────────────────────────


CDN_URL = "https://cdn.example.com/media/file.jpg"
MEDIA_META = {
    "messaging_product": "whatsapp",
    "url": CDN_URL,
    "mime_type": "image/jpeg",
    "sha256": "abc",
    "file_size": "100",
    "id": "media123",
}


class TestMediaDownloadAuth:
    @respx.mock
    async def test_auth_never(self):
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json=MEDIA_META)
        )
        cdn_route = respx.get(CDN_URL).mock(
            return_value=httpx.Response(200, content=b"public-bytes")
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123", auth="never")
        assert data == b"public-bytes"
        req = cdn_route.calls[0].request
        assert "x-api-key" not in req.headers

    @respx.mock
    async def test_auth_always(self):
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json=MEDIA_META)
        )
        cdn_route = respx.get(CDN_URL).mock(
            return_value=httpx.Response(200, content=b"auth-bytes")
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123", auth="always")
        assert data == b"auth-bytes"
        req = cdn_route.calls[0].request
        assert req.headers.get("x-api-key") == "tok"

    @respx.mock
    async def test_auth_auto_fallback(self):
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json=MEDIA_META)
        )
        cdn_route = respx.get(CDN_URL).mock(
            side_effect=[
                httpx.Response(403, content=b""),
                httpx.Response(200, content=b"retried-bytes"),
            ]
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123", auth="auto")
        assert data == b"retried-bytes"
        assert cdn_route.call_count == 2

    @respx.mock
    async def test_use_auth_backwards_compat(self):
        """use_auth=True should still work (maps to auth='always')."""
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json=MEDIA_META)
        )
        cdn_route = respx.get(CDN_URL).mock(
            return_value=httpx.Response(200, content=b"compat-bytes")
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123", use_auth=True)
        assert data == b"compat-bytes"
        req = cdn_route.calls[0].request
        assert req.headers.get("x-api-key") == "tok"


# ── flow deploy hash caching ────────────────────────────────────────


class TestFlowDeployHashCaching:
    def test_compute_flow_hash_deterministic(self):
        """Same JSON with different key order produces same hash."""
        a = {"z": 1, "a": 2, "nested": {"b": 3, "a": 4}}
        b = {"a": 2, "nested": {"a": 4, "b": 3}, "z": 1}
        assert _compute_flow_hash(a) == _compute_flow_hash(b)

    def test_compute_flow_hash_different(self):
        a = {"key": "value1"}
        b = {"key": "value2"}
        assert _compute_flow_hash(a) != _compute_flow_hash(b)

    @respx.mock
    async def test_deploy_caches_hash(self):
        """Second deploy with same JSON should skip update_asset call."""
        from whatsapp_cloud_api.resources.flows import DeployFlowInput

        waba = "waba123"
        flow_json = {"screens": [{"id": "s1"}]}

        # First deploy: update_asset is called
        asset_route = respx.post(f"{BASE}/flow1/assets").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            await resource.deploy(
                DeployFlowInput(
                    flow_json=flow_json,
                    name="test-flow",
                    waba_id=waba,
                    flow_id="flow1",
                )
            )
            assert asset_route.call_count == 1

            # Second deploy with same JSON: should skip
            await resource.deploy(
                DeployFlowInput(
                    flow_json=flow_json,
                    name="test-flow",
                    waba_id=waba,
                    flow_id="flow1",
                )
            )
            # Still 1 — the second call was skipped
            assert asset_route.call_count == 1

    @respx.mock
    async def test_deploy_force_upload(self):
        """force_asset_upload=True should bypass cache."""
        from whatsapp_cloud_api.resources.flows import DeployFlowInput

        flow_json = {"screens": [{"id": "s1"}]}
        asset_route = respx.post(f"{BASE}/flow1/assets").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            await resource.deploy(
                DeployFlowInput(
                    flow_json=flow_json,
                    name="test-flow",
                    waba_id="waba123",
                    flow_id="flow1",
                )
            )
            await resource.deploy(
                DeployFlowInput(
                    flow_json=flow_json,
                    name="test-flow",
                    waba_id="waba123",
                    flow_id="flow1",
                    force_asset_upload=True,
                )
            )
            # Both calls went through
            assert asset_route.call_count == 2
