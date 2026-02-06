"""Flows resource — create, update, publish, deprecate, preview, deploy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..client import WhatsAppClient


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


# ── Resource ─────────────────────────────────────────────────────────


class FlowsResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

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
        """Idempotent deploy: create-or-update + optional publish."""
        if input.flow_id:
            result = await self.update_asset(
                UpdateFlowAssetInput(flow_id=input.flow_id, json_data=input.flow_json)
            )
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

        flow_id = input.flow_id or result.get("id", "")

        if input.publish and flow_id:
            await self.publish(PublishFlowInput(flow_id=flow_id))

        return {**result, "flow_id": flow_id, "published": input.publish}
