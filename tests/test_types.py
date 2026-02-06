"""Tests for types.py — Pydantic response models and CamelModel."""

from whatsapp_cloud_api.types import (
    CamelModel,
    MediaMetadata,
    MessageStatusUpdate,
    NormalizedWebhook,
    SendMessageResponse,
    WebhookMessage,
)


class TestCamelModel:
    def test_alias_generation_snake_to_camel(self):
        class Sample(CamelModel):
            first_name: str
            last_name: str

        obj = Sample(first_name="John", last_name="Doe")
        dumped = obj.model_dump(by_alias=True)
        assert "firstName" in dumped
        assert "lastName" in dumped

    def test_populate_by_name(self):
        class Sample(CamelModel):
            first_name: str

        # Can create using snake_case field name
        obj = Sample(first_name="John")
        assert obj.first_name == "John"

    def test_populate_by_alias(self):
        class Sample(CamelModel):
            first_name: str

        # Can also create using camelCase alias
        obj = Sample.model_validate({"firstName": "John"})
        assert obj.first_name == "John"


class TestSendMessageResponse:
    def test_basic_validation(self):
        data = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "5511999999999", "wa_id": "5511999999999"}],
            "messages": [{"id": "wamid.test123"}],
        }
        resp = SendMessageResponse.model_validate(data)
        assert resp.messaging_product == "whatsapp"
        assert len(resp.contacts) == 1
        assert resp.contacts[0].wa_id == "5511999999999"
        assert resp.messages[0].id == "wamid.test123"

    def test_defaults(self):
        resp = SendMessageResponse()
        assert resp.messaging_product == "whatsapp"
        assert resp.contacts == []
        assert resp.messages == []

    def test_camel_case_input(self):
        data = {
            "messagingProduct": "whatsapp",
            "contacts": [{"input": "num", "waId": "num"}],
            "messages": [{"id": "wamid.1", "messageStatus": "accepted"}],
        }
        resp = SendMessageResponse.model_validate(data)
        assert resp.contacts[0].wa_id == "num"
        assert resp.messages[0].message_status == "accepted"


class TestMediaMetadata:
    def test_validation(self):
        data = {
            "url": "https://cdn.example.com/media/123",
            "mime_type": "image/jpeg",
            "sha256": "abc123",
            "file_size": "12345",
            "id": "media_id_123",
        }
        meta = MediaMetadata.model_validate(data)
        assert meta.url == "https://cdn.example.com/media/123"
        assert meta.mime_type == "image/jpeg"
        assert meta.id == "media_id_123"


class TestWebhookMessage:
    def test_basic_fields(self):
        data = {
            "id": "wamid.1",
            "type": "text",
            "timestamp": "1234567890",
            "from_": "5511999999999",
            "text": {"body": "Hello"},
        }
        msg = WebhookMessage.model_validate(data)
        assert msg.id == "wamid.1"
        assert msg.type == "text"
        assert msg.from_ == "5511999999999"

    def test_extra_fields_allowed(self):
        data = {
            "id": "wamid.1",
            "type": "text",
            "timestamp": "1234567890",
            "unknown_field": "should_not_fail",
        }
        msg = WebhookMessage.model_validate(data)
        assert msg.id == "wamid.1"

    def test_optional_fields_none_by_default(self):
        data = {"id": "wamid.1", "type": "text", "timestamp": "1234567890"}
        msg = WebhookMessage.model_validate(data)
        assert msg.from_ is None
        assert msg.text is None
        assert msg.image is None
        assert msg.context is None


class TestMessageStatusUpdate:
    def test_basic(self):
        data = {
            "id": "wamid.1",
            "status": "delivered",
            "timestamp": "1234567890",
            "recipient_id": "5511999999999",
        }
        status = MessageStatusUpdate.model_validate(data)
        assert status.status == "delivered"
        assert status.recipient_id == "5511999999999"

    def test_extra_allowed(self):
        data = {
            "id": "wamid.1",
            "status": "sent",
            "timestamp": "1234567890",
            "custom_field": "ok",
        }
        status = MessageStatusUpdate.model_validate(data)
        assert status.id == "wamid.1"


class TestNormalizedWebhook:
    def test_defaults(self):
        wh = NormalizedWebhook()
        assert wh.object is None
        assert wh.messages == []
        assert wh.statuses == []
        assert wh.contacts == []
        assert wh.raw == {}

    def test_extra_allowed(self):
        wh = NormalizedWebhook.model_validate({"extra_field": "ok"})
        assert wh.messages == []
