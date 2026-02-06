"""Tests for resources/messages/models.py — Pydantic message input models."""

import pytest
from pydantic import ValidationError

from whatsapp_cloud_api.resources.messages.models import (
    BaseMessage,
    DocumentPayloadById,
    InteractiveButton,
    InteractiveButtonsMessage,
    InteractiveListMessage,
    ListRow,
    ListSection,
    LocationPayload,
    MediaById,
    MediaByLink,
    TextMessage,
)


class TestBaseMessage:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            BaseMessage()  # type: ignore[call-arg]

    def test_valid_creation(self):
        msg = BaseMessage(phone_number_id="123", to="456")
        assert msg.phone_number_id == "123"
        assert msg.to == "456"
        assert msg.recipient_type == "individual"

    def test_recipient_type_literal(self):
        msg = BaseMessage(phone_number_id="123", to="456", recipient_type="group")
        assert msg.recipient_type == "group"

    def test_invalid_recipient_type(self):
        with pytest.raises(ValidationError):
            BaseMessage(phone_number_id="123", to="456", recipient_type="broadcast")

    def test_biz_opaque_callback_data_max_length(self):
        # Exactly 512 should be fine
        msg = BaseMessage(phone_number_id="1", to="2", biz_opaque_callback_data="a" * 512)
        assert len(msg.biz_opaque_callback_data) == 512

    def test_biz_opaque_callback_data_over_limit(self):
        with pytest.raises(ValidationError):
            BaseMessage(phone_number_id="1", to="2", biz_opaque_callback_data="a" * 513)


class TestMediaUnion:
    def test_media_by_id(self):
        m = MediaById(id="media123", caption="Test")
        assert m.id == "media123"

    def test_media_by_link(self):
        m = MediaByLink(link="https://example.com/img.jpg")
        assert m.link == "https://example.com/img.jpg"
        assert m.caption is None


class TestTextMessage:
    def test_basic(self):
        msg = TextMessage(phone_number_id="1", to="2", body="Hello")
        assert msg.body == "Hello"
        assert msg.preview_url is False


class TestInteractiveButton:
    def test_max_length_id(self):
        # 256 chars should be fine
        btn = InteractiveButton(id="a" * 256, title="OK")
        assert len(btn.id) == 256

    def test_over_max_length_id(self):
        with pytest.raises(ValidationError):
            InteractiveButton(id="a" * 257, title="OK")

    def test_max_length_title(self):
        btn = InteractiveButton(id="1", title="a" * 20)
        assert len(btn.title) == 20

    def test_over_max_length_title(self):
        with pytest.raises(ValidationError):
            InteractiveButton(id="1", title="a" * 21)


class TestInteractiveButtonsMessage:
    def test_buttons_min_length(self):
        with pytest.raises(ValidationError):
            InteractiveButtonsMessage(
                phone_number_id="1", to="2", body_text="text", buttons=[]
            )

    def test_buttons_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveButtonsMessage(
                phone_number_id="1",
                to="2",
                body_text="text",
                buttons=[
                    InteractiveButton(id=str(i), title=f"B{i}") for i in range(4)
                ],
            )

    def test_buttons_valid_range(self):
        msg = InteractiveButtonsMessage(
            phone_number_id="1",
            to="2",
            body_text="Choose",
            buttons=[
                InteractiveButton(id="1", title="A"),
                InteractiveButton(id="2", title="B"),
                InteractiveButton(id="3", title="C"),
            ],
        )
        assert len(msg.buttons) == 3

    def test_body_text_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveButtonsMessage(
                phone_number_id="1",
                to="2",
                body_text="a" * 1025,
                buttons=[InteractiveButton(id="1", title="OK")],
            )

    def test_footer_text_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveButtonsMessage(
                phone_number_id="1",
                to="2",
                body_text="text",
                footer_text="a" * 61,
                buttons=[InteractiveButton(id="1", title="OK")],
            )


class TestListRow:
    def test_max_length_id(self):
        row = ListRow(id="a" * 200, title="t")
        assert len(row.id) == 200

    def test_over_max_length_id(self):
        with pytest.raises(ValidationError):
            ListRow(id="a" * 201, title="t")

    def test_max_length_title(self):
        row = ListRow(id="1", title="a" * 24)
        assert len(row.title) == 24

    def test_over_max_length_title(self):
        with pytest.raises(ValidationError):
            ListRow(id="1", title="a" * 25)

    def test_description_max_length(self):
        row = ListRow(id="1", title="t", description="a" * 72)
        assert len(row.description) == 72

    def test_description_over_max_length(self):
        with pytest.raises(ValidationError):
            ListRow(id="1", title="t", description="a" * 73)


class TestListSection:
    def test_rows_min_length(self):
        with pytest.raises(ValidationError):
            ListSection(title="sec", rows=[])

    def test_rows_max_length(self):
        with pytest.raises(ValidationError):
            ListSection(
                title="sec",
                rows=[ListRow(id=str(i), title=f"R{i}") for i in range(11)],
            )

    def test_valid_rows(self):
        sec = ListSection(
            title="sec", rows=[ListRow(id="1", title="Row1")]
        )
        assert len(sec.rows) == 1


class TestInteractiveListMessage:
    def test_sections_min_length(self):
        with pytest.raises(ValidationError):
            InteractiveListMessage(
                phone_number_id="1",
                to="2",
                body_text="text",
                button_text="Menu",
                sections=[],
            )

    def test_sections_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveListMessage(
                phone_number_id="1",
                to="2",
                body_text="text",
                button_text="Menu",
                sections=[
                    ListSection(title=f"S{i}", rows=[ListRow(id=str(i), title=f"R{i}")])
                    for i in range(11)
                ],
            )

    def test_body_text_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveListMessage(
                phone_number_id="1",
                to="2",
                body_text="a" * 4097,
                button_text="Menu",
                sections=[ListSection(title="s", rows=[ListRow(id="1", title="r")])],
            )

    def test_button_text_max_length(self):
        with pytest.raises(ValidationError):
            InteractiveListMessage(
                phone_number_id="1",
                to="2",
                body_text="text",
                button_text="a" * 21,
                sections=[ListSection(title="s", rows=[ListRow(id="1", title="r")])],
            )


class TestLocationPayload:
    def test_name_max_length(self):
        loc = LocationPayload(latitude=0.0, longitude=0.0, name="a" * 100)
        assert len(loc.name) == 100

    def test_name_over_max_length(self):
        with pytest.raises(ValidationError):
            LocationPayload(latitude=0.0, longitude=0.0, name="a" * 101)

    def test_address_max_length(self):
        loc = LocationPayload(latitude=0.0, longitude=0.0, address="a" * 300)
        assert len(loc.address) == 300

    def test_address_over_max_length(self):
        with pytest.raises(ValidationError):
            LocationPayload(latitude=0.0, longitude=0.0, address="a" * 301)


class TestDocumentPayloadById:
    def test_filename_max_length(self):
        doc = DocumentPayloadById(id="1", filename="a" * 240)
        assert len(doc.filename) == 240

    def test_filename_over_max_length(self):
        with pytest.raises(ValidationError):
            DocumentPayloadById(id="1", filename="a" * 241)
