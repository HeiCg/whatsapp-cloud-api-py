"""Tests for errors/retry.py — retry hints from error categories."""

import dataclasses

import pytest

from whatsapp_cloud_api.errors.retry import _CATEGORY_RETRY, RetryHint, get_retry_hint


class TestGetRetryHint:
    @pytest.mark.parametrize(
        "category,expected_action",
        list(_CATEGORY_RETRY.items()),
        ids=list(_CATEGORY_RETRY),
    )
    def test_all_category_mappings(self, category, expected_action):
        hint = get_retry_hint(category)
        assert hint.action == expected_action

    def test_throttling_default_60s_when_no_header(self):
        hint = get_retry_hint("throttling")
        assert hint.action == "retry_after"
        assert hint.retry_after_ms == 60_000

    def test_throttling_with_retry_after_header(self):
        hint = get_retry_hint("throttling", retry_after_header="30")
        assert hint.action == "retry_after"
        assert hint.retry_after_ms == 30_000

    def test_throttling_with_float_header(self):
        hint = get_retry_hint("throttling", retry_after_header="1.5")
        assert hint.retry_after_ms == 1500

    def test_invalid_retry_after_header_falls_back_to_default(self):
        hint = get_retry_hint("throttling", retry_after_header="not-a-number")
        assert hint.retry_after_ms == 60_000

    def test_non_throttling_with_retry_after_header(self):
        # retry_after_header is parsed but retry_after_ms only forced for "retry_after" action
        hint = get_retry_hint("authorization", retry_after_header="10")
        assert hint.action == "refresh_token"
        assert hint.retry_after_ms == 10_000

    def test_non_throttling_no_header(self):
        hint = get_retry_hint("authorization")
        assert hint.retry_after_ms is None

    def test_server_returns_retry(self):
        hint = get_retry_hint("server")
        assert hint.action == "retry"
        assert hint.retry_after_ms is None

    def test_unknown_returns_retry(self):
        hint = get_retry_hint("unknown")
        assert hint.action == "retry"


class TestRetryHintFrozen:
    def test_immutable(self):
        hint = RetryHint(action="retry")
        with pytest.raises(dataclasses.FrozenInstanceError):
            hint.action = "do_not_retry"  # type: ignore[misc]

    def test_slots(self):
        hint = RetryHint(action="retry")
        with pytest.raises((AttributeError, TypeError)):
            hint.extra = "nope"  # type: ignore[attr-defined]
