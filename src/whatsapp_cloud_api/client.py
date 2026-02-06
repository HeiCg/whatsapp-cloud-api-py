from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

import httpx

from .errors import GraphApiError
from .utils.case import to_snake_deep

if TYPE_CHECKING:
    from .resources.flows import FlowsResource
    from .resources.media import MediaResource
    from .resources.messages.resource import MessagesResource
    from .resources.phone_numbers import PhoneNumbersResource
    from .resources.templates.resource import TemplatesResource

_DEFAULT_BASE_URL = "https://graph.facebook.com"
_DEFAULT_VERSION = "v23.0"


class WhatsAppClient:
    """Async WhatsApp Business Cloud API client backed by httpx."""

    def __init__(
        self,
        *,
        access_token: str,
        base_url: str = _DEFAULT_BASE_URL,
        graph_version: str = _DEFAULT_VERSION,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._access_token = access_token
        self._base_url = base_url.rstrip("/")
        self._version = graph_version

        if http_client is not None:
            self._http = http_client
            self._owns_client = False
        else:
            self._http = httpx.AsyncClient(
                http2=True,
                timeout=httpx.Timeout(timeout),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
            self._owns_client = True

    # ── context manager ──────────────────────────────────────────

    async def __aenter__(self) -> WhatsAppClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    # ── URL helpers ──────────────────────────────────────────────

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self._base_url}/{self._version}/{path.lstrip('/')}"

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── core request ─────────────────────────────────────────────

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raw_response: bool = False,
    ) -> Any:
        merged_headers = {**self._auth_headers, **(headers or {})}

        resp = await self._http.request(
            method,
            self._url(path),
            json=json,
            params=params,
            data=data,
            files=files,
            headers=merged_headers,
        )

        if raw_response:
            return resp

        body: dict[str, Any] = {}
        if resp.content:
            body = resp.json()

        if resp.status_code >= 400:
            raise GraphApiError.from_response(
                resp.status_code,
                body,
                retry_after_header=resp.headers.get("retry-after"),
            )

        return to_snake_deep(body)

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        return await self.request("POST", path, json=json, data=data, files=files)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("DELETE", path, params=params)

    async def fetch_raw(
        self, url: str, *, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        """Fetch a URL without attaching auth headers (e.g., WhatsApp CDN)."""
        return await self._http.get(url, headers=headers or {})

    async def fetch_authenticated(
        self, url: str, *, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        """Fetch a URL WITH auth headers attached."""
        merged = {**self._auth_headers, **(headers or {})}
        return await self._http.get(url, headers=merged)

    # ── lazy resource accessors (cached) ─────────────────────────

    @cached_property
    def messages(self) -> MessagesResource:
        from .resources.messages.resource import MessagesResource as _Cls

        return _Cls(self)

    @cached_property
    def media(self) -> MediaResource:
        from .resources.media import MediaResource as _Cls

        return _Cls(self)

    @cached_property
    def templates(self) -> TemplatesResource:
        from .resources.templates.resource import TemplatesResource as _Cls

        return _Cls(self)

    @cached_property
    def phone_numbers(self) -> PhoneNumbersResource:
        from .resources.phone_numbers import PhoneNumbersResource as _Cls

        return _Cls(self)

    @cached_property
    def flows(self) -> FlowsResource:
        from .resources.flows import FlowsResource as _Cls

        return _Cls(self)
