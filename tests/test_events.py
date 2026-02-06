"""Tests for events/events.py — frozen dataclass events."""

import dataclasses

import pytest

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
    MessageEvent,
    MessageFailed,
    MessageRead,
    MessageSent,
    OrderReceived,
    ReactionReceived,
    StatusEvent,
    StickerReceived,
    TextReceived,
    UnknownMessageReceived,
    VideoReceived,
    WhatsAppEvent,
)

ALL_EVENT_CLASSES = [
    WhatsAppEvent,
    MessageEvent,
    TextReceived,
    ImageReceived,
    VideoReceived,
    AudioReceived,
    DocumentReceived,
    StickerReceived,
    LocationReceived,
    ContactsReceived,
    ReactionReceived,
    ButtonReply,
    ListReply,
    FlowResponse,
    OrderReceived,
    StatusEvent,
    MessageSent,
    MessageDelivered,
    MessageRead,
    MessageFailed,
    UnknownMessageReceived,
]


class TestEventInstantiation:
    @pytest.mark.parametrize("cls", ALL_EVENT_CLASSES, ids=lambda c: c.__name__)
    def test_instantiates_with_defaults(self, cls):
        """All events should be instantiable with no args (all fields have defaults)."""
        event = cls()
        assert event is not None


class TestEventFrozen:
    @pytest.mark.parametrize("cls", ALL_EVENT_CLASSES, ids=lambda c: c.__name__)
    def test_frozen(self, cls):
        event = cls()
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.phone_number_id = "should_fail"  # type: ignore[misc]


class TestInheritance:
    def test_text_received_is_message_event(self):
        assert issubclass(TextReceived, MessageEvent)
        assert issubclass(TextReceived, WhatsAppEvent)

    def test_image_received_is_message_event(self):
        assert issubclass(ImageReceived, MessageEvent)

    def test_message_sent_is_status_event(self):
        assert issubclass(MessageSent, StatusEvent)
        assert issubclass(MessageSent, WhatsAppEvent)

    def test_message_failed_is_status_event(self):
        assert issubclass(MessageFailed, StatusEvent)

    def test_unknown_is_message_event(self):
        assert issubclass(UnknownMessageReceived, MessageEvent)


class TestSpecificEvents:
    def test_text_received(self):
        evt = TextReceived(body="Hello", preview_url=True, from_number="123")
        assert evt.body == "Hello"
        assert evt.preview_url is True
        assert evt.from_number == "123"

    def test_image_received(self):
        evt = ImageReceived(image_id="img1", mime_type="image/jpeg", sha256="abc", caption="pic")
        assert evt.image_id == "img1"
        assert evt.caption == "pic"

    def test_button_reply(self):
        evt = ButtonReply(button_id="btn1", button_title="Yes")
        assert evt.button_id == "btn1"
        assert evt.button_title == "Yes"

    def test_list_reply(self):
        evt = ListReply(list_id="row1", list_title="Option 1", list_description="Desc")
        assert evt.list_description == "Desc"

    def test_flow_response(self):
        evt = FlowResponse(response_json={"key": "val"}, flow_token="tok")
        assert evt.response_json == {"key": "val"}
        assert evt.flow_token == "tok"

    def test_order_received(self):
        evt = OrderReceived(catalog_id="cat1", product_items=[{"id": "p1"}])
        assert evt.catalog_id == "cat1"
        assert len(evt.product_items) == 1

    def test_message_failed_with_errors(self):
        evt = MessageFailed(errors=[{"code": 131047, "title": "Error"}])
        assert len(evt.errors) == 1

    def test_unknown_message_received(self):
        evt = UnknownMessageReceived(raw_type="ephemeral", raw_data={"foo": "bar"})
        assert evt.raw_type == "ephemeral"

    def test_contacts_received(self):
        evt = ContactsReceived(contacts=[{"name": "John"}])
        assert evt.contacts == [{"name": "John"}]

    def test_location_received(self):
        evt = LocationReceived(latitude=1.0, longitude=2.0, name="Place", address="Addr")
        assert evt.latitude == 1.0
        assert evt.name == "Place"

    def test_sticker_received(self):
        evt = StickerReceived(sticker_id="stk1", animated=True)
        assert evt.animated is True

    def test_reaction_received(self):
        evt = ReactionReceived(emoji="👍", reacted_message_id="msg1")
        assert evt.emoji == "👍"

    def test_video_received(self):
        evt = VideoReceived(video_id="vid1", mime_type="video/mp4", caption="clip")
        assert evt.video_id == "vid1"

    def test_audio_received(self):
        evt = AudioReceived(audio_id="aud1", voice=True)
        assert evt.voice is True

    def test_document_received(self):
        evt = DocumentReceived(document_id="doc1", filename="file.pdf")
        assert evt.filename == "file.pdf"
