"""Tests for errors/graph_api_error.py — GraphApiError creation and helpers."""

from whatsapp_cloud_api.errors.graph_api_error import GraphApiError


class TestFromResponse:
    def test_nested_error_body(self):
        body = {
            "error": {
                "message": "Invalid token",
                "code": 190,
                "type": "OAuthException",
                "fbtrace_id": "trace123",
                "error_subcode": 460,
                "error_user_msg": "Your token expired",
                "error_data": {"some": "info"},
            }
        }
        err = GraphApiError.from_response(401, body)
        assert str(err) == "Invalid token"
        assert err.http_status == 401
        assert err.code == 190
        assert err.type == "OAuthException"
        assert err.fbtrace_id == "trace123"
        assert err.error_subcode == 460
        assert err.details == "Your token expired"
        assert err.error_data == {"some": "info"}
        assert err.raw == body

    def test_flat_error_body(self):
        body = {"message": "Rate limited", "code": 4, "type": "RateLimitError"}
        err = GraphApiError.from_response(429, body)
        assert str(err) == "Rate limited"
        assert err.code == 4

    def test_missing_fields_default(self):
        err = GraphApiError.from_response(500, {})
        assert str(err) == "Unknown Graph API error"
        assert err.code is None
        assert err.type == ""
        assert err.details is None
        assert err.error_subcode is None
        assert err.fbtrace_id is None
        assert err.error_data is None

    def test_retry_after_header_parsed(self):
        body = {"error": {"message": "Throttled", "code": 4}}
        err = GraphApiError.from_response(429, body, retry_after_header="30")
        assert err.retry.retry_after_ms == 30_000

    def test_details_prefers_error_user_msg(self):
        body = {
            "error": {
                "message": "Error",
                "error_user_msg": "User-facing message",
                "details": "Technical details",
            }
        }
        err = GraphApiError.from_response(400, body)
        assert err.details == "User-facing message"

    def test_details_falls_back_to_details(self):
        body = {"error": {"message": "Error", "details": "Technical details"}}
        err = GraphApiError.from_response(400, body)
        assert err.details == "Technical details"


class TestHelpers:
    def test_is_auth_error(self):
        err = GraphApiError("auth", code=190, http_status=401)
        assert err.is_auth_error() is True
        assert err.is_rate_limit() is False

    def test_is_rate_limit(self):
        err = GraphApiError("rate", code=4, http_status=429)
        assert err.is_rate_limit() is True
        assert err.is_auth_error() is False

    def test_is_template_error(self):
        err = GraphApiError("tpl", code=132000, http_status=400)
        assert err.is_template_error() is True

    def test_requires_token_refresh(self):
        err = GraphApiError("auth", code=190, http_status=401)
        assert err.requires_token_refresh() is True

    def test_not_requires_token_refresh(self):
        err = GraphApiError("param", code=100, http_status=400)
        assert err.requires_token_refresh() is False


class TestToDict:
    def test_serialization(self):
        err = GraphApiError(
            "Test error",
            http_status=400,
            code=100,
            type_="ParameterError",
            fbtrace_id="trace456",
        )
        d = err.to_dict()
        assert d["message"] == "Test error"
        assert d["http_status"] == 400
        assert d["code"] == 100
        assert d["type"] == "ParameterError"
        assert d["category"] == "parameter"
        assert d["fbtrace_id"] == "trace456"
        assert "retry" in d
        assert d["retry"]["action"] == "fix_and_retry"

    def test_to_dict_with_none_fields(self):
        err = GraphApiError("Minimal")
        d = err.to_dict()
        assert d["code"] is None
        assert d["fbtrace_id"] is None
