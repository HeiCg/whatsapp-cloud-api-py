"""Flows resource — create, update, publish, deprecate, preview, deploy."""

from __future__ import annotations

import hashlib
import json as json_mod
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..client import WhatsAppClient


def _canonicalize(value: Any) -> Any:
    """Sort object keys recursively for deterministic hashing."""
    if isinstance(value, dict):
        return {k: _canonicalize(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def _compute_flow_hash(flow_json: dict[str, Any]) -> str:
    """SHA-256 hash of canonicalized flow JSON."""
    canonical = json_mod.dumps(_canonicalize(flow_json), separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── Input models ─────────────────────────────────────────────────────


class CreateFlowInput(BaseModel):
    waba_id: str
    name: str
    categories: list[str] | None = None
    flow_json: dict[str, Any]
    endpoint_uri: str | None = None
    publish: bool = False


class UpdateFlowAssetInput(BaseModel):
    flow_id: str
    json_data: dict[str, Any] | None = None
    file: bytes | None = None


class PublishFlowInput(BaseModel):
    flow_id: str


class DeprecateFlowInput(BaseModel):
    flow_id: str


class PreviewFlowInput(BaseModel):
    flow_id: str
    interactive: bool | None = None
    fields: str | None = None
    params: dict[str, Any] | None = None


class DeployFlowInput(BaseModel):
    flow_json: dict[str, Any]
    name: str
    waba_id: str
    endpoint_uri: str | None = None
    publish: bool = False
    flow_id: str | None = None
    categories: list[str] | None = None
    force_asset_upload: bool = False


# ── Resource ─────────────────────────────────────────────────────────


class FlowsResource:
    __slots__ = ("_client", "_deploy_hashes")

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client
        self._deploy_hashes: dict[str, str] = {}

    async def create(self, input: CreateFlowInput) -> dict[str, Any]:
        import json as json_mod

        data: dict[str, Any] = {
            "name": input.name,
            "categories": json_mod.dumps(input.categories or ["OTHER"]),
        }
        files = {
            "flow_json": (
                "flow.json",
                json_mod.dumps(input.flow_json).encode(),
                "application/json",
            ),
        }
        resp = await self._client.post(f"{input.waba_id}/flows", data=data, files=files)

        if input.publish and resp.get("id"):
            await self.publish(PublishFlowInput(flow_id=resp["id"]))

        return resp

    async def update_asset(self, input: UpdateFlowAssetInput) -> dict[str, Any]:
        import json as json_mod

        if input.json_data:
            file_bytes = json_mod.dumps(input.json_data).encode()
        elif input.file:
            file_bytes = input.file
        else:
            raise ValueError("Either json_data or file must be provided")

        return await self._client.post(
            f"{input.flow_id}/assets",
            data={"name": "flow.json", "asset_type": "FLOW_JSON"},
            files={"file": ("flow.json", file_bytes, "application/json")},
        )

    async def publish(self, input: PublishFlowInput) -> dict[str, Any]:
        return await self._client.post(f"{input.flow_id}/publish", json={})

    async def deprecate(self, input: DeprecateFlowInput) -> dict[str, Any]:
        return await self._client.post(f"{input.flow_id}/deprecate", json={})

    async def preview(self, input: PreviewFlowInput) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if input.interactive is not None:
            params["interactive"] = input.interactive
        if input.fields:
            params["fields"] = input.fields
        return await self._client.get(f"{input.flow_id}/preview", params=params or None)

    async def get(self, flow_id: str, *, fields: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] | None = {"fields": fields} if fields else None
        return await self._client.get(flow_id, params=params)

    async def list(
        self,
        waba_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if after:
            params["after"] = after
        return await self._client.get(f"{waba_id}/flows", params=params or None)

    async def deploy(self, input: DeployFlowInput) -> dict[str, Any]:
        """Idempotent deploy: create-or-update + optional publish.

        Uses SHA-256 hash caching to skip asset uploads when the flow JSON
        hasn't changed since the last deploy (per client instance).
        Pass ``force_asset_upload=True`` to bypass the cache.
        """
        cache_key = f"{input.waba_id}::{input.name}"
        current_hash = _compute_flow_hash(input.flow_json)

        if input.flow_id:
            # Check cache — skip upload if unchanged
            last_hash = self._deploy_hashes.get(cache_key)
            if last_hash == current_hash and not input.force_asset_upload:
                result: dict[str, Any] = {}
            else:
                result = await self.update_asset(
                    UpdateFlowAssetInput(flow_id=input.flow_id, json_data=input.flow_json)
                )
                self._deploy_hashes[cache_key] = current_hash
        else:
            result = await self.create(
                CreateFlowInput(
                    waba_id=input.waba_id,
                    name=input.name,
                    categories=input.categories,
                    flow_json=input.flow_json,
                    endpoint_uri=input.endpoint_uri,
                    publish=False,
                )
            )
            self._deploy_hashes[cache_key] = current_hash

        flow_id = input.flow_id or result.get("id", "")

        if input.publish and flow_id:
            await self.publish(PublishFlowInput(flow_id=flow_id))

        return {**result, "flow_id": flow_id, "published": input.publish}
