"""Tests for resources/phone_numbers.py — PhoneNumbersResource."""

from __future__ import annotations

import json

import httpx
import respx

from whatsapp_cloud_api.client import WhatsAppClient
from whatsapp_cloud_api.resources.phone_numbers import (
    DeregisterInput,
    PhoneNumbersResource,
    RegisterInput,
    RequestCodeInput,
    UpdateBusinessProfileInput,
    VerifyCodeInput,
)

BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
PHONE = "1234567890"


class TestRequestCode:
    @respx.mock
    async def test_request_code(self):
        route = respx.post(f"{BASE}/{PHONE}/request_code").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            result = await resource.request_code(
                RequestCodeInput(phone_number_id=PHONE, code_method="SMS", language="en")
            )
        assert result == {"success": True}
        sent = json.loads(route.calls[0].request.content)
        assert sent["code_method"] == "SMS"
        assert sent["language"] == "en"


class TestVerifyCode:
    @respx.mock
    async def test_verify_code(self):
        route = respx.post(f"{BASE}/{PHONE}/verify_code").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            await resource.verify_code(
                VerifyCodeInput(phone_number_id=PHONE, code="123456")
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["code"] == "123456"


class TestRegister:
    @respx.mock
    async def test_register_basic(self):
        route = respx.post(f"{BASE}/{PHONE}/register").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            await resource.register(RegisterInput(phone_number_id=PHONE, pin="123456"))
        sent = json.loads(route.calls[0].request.content)
        assert sent["messaging_product"] == "whatsapp"
        assert sent["pin"] == "123456"
        assert "data_localization_region" not in sent

    @respx.mock
    async def test_register_with_data_localization(self):
        route = respx.post(f"{BASE}/{PHONE}/register").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            await resource.register(
                RegisterInput(
                    phone_number_id=PHONE, pin="123456", data_localization_region="BR"
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["data_localization_region"] == "BR"


class TestDeregister:
    @respx.mock
    async def test_deregister(self):
        route = respx.post(f"{BASE}/{PHONE}/deregister").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            await resource.deregister(DeregisterInput(phone_number_id=PHONE))
        sent = json.loads(route.calls[0].request.content)
        assert sent == {}
        assert route.called


class TestBusinessProfileSubResource:
    @respx.mock
    async def test_get(self):
        route = respx.get(f"{BASE}/{PHONE}/whatsapp_business_profile").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"about": "Test business", "description": "Desc"}]},
            )
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            result = await resource.business_profile.get(PHONE)
        assert len(result.data) == 1
        assert result.data[0].about == "Test business"
        assert route.called

    @respx.mock
    async def test_update(self):
        route = respx.post(f"{BASE}/{PHONE}/whatsapp_business_profile").mock(
            return_value=httpx.Response(200, json={"success": True})
        )
        async with WhatsAppClient(access_token="tok") as client:
            resource = PhoneNumbersResource(client)
            await resource.business_profile.update(
                UpdateBusinessProfileInput(
                    phone_number_id=PHONE,
                    about="New about",
                    description="New desc",
                )
            )
        sent = json.loads(route.calls[0].request.content)
        assert sent["about"] == "New about"
        assert sent["description"] == "New desc"
        assert sent["messaging_product"] == "whatsapp"
        assert "phone_number_id" not in sent
