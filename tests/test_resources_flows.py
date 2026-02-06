"""Tests for resources/flows.py — FlowsResource."""

from __future__ import annotations

import httpx
import pytest
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.flows import (
    CreateFlowInput,
    DeployFlowInput,
    FlowsResource,
    UpdateFlowAssetInput,
)

BASE = "https://graph.facebook.com/v23.0"
WABA = "waba123"


class TestCreate:
    @respx.mock
    async def test_create_without_publish(self):
        route = respx.post(f"{BASE}/{WABA}/flows").mock(
            return_value=httpx.Response(200, json={"id": "flow1"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            result = await resource.create(
                CreateFlowInput(
                    waba_id=WABA,
                    name="My Flow",
                    flow_json={"screens": []},
                )
            )
        assert result == {"id": "flow1"}
        assert route.called

    @respx.mock
    async def test_create_with_publish(self):
        respx.post(f"{BASE}/{WABA}/flows").mock(
            return_value=httpx.Response(200, json={"id": "flow1"})
        )
        publish_route = respx.post(f"{BASE}/flow1/publish").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            await resource.create(
                CreateFlowInput(
                    waba_id=WABA,
                    name="My Flow",
                    flow_json={"screens": []},
                    publish=True,
                )
            )
        assert publish_route.called


class TestUpdateAsset:
    @respx.mock
    async def test_with_json_data(self):
        route = respx.post(f"{BASE}/flow1/assets").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            result = await resource.update_asset(
                UpdateFlowAssetInput(flow_id="flow1", json_data={"screens": []})
            )
        assert result == {"success": True}
        assert route.called

    @respx.mock
    async def test_with_file_bytes(self):
        route = respx.post(f"{BASE}/flow1/assets").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            await resource.update_asset(
                UpdateFlowAssetInput(flow_id="flow1", file=b'{"screens": []}')
            )
        assert route.called

    async def test_neither_raises_value_error(self):
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            with pytest.raises(ValueError, match="Either json_data or file must be provided"):
                await resource.update_asset(
                    UpdateFlowAssetInput(flow_id="flow1")
                )


class TestDeploy:
    @respx.mock
    async def test_deploy_new_flow(self):
        create_route = respx.post(f"{BASE}/{WABA}/flows").mock(
            return_value=httpx.Response(200, json={"id": "new_flow"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            result = await resource.deploy(
                DeployFlowInput(
                    waba_id=WABA,
                    name="Deploy Flow",
                    flow_json={"screens": []},
                )
            )
        assert create_route.called
        assert result["flow_id"] == "new_flow"
        assert result["published"] is False

    @respx.mock
    async def test_deploy_existing_flow(self):
        update_route = respx.post(f"{BASE}/existing_flow/assets").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            result = await resource.deploy(
                DeployFlowInput(
                    waba_id=WABA,
                    name="Deploy Flow",
                    flow_json={"screens": []},
                    flow_id="existing_flow",
                )
            )
        assert update_route.called
        assert result["flow_id"] == "existing_flow"

    @respx.mock
    async def test_deploy_with_publish(self):
        respx.post(f"{BASE}/{WABA}/flows").mock(
            return_value=httpx.Response(200, json={"id": "flow_pub"})
        )
        publish_route = respx.post(f"{BASE}/flow_pub/publish").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = FlowsResource(client)
            result = await resource.deploy(
                DeployFlowInput(
                    waba_id=WABA,
                    name="Deploy Flow",
                    flow_json={"screens": []},
                    publish=True,
                )
            )
        assert publish_route.called
        assert result["published"] is True
