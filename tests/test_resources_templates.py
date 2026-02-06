"""Tests for resources/templates/resource.py — TemplatesResource."""

from __future__ import annotations

import json

import httpx
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.templates.models import (
    TemplateCreateInput,
    TemplateDeleteInput,
    TemplateListInput,
)
from whatsapp_cloud_api.resources.templates.resource import TemplatesResource

BASE = "https://api.kapso.ai/meta/whatsapp/v23.0"
WABA = "waba123"


class TestList:
    @respx.mock
    async def test_list_no_filters(self):
        route = respx.get(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"data": [], "paging": {}})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            result = await resource.list(TemplateListInput(business_account_id=WABA))
        assert result.data == []
        assert route.called

    @respx.mock
    async def test_list_with_filters(self):
        route = respx.get(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"data": [], "paging": {}})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            await resource.list(
                TemplateListInput(
                    business_account_id=WABA,
                    limit=10,
                    status="APPROVED",
                    name="welcome",
                    category="MARKETING",
                    language="en_US",
                )
            )
        req = route.calls[0].request
        assert "limit=10" in str(req.url)
        assert "status=APPROVED" in str(req.url)
        assert "name=welcome" in str(req.url)

    @respx.mock
    async def test_list_none_filters_excluded(self):
        route = respx.get(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"data": [], "paging": {}})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            await resource.list(
                TemplateListInput(business_account_id=WABA, limit=None, name=None)
            )
        req = route.calls[0].request
        assert "limit" not in str(req.url)
        assert "name" not in str(req.url)


class TestCreate:
    @respx.mock
    async def test_create_basic(self):
        route = respx.post(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"id": "tpl1", "status": "PENDING"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            result = await resource.create(
                TemplateCreateInput(
                    business_account_id=WABA,
                    name="test",
                    language="en_US",
                    category="MARKETING",
                    components=[{"type": "BODY", "text": "Hello {{1}}"}],
                )
            )
        assert result.id == "tpl1"
        sent = json.loads(route.calls[0].request.content)
        assert sent["name"] == "test"
        assert sent["language"] == "en_US"
        assert sent["category"] == "MARKETING"

    @respx.mock
    async def test_create_with_optional_fields(self):
        route = respx.post(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"id": "tpl2"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            await resource.create(
                TemplateCreateInput(
                    business_account_id=WABA,
                    name="test",
                    language="en_US",
                    category="MARKETING",
                    components=[],
                    parameter_format="NAMED",
                    allow_category_change=True,
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["parameter_format"] == "NAMED"
        assert sent["allow_category_change"] is True

    @respx.mock
    async def test_create_without_optional_fields(self):
        route = respx.post(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"id": "tpl3"})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            await resource.create(
                TemplateCreateInput(
                    business_account_id=WABA,
                    name="test",
                    language="en_US",
                    category="MARKETING",
                    components=[],
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert "parameter_format" not in sent
        assert "allow_category_change" not in sent


class TestDelete:
    @respx.mock
    async def test_delete_by_name_only(self):
        route = respx.delete(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            result = await resource.delete(
                TemplateDeleteInput(business_account_id=WABA, name="old_template")
            )
        assert result.success is True
        req = route.calls[0].request
        assert "name=old_template" in str(req.url)
        assert "hsm_id" not in str(req.url)

    @respx.mock
    async def test_delete_with_language(self):
        route = respx.delete(f"{BASE}/{WABA}/message_templates").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = TemplatesResource(client)
            await resource.delete(
                TemplateDeleteInput(
                    business_account_id=WABA,
                    name="old_template",
                    language="en_US",
                )
            )
        req = route.calls[0].request
        assert "hsm_id=en_US" in str(req.url)
