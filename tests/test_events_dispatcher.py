"""Tests for events/dispatcher.py — event dispatching from normalized webhooks."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from tests.conftest import build_webhook_payload
from whatsapp_cloud_api.events.dispatcher import _map_message, dispatch_webhook
from whatsapp_cloud_api.events.events import (
    AudioReceived,
    ButtonReply,
    ContactsReceived,
    DocumentReceived,
    FlowResponse,
    ImageReceived,
    ListReply,
    LocationReceived,
    MessageDelivered,
    MessageFailed,
    MessageRead,
    MessageSent,
    OrderReceived,
    ReactionReceived,
    StickerReceived,
    TextReceived,
    UnknownMessageReceived,
    VideoReceived,
)
from whatsapp_cloud_api.types import WebhookMessage
from whatsapp_cloud_api.webhooks.normalize import normalize_webhook


def _make_msg(**kwargs: Any) -> WebhookMessage:
    """Create a WebhookMessage with sensible defaults."""
    defaults = {"id": "wamid.1", "timestamp": "1234567890", "from_": "123"}
    defaults.update(kwargs)
    return WebhookMessage.model_validate(defaults)


class TestMapMessage:
    def test_text(self):
        msg = _make_msg(type="text", text={"body": "Hello"})
        event = _map_message(msg, "phone1")
        assert isinstance(event, TextReceived)
        assert event.body == "Hello"
        assert event.phone_number_id == "phone1"
        assert event.from_number == "123"

    def test_image(self):
        msg = _make_msg(
            type="image",
            image={"id": "img1", "mime_type": "image/jpeg", "sha256": "abc", "caption": "pic"},
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, ImageReceived)
        assert event.image_id == "img1"
        assert event.caption == "pic"

    def test_video(self):
        msg = _make_msg(type="video", video={"id": "vid1", "mime_type": "video/mp4", "sha256": "x"})
        event = _map_message(msg, "phone1")
        assert isinstance(event, VideoReceived)
        assert event.video_id == "vid1"

    def test_audio(self):
        audio = {"id": "aud1", "mime_type": "audio/ogg", "sha256": "x", "voice": True}
        msg = _make_msg(type="audio", audio=audio)
        event = _map_message(msg, "phone1")
        assert isinstance(event, AudioReceived)
        assert event.audio_id == "aud1"
        assert event.voice is True

    def test_document(self):
        msg = _make_msg(
            type="document",
            document={
                "id": "doc1",
                "mime_type": "application/pdf",
                "sha256": "x",
                "filename": "file.pdf",
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, DocumentReceived)
        assert event.filename == "file.pdf"

    def test_sticker(self):
        msg = _make_msg(
            type="sticker", sticker={"id": "stk1", "mime_type": "image/webp", "animated": True}
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, StickerReceived)
        assert event.animated is True

    def test_location(self):
        msg = _make_msg(
            type="location",
            location={"latitude": 1.0, "longitude": 2.0, "name": "Place", "address": "Addr"},
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, LocationReceived)
        assert event.latitude == 1.0
        assert event.name == "Place"

    def test_contacts(self):
        msg = _make_msg(type="contacts", contacts=[{"name": "John"}])
        event = _map_message(msg, "phone1")
        assert isinstance(event, ContactsReceived)
        assert event.contacts == [{"name": "John"}]

    def test_reaction(self):
        msg = _make_msg(
            type="reaction", reaction={"emoji": "\U0001f44d", "message_id": "msg1"}
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, ReactionReceived)
        assert event.emoji == "\U0001f44d"
        assert event.reacted_message_id == "msg1"

    def test_order(self):
        msg = _make_msg(
            type="order",
            order={"catalog_id": "cat1", "product_items": [{"id": "p1"}], "order_text": "note"},
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, OrderReceived)
        assert event.catalog_id == "cat1"
        assert event.order_text == "note"

    def test_unknown_type(self):
        msg = _make_msg(type="ephemeral")
        event = _map_message(msg, "phone1")
        assert isinstance(event, UnknownMessageReceived)
        assert event.raw_type == "ephemeral"


class TestMapInteractive:
    def test_button_reply(self):
        msg = _make_msg(
            type="interactive",
            interactive={
                "type": "button_reply",
                "button_reply": {"id": "btn1", "title": "Yes"},
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, ButtonReply)
        assert event.button_id == "btn1"
        assert event.button_title == "Yes"

    def test_list_reply(self):
        msg = _make_msg(
            type="interactive",
            interactive={
                "type": "list_reply",
                "list_reply": {"id": "row1", "title": "Option", "description": "Desc"},
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, ListReply)
        assert event.list_id == "row1"
        assert event.list_description == "Desc"

    def test_nfm_reply_with_dict(self):
        msg = _make_msg(
            type="interactive",
            interactive={
                "type": "nfm_reply",
                "nfm_reply": {
                    "response_json": {"key": "val"},
                    "flow_token": "tok",
                },
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, FlowResponse)
        assert event.response_json == {"key": "val"}
        assert event.flow_token == "tok"

    def test_nfm_reply_with_json_string(self):
        msg = _make_msg(
            type="interactive",
            interactive={
                "type": "nfm_reply",
                "nfm_reply": {
                    "response_json": '{"key": "val"}',
                    "flow_token": "tok",
                },
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, FlowResponse)
        assert event.response_json == {"key": "val"}

    def test_nfm_reply_with_invalid_json_string(self):
        msg = _make_msg(
            type="interactive",
            interactive={
                "type": "nfm_reply",
                "nfm_reply": {"response_json": "not valid json"},
            },
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, FlowResponse)
        assert event.response_json == {}

    def test_unknown_interactive_type(self):
        msg = _make_msg(
            type="interactive",
            interactive={"type": "custom_reply", "custom_reply": {}},
        )
        event = _map_message(msg, "phone1")
        assert isinstance(event, UnknownMessageReceived)
        assert event.raw_type == "interactive:custom_reply"


class TestDispatchWebhook:
    def test_dispatches_messages(self):
        payload = build_webhook_payload(
            messages=[
                {
                    "from": "123",
                    "id": "m1",
                    "timestamp": "1",
                    "type": "text",
                    "text": {"body": "Hi"},
                }
            ]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        assert emitter.emit.call_count == 1
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, TextReceived)
        assert event.body == "Hi"

    def test_dispatches_statuses(self):
        payload = build_webhook_payload(
            statuses=[
                {"id": "m1", "status": "delivered", "timestamp": "1", "recipient_id": "456"}
            ]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        assert emitter.emit.call_count == 1
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, MessageDelivered)

    def test_status_sent(self):
        payload = build_webhook_payload(
            statuses=[{"id": "m1", "status": "sent", "timestamp": "1", "recipient_id": "456"}]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, MessageSent)

    def test_status_read(self):
        payload = build_webhook_payload(
            statuses=[{"id": "m1", "status": "read", "timestamp": "1", "recipient_id": "456"}]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, MessageRead)

    def test_status_failed(self):
        payload = build_webhook_payload(
            statuses=[
                {
                    "id": "m1",
                    "status": "failed",
                    "timestamp": "1",
                    "recipient_id": "456",
                    "errors": [{"code": 131047}],
                }
            ]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, MessageFailed)
        assert len(event.errors) == 1

    def test_status_unknown_defaults_to_sent(self):
        payload = build_webhook_payload(
            statuses=[
                {"id": "m1", "status": "pending", "timestamp": "1", "recipient_id": "456"}
            ]
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        event = emitter.emit.call_args[0][0]
        assert isinstance(event, MessageSent)

    def test_empty_webhook_no_emits(self):
        webhook = normalize_webhook({})
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        assert emitter.emit.call_count == 0

    def test_multiple_messages_and_statuses(self):
        payload = build_webhook_payload(
            messages=[
                {"from": "1", "id": "m1", "timestamp": "1", "type": "text", "text": {"body": "A"}},
                {"from": "2", "id": "m2", "timestamp": "2", "type": "image", "image": {"id": "i1"}},
            ],
            statuses=[
                {"id": "s1", "status": "sent", "timestamp": "3", "recipient_id": "3"},
            ],
        )
        webhook = normalize_webhook(payload)
        emitter = MagicMock()
        dispatch_webhook(webhook, emitter)
        assert emitter.emit.call_count == 3
        events = [call[0][0] for call in emitter.emit.call_args_list]
        assert isinstance(events[0], TextReceived)
        assert isinstance(events[1], ImageReceived)
        assert isinstance(events[2], MessageSent)
