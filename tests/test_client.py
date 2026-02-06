"""Tests for client.py — WhatsAppClient async behavior."""

from __future__ import annotations

import httpx
import pytest
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.errors import GraphApiError

BASE = "https://graph.facebook.com/v23.0"


class TestUrl:
    def test_relative_path(self):
        client = WhatsAppClient(access_token="tok")
        assert client._url("123/messages") == f"{BASE}/123/messages"

    def test_relative_path_with_leading_slash(self):
        client = WhatsAppClient(access_token="tok")
        assert client._url("/123/messages") == f"{BASE}/123/messages"

    def test_absolute_url_passthrough(self):
        client = WhatsAppClient(access_token="tok")
        url = "https://cdn.example.com/media/123"
        assert client._url(url) == url

    def test_custom_base_url(self):
        client = WhatsAppClient(access_token="tok", base_url="https://custom.api.com/")
        assert client._url("path") == "https://custom.api.com/v23.0/path"

    def test_custom_version(self):
        client = WhatsAppClient(access_token="tok", graph_version="v22.0")
        assert client._url("path") == "https://graph.facebook.com/v22.0/path"


class TestRequest:
    @respx.mock
    async def test_success_returns_snake_case(self):
        route = respx.get(f"{BASE}/test").mock(
            return_value=httpx.Response(200, json={"messagingProduct": "whatsapp"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            result = await client.get("test")
        assert result == {"messaging_product": "whatsapp"}
        assert route.called

    @respx.mock
    async def test_error_raises_graph_api_error(self):
        respx.get(f"{BASE}/test").mock(
            return_value=httpx.Response(
                400,
                json={"error": {"message": "Bad param", "code": 100, "type": "ParamError"}},
            )
        )
        async with WhatsAppClient(access_token="tok") as client:
            with pytest.raises(GraphApiError) as exc_info:
                await client.get("test")
        assert exc_info.value.code == 100
        assert exc_info.value.http_status == 400
        assert str(exc_info.value) == "Bad param"

    @respx.mock
    async def test_raw_response_returns_httpx_response(self):
        respx.get(f"{BASE}/test").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            result = await client.request("GET", "test", raw_response=True)
        assert isinstance(result, httpx.Response)
        assert result.status_code == 200

    @respx.mock
    async def test_auth_headers_present(self):
        route = respx.get(f"{BASE}/test").mock(
            return_value=httpx.Response(200, json={})
        )
        async with WhatsAppClient(access_token="my-token") as client:
            await client.get("test")
        assert route.calls[0].request.headers["authorization"] == "Bearer my-token"

    @respx.mock
    async def test_post_with_json(self):
        route = respx.post(f"{BASE}/123/messages").mock(
            return_value=httpx.Response(200, json={"messaging_product": "whatsapp"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            await client.post("123/messages", json={"to": "456", "type": "text"})
        assert route.called

    @respx.mock
    async def test_delete(self):
        route = respx.delete(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            result = await client.delete("media123")
        assert result == {"success": True}
        assert route.called

    @respx.mock
    async def test_retry_after_header_parsed(self):
        respx.get(f"{BASE}/test").mock(
            return_value=httpx.Response(
                429,
                json={"error": {"message": "Throttled", "code": 4}},
                headers={"retry-after": "30"},
            )
        )
        async with WhatsAppClient(access_token="tok") as client:
            with pytest.raises(GraphApiError) as exc_info:
                await client.get("test")
        assert exc_info.value.retry.retry_after_ms == 30_000

    @respx.mock
    async def test_empty_response_body(self):
        respx.delete(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, content=b"")
        )
        async with WhatsAppClient(access_token="tok") as client:
            result = await client.delete("media123")
        assert result == {}


class TestAclose:
    async def test_aclose_owned_client(self):
        client = WhatsAppClient(access_token="tok")
        assert client._owns_client is True
        await client.aclose()
        # httpx client should be closed
        assert client._http.is_closed

    async def test_aclose_external_client(self):
        http = httpx.AsyncClient()
        client = WhatsAppClient(access_token="tok", http_client=http)
        assert client._owns_client is False
        await client.aclose()
        # External client should NOT be closed
        assert not http.is_closed
        await http.aclose()

    async def test_context_manager(self):
        async with WhatsAppClient(access_token="tok") as client:
            assert client._owns_client is True
        assert client._http.is_closed


class TestFetchMethods:
    @respx.mock
    async def test_fetch_raw_no_auth(self):
        url = "https://cdn.example.com/media/file.jpg"
        route = respx.get(url).mock(return_value=httpx.Response(200, content=b"bytes"))
        async with WhatsAppClient(access_token="secret-tok") as client:
            resp = await client.fetch_raw(url)
        assert resp.content == b"bytes"
        assert "authorization" not in route.calls[0].request.headers

    @respx.mock
    async def test_fetch_authenticated_has_auth(self):
        url = "https://cdn.example.com/media/file.jpg"
        route = respx.get(url).mock(return_value=httpx.Response(200, content=b"bytes"))
        async with WhatsAppClient(access_token="secret-tok") as client:
            resp = await client.fetch_authenticated(url)
        assert resp.content == b"bytes"
        assert route.calls[0].request.headers["authorization"] == "Bearer secret-tok"


class TestCachedProperties:
    def test_messages_returns_same_instance(self):
        client = WhatsAppClient(access_token="tok")
        m1 = client.messages
        m2 = client.messages
        assert m1 is m2

    def test_media_returns_same_instance(self):
        client = WhatsAppClient(access_token="tok")
        assert client.media is client.media

    def test_templates_returns_same_instance(self):
        client = WhatsAppClient(access_token="tok")
        assert client.templates is client.templates

    def test_phone_numbers_returns_same_instance(self):
        client = WhatsAppClient(access_token="tok")
        assert client.phone_numbers is client.phone_numbers

    def test_flows_returns_same_instance(self):
        client = WhatsAppClient(access_token="tok")
        assert client.flows is client.flows
