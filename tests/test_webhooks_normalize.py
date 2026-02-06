"""Tests for webhooks/normalize.py — webhook payload normalization."""

from __future__ import annotations

from tests.conftest import build_webhook_payload
from whatsapp_cloud_api.webhooks.normalize import normalize_webhook


class TestNormalizeWebhookEdgeCases:
    def test_non_dict_returns_empty(self):
        wh = normalize_webhook("not a dict")
        assert wh.messages == []
        assert wh.statuses == []
        assert wh.contacts == []
        assert wh.object is None

    def test_none_returns_empty(self):
        wh = normalize_webhook(None)
        assert wh.messages == []

    def test_list_returns_empty(self):
        wh = normalize_webhook([1, 2, 3])
        assert wh.messages == []

    def test_empty_dict(self):
        wh = normalize_webhook({})
        assert wh.messages == []
        assert wh.object is None


class TestNormalizeMessages:
    def test_single_text_message(self):
        payload = build_webhook_payload(
            messages=[
                {
                    "from": "5511999999999",
                    "id": "wamid.1",
                    "timestamp": "1234567890",
                    "type": "text",
                    "text": {"body": "Hello"},
                }
            ],
            contacts=[{"profile": {"name": "John"}, "wa_id": "5511999999999"}],
        )
        wh = normalize_webhook(payload)
        assert wh.object == "whatsapp_business_account"
        assert wh.phone_number_id == "1234567890"
        assert wh.display_phone_number == "+5511999999999"
        assert len(wh.messages) == 1
        msg = wh.messages[0]
        assert msg.id == "wamid.1"
        assert msg.type == "text"
        assert msg.from_ == "5511999999999"
        assert msg.text == {"body": "Hello"}

    def test_from_remapped_to_from_(self):
        payload = build_webhook_payload(
            messages=[
                {
                    "from": "5511999999999",
                    "id": "wamid.1",
                    "timestamp": "1234567890",
                    "type": "text",
                }
            ]
        )
        wh = normalize_webhook(payload)
        msg = wh.messages[0]
        assert msg.from_ == "5511999999999"

    def test_multiple_messages(self):
        payload = build_webhook_payload(
            messages=[
                {"from": "1", "id": "m1", "timestamp": "1", "type": "text"},
                {"from": "2", "id": "m2", "timestamp": "2", "type": "image"},
            ]
        )
        wh = normalize_webhook(payload)
        assert len(wh.messages) == 2
        assert wh.messages[0].id == "m1"
        assert wh.messages[1].id == "m2"


class TestNormalizeStatuses:
    def test_single_status(self):
        payload = build_webhook_payload(
            statuses=[
                {
                    "id": "wamid.1",
                    "status": "delivered",
                    "timestamp": "1234567890",
                    "recipient_id": "5511999999999",
                }
            ]
        )
        wh = normalize_webhook(payload)
        assert len(wh.statuses) == 1
        assert wh.statuses[0].status == "delivered"
        assert wh.statuses[0].recipient_id == "5511999999999"


class TestNormalizeContacts:
    def test_contacts_extracted(self):
        payload = build_webhook_payload(
            messages=[
                {"from": "1", "id": "m1", "timestamp": "1", "type": "text"},
            ],
            contacts=[
                {"profile": {"name": "John"}, "wa_id": "5511999999999"},
            ],
        )
        wh = normalize_webhook(payload)
        assert len(wh.contacts) == 1
        assert wh.contacts[0]["wa_id"] == "5511999999999"


class TestNormalizeRawFields:
    def test_non_messages_field_goes_to_raw(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "entry1",
                    "changes": [
                        {
                            "value": {"some_data": "test"},
                            "field": "account_alerts",
                        }
                    ],
                }
            ],
        }
        wh = normalize_webhook(payload)
        assert wh.messages == []
        assert "account_alerts" in wh.raw
        assert len(wh.raw["account_alerts"]) == 1

    def test_mixed_fields(self):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "entry1",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "phone_number_id": "123",
                                    "display_phone_number": "+1",
                                },
                                "messages": [
                                    {
                                        "from": "1",
                                        "id": "m1",
                                        "timestamp": "1",
                                        "type": "text",
                                    }
                                ],
                            },
                            "field": "messages",
                        },
                        {
                            "value": {"alert_type": "policy"},
                            "field": "account_alerts",
                        },
                    ],
                }
            ],
        }
        wh = normalize_webhook(payload)
        assert len(wh.messages) == 1
        assert "account_alerts" in wh.raw
