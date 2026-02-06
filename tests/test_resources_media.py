"""Tests for resources/media.py — MediaResource."""

from __future__ import annotations

import httpx
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.media import MediaResource, MediaUploadInput

BASE = "https://api.kapso.ai/meta/whatsapp/v23.0"


class TestUpload:
    @respx.mock
    async def test_upload_multipart(self):
        route = respx.post(f"{BASE}/123/media").mock(
            return_value=httpx.Response(200, json={"id": "media_id_1"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            result = await resource.upload(
                MediaUploadInput(
                    phone_number_id="123",
                    type="image",
                    file=b"fakeimagebytes",
                    filename="photo.jpg",
                    mime_type="image/jpeg",
                )
            )
        assert result.id == "media_id_1"
        assert route.called
        # Verify content type is multipart
        req = route.calls[0].request
        assert b"multipart/form-data" in req.headers.get("content-type", "").encode() or \
            "multipart" in req.headers.get("content-type", "")


class TestGet:
    @respx.mock
    async def test_get_metadata(self):
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "messaging_product": "whatsapp",
                    "url": "https://cdn.example.com/file",
                    "mime_type": "image/jpeg",
                    "sha256": "abc",
                    "file_size": "1024",
                    "id": "media123",
                },
            )
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            meta = await resource.get("media123")
        assert meta.id == "media123"
        assert meta.url == "https://cdn.example.com/file"
        assert meta.mime_type == "image/jpeg"


class TestDelete:
    @respx.mock
    async def test_delete(self):
        route = respx.delete(f"{BASE}/media123").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            result = await resource.delete("media123")
        assert result == {"success": True}
        assert route.called


class TestDownload:
    @respx.mock
    async def test_download_without_auth(self):
        cdn_url = "https://cdn.example.com/media/file.jpg"
        # First call: get metadata
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "messaging_product": "whatsapp",
                    "url": cdn_url,
                    "mime_type": "image/jpeg",
                    "sha256": "abc",
                    "file_size": "100",
                    "id": "media123",
                },
            )
        )
        # Second call: download from CDN (no auth)
        respx.get(cdn_url).mock(
            return_value=httpx.Response(200, content=b"image-bytes")
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123")
        assert data == b"image-bytes"

    @respx.mock
    async def test_download_retry_on_401(self):
        cdn_url = "https://cdn.example.com/media/file.jpg"
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "messaging_product": "whatsapp",
                    "url": cdn_url,
                    "mime_type": "image/jpeg",
                    "sha256": "abc",
                    "file_size": "100",
                    "id": "media123",
                },
            )
        )
        # First CDN request returns 401, second (with auth) succeeds
        cdn_route = respx.get(cdn_url).mock(
            side_effect=[
                httpx.Response(401, content=b""),
                httpx.Response(200, content=b"image-bytes-auth"),
            ]
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123")
        assert data == b"image-bytes-auth"
        # Two CDN calls: raw fetch + auth retry
        assert cdn_route.call_count == 2

    @respx.mock
    async def test_download_with_use_auth(self):
        cdn_url = "https://cdn.example.com/media/file.jpg"
        respx.get(f"{BASE}/media123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "messaging_product": "whatsapp",
                    "url": cdn_url,
                    "mime_type": "image/jpeg",
                    "sha256": "abc",
                    "file_size": "100",
                    "id": "media123",
                },
            )
        )
        cdn_route = respx.get(cdn_url).mock(
            return_value=httpx.Response(200, content=b"auth-bytes")
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = MediaResource(client)
            data = await resource.download("media123", use_auth=True)
        assert data == b"auth-bytes"
        # With use_auth=True, the first call already has auth headers
        req = cdn_route.calls[0].request
        assert "Bearer tok" in req.headers.get("authorization", "")
