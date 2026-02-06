"""Shared fixtures for the whatsapp-cloud-api test suite."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from whatsapp_cloud_api.client import WhatsAppClient


@pytest.fixture()
def mock_api():
    """Yield a started respx mock router."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture()
def mock_client(mock_api):
    """WhatsAppClient backed by a respx-mocked httpx transport."""
    transport = httpx.MockTransport(mock_api.handler)
    http = httpx.AsyncClient(transport=transport)
    return WhatsAppClient(access_token="test-token", http_client=http)


@pytest.fixture()
def send_message_response() -> dict[str, Any]:
    """Standard API response for a sent message."""
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "5511999999999", "wa_id": "5511999999999"}],
        "messages": [{"id": "wamid.test123"}],
    }


def build_webhook_payload(
    *,
    messages: list[dict[str, Any]] | None = None,
    statuses: list[dict[str, Any]] | None = None,
    contacts: list[dict[str, Any]] | None = None,
    field: str = "messages",
    phone_number_id: str = "1234567890",
    display_phone_number: str = "+5511999999999",
) -> dict[str, Any]:
    """Build a realistic Meta webhook payload."""
    value: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "metadata": {
            "phone_number_id": phone_number_id,
            "display_phone_number": display_phone_number,
        },
    }
    if messages is not None:
        value["messages"] = messages
    if statuses is not None:
        value["statuses"] = statuses
    if contacts is not None:
        value["contacts"] = contacts

    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry1",
                "changes": [{"value": value, "field": field}],
            }
        ],
    }
