"""Tests for utils/case.py — pure function case conversion."""

from whatsapp_cloud_api.utils.case import to_camel, to_camel_deep, to_snake, to_snake_deep

# ── to_camel ────────────────────────────────────────────────────────


class TestToCamel:
    def test_basic(self):
        assert to_camel("phone_number_id") == "phoneNumberId"

    def test_single_word(self):
        assert to_camel("name") == "name"

    def test_already_camel(self):
        assert to_camel("phoneNumberId") == "phoneNumberId"

    def test_with_numbers(self):
        assert to_camel("error_code_2") == "errorCode2"

    def test_empty_string(self):
        assert to_camel("") == ""

    def test_leading_underscore_preserved(self):
        # _CAMEL_RE only matches _[a-z0-9], so leading underscore before uppercase stays
        result = to_camel("_private")
        assert result == "Private"

    def test_multiple_underscores(self):
        assert to_camel("a_b_c") == "aBC"


# ── to_snake ────────────────────────────────────────────────────────


class TestToSnake:
    def test_basic(self):
        assert to_snake("phoneNumberId") == "phone_number_id"

    def test_single_word(self):
        assert to_snake("name") == "name"

    def test_already_snake(self):
        assert to_snake("phone_number_id") == "phone_number_id"

    def test_with_numbers(self):
        assert to_snake("errorCode2") == "error_code2"

    def test_empty_string(self):
        assert to_snake("") == ""

    def test_all_uppercase(self):
        # Only matches [a-z0-9][A-Z] boundaries
        assert to_snake("URL") == "url"


# ── to_camel_deep ──────────────────────────────────────────────────


class TestToCamelDeep:
    def test_nested_dict(self):
        result = to_camel_deep({"phone_number_id": {"display_name": "test"}})
        assert result == {"phoneNumberId": {"displayName": "test"}}

    def test_list_of_dicts(self):
        result = to_camel_deep([{"first_name": "a"}, {"last_name": "b"}])
        assert result == [{"firstName": "a"}, {"lastName": "b"}]

    def test_non_dict_passthrough(self):
        assert to_camel_deep(42) == 42
        assert to_camel_deep("hello") == "hello"
        assert to_camel_deep(None) is None

    def test_mixed_nesting(self):
        result = to_camel_deep({"items": [{"item_id": 1}]})
        assert result == {"items": [{"itemId": 1}]}


# ── to_snake_deep ──────────────────────────────────────────────────


class TestToSnakeDeep:
    def test_nested_dict(self):
        result = to_snake_deep({"phoneNumberId": {"displayName": "test"}})
        assert result == {"phone_number_id": {"display_name": "test"}}

    def test_list_of_dicts(self):
        result = to_snake_deep([{"firstName": "a"}, {"lastName": "b"}])
        assert result == [{"first_name": "a"}, {"last_name": "b"}]

    def test_non_dict_passthrough(self):
        assert to_snake_deep(42) == 42
        assert to_snake_deep("hello") == "hello"
        assert to_snake_deep(None) is None

    def test_empty_dict(self):
        assert to_snake_deep({}) == {}

    def test_empty_list(self):
        assert to_snake_deep([]) == []
