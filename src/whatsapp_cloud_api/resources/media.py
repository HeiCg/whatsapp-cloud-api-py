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
        use_auth: bool = False,
    ) -> bytes:
        """Download media by first fetching the URL, then downloading the bytes.

        Args:
            media_id: The media ID to download.
            use_auth: If True, sends auth headers to the CDN. Usually not needed
                      for WhatsApp's public CDN URLs.
        """
        meta = await self.get(media_id)
        if use_auth:
            resp = await self._client.fetch_authenticated(meta.url)
        else:
            resp = await self._client.fetch_raw(meta.url)

        if resp.status_code == 401 or resp.status_code == 403:
            # Retry with auth
            resp = await self._client.fetch_authenticated(meta.url)

        resp.raise_for_status()
        return resp.content
