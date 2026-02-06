"""Tests for errors/categorize.py — error code to category mapping."""

import pytest

from whatsapp_cloud_api.errors.categorize import _CODE_TO_CATEGORY, categorize_error


class TestCategorizeError:
    """All known code→category mappings plus edge cases."""

    @pytest.mark.parametrize(
        "code,expected",
        list(_CODE_TO_CATEGORY.items()),
        ids=[f"code_{c}" for c in _CODE_TO_CATEGORY],
    )
    def test_known_codes(self, code, expected):
        assert categorize_error(code) == expected

    def test_unknown_code_returns_unknown(self):
        assert categorize_error(99999) == "unknown"

    def test_code_none_http_500_returns_server(self):
        assert categorize_error(None, http_status=500) == "server"

    def test_code_none_http_502_returns_server(self):
        assert categorize_error(None, http_status=502) == "server"

    def test_code_none_http_400_returns_unknown(self):
        assert categorize_error(None, http_status=400) == "unknown"

    def test_code_none_no_status_returns_unknown(self):
        assert categorize_error(None) == "unknown"

    def test_known_code_overrides_http_status(self):
        # Even if HTTP status is 500, the code mapping wins
        assert categorize_error(190, http_status=500) == "authorization"

    # Spot-check specific categories
    def test_authorization_codes(self):
        assert categorize_error(0) == "authorization"
        assert categorize_error(190) == "authorization"

    def test_throttling_codes(self):
        assert categorize_error(4) == "throttling"
        assert categorize_error(80007) == "throttling"
        assert categorize_error(130429) == "throttling"
        assert categorize_error(131048) == "throttling"
        assert categorize_error(131056) == "throttling"

    def test_template_codes(self):
        assert categorize_error(132000) == "template"
        assert categorize_error(132001) == "template"
        assert categorize_error(132015) == "template"

    def test_media_codes(self):
        assert categorize_error(131051) == "media"
        assert categorize_error(131052) == "media"
        assert categorize_error(131053) == "media"

    def test_flow_codes(self):
        assert categorize_error(132068) == "flow"
        assert categorize_error(132069) == "flow"

    def test_phone_registration_codes(self):
        assert categorize_error(133000) == "phone_registration"
        assert categorize_error(133015) == "phone_registration"

    def test_integrity_codes(self):
        assert categorize_error(368) == "integrity"
        assert categorize_error(130497) == "integrity"

    def test_reengagement_window(self):
        assert categorize_error(131047) == "reengagement_window"
