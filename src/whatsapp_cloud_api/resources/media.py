"""Media resource — upload, get metadata, download, delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel

from ..types import MediaMetadata, MediaUploadResponse

if TYPE_CHECKING:
    from ..client import WhatsAppClient


class MediaUploadInput(BaseModel):
    phone_number_id: str
    type: Literal["image", "video", "audio", "document", "sticker"]
    file: bytes
    filename: str = "file"
    mime_type: str = "application/octet-stream"
    messaging_product: str = "whatsapp"


class MediaResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

    async def upload(self, input: MediaUploadInput) -> MediaUploadResponse:
        resp = await self._client.post(
            f"{input.phone_number_id}/media",
            data={"messaging_product": input.messaging_product, "type": input.mime_type},
            files={"file": (input.filename, input.file, input.mime_type)},
        )
        return MediaUploadResponse.model_validate(resp)

    async def get(self, media_id: str) -> MediaMetadata:
        resp = await self._client.get(media_id)
        return MediaMetadata.model_validate(resp)

    async def delete(self, media_id: str) -> dict[str, Any]:
        return await self._client.delete(media_id)

    async def download(
        self,
        media_id: str,
        *,
        auth: Literal["auto", "never", "always"] = "auto",
        use_auth: bool | None = None,
    ) -> bytes:
        """Download media by first fetching the URL, then downloading the bytes.

        Args:
            media_id: The media ID to download.
            auth: Authentication mode for the CDN fetch.
                - "auto" (default): Try without auth first, retry with auth on 401/403.
                - "never": Never send auth headers (public CDN downloads).
                - "always": Always send auth headers.
            use_auth: Deprecated. Use ``auth="always"`` instead. Kept for
                backwards compatibility.
        """
        # Backwards compat: use_auth=True maps to auth="always"
        if use_auth is not None:
            auth = "always" if use_auth else "auto"

        meta = await self.get(media_id)

        if auth == "never":
            resp = await self._client.fetch_raw(meta.url)
            resp.raise_for_status()
            return resp.content

        if auth == "always":
            resp = await self._client.fetch_authenticated(meta.url)
            resp.raise_for_status()
            return resp.content

        # auth == "auto": try raw, retry with auth on 401/403
        resp = await self._client.fetch_raw(meta.url)
        if resp.status_code in (401, 403):
            resp = await self._client.fetch_authenticated(meta.url)
        resp.raise_for_status()
        return resp.content
