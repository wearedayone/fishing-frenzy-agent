"""Output format and structure tests — verify tool outputs have correct shapes."""

import json

import pytest

from ff_agent.server import _game_error, _build_verification


KNOWN_ERROR_TYPES = {"auth", "transient", "resource_depleted", "game_logic", "blocked", "unknown"}

REQUIRED_ERROR_FIELDS = {"success", "error_type", "error", "suggestion", "action"}


class TestGameErrorFormat:
    """All _game_error() outputs have required fields and valid error_types."""

    def test_required_fields_present(self):
        result = _game_error("test_action", Exception("something broke"))
        assert REQUIRED_ERROR_FIELDS.issubset(result.keys())

    def test_success_always_false(self):
        result = _game_error("test_action", Exception("err"))
        assert result["success"] is False

    def test_error_type_in_known_set(self):
        """Test all classification paths produce known error types."""
        test_cases = [
            ("401 unauthorized", "auth"),
            ("Request timed out", "transient"),
            ("Connection refused", "transient"),
            ("Not enough energy", "resource_depleted"),
            ("Insufficient gold", "resource_depleted"),
            ("Already claimed", "game_logic"),
            ("Completed already", "game_logic"),
            ("Not found", "blocked"),
            ("Level requirement not met", "blocked"),
            ("Something weird", "unknown"),
            ("Cooldown 10 seconds", "game_logic"),
        ]
        for error_msg, expected_type in test_cases:
            result = _game_error("test", Exception(error_msg))
            assert result["error_type"] in KNOWN_ERROR_TYPES, (
                f"Error type '{result['error_type']}' not in known set for: {error_msg}"
            )
            assert result["error_type"] == expected_type, (
                f"Expected '{expected_type}' for '{error_msg}', got '{result['error_type']}'"
            )

    def test_api_response_overrides_classification(self):
        """API response body can override error classification."""
        api_resp = {"code": 400, "message": "Not enough energy to fish"}
        result = _game_error("fish", Exception("400 error"), api_resp)
        assert result["error_type"] == "resource_depleted"
        assert "energy" in result["suggestion"].lower()

    def test_action_field_matches_input(self):
        result = _game_error("sell_all_fish", Exception("err"))
        assert result["action"] == "sell_all_fish"


class TestBuildVerification:
    """_build_verification() produces correct before/after/change triplets."""

    def test_basic_verification(self):
        before = {"gold": 1000, "energy": 20, "xp": 5000}
        after = {"gold": 1500, "energy": 15, "xp": 5100}
        v = _build_verification(before, after)

        assert v["gold_before"] == 1000
        assert v["gold_after"] == 1500
        assert v["gold_change"] == 500
        assert v["energy_before"] == 20
        assert v["energy_after"] == 15
        assert v["energy_change"] == -5
        assert v["xp_before"] == 5000
        assert v["xp_after"] == 5100
        assert v["xp_change"] == 100

    def test_none_before_returns_none(self):
        assert _build_verification(None, {"gold": 100, "energy": 10, "xp": 0}) is None

    def test_none_after_returns_none(self):
        assert _build_verification({"gold": 100, "energy": 10, "xp": 0}, None) is None

    def test_both_none_returns_none(self):
        assert _build_verification(None, None) is None

    def test_zero_change(self):
        same = {"gold": 500, "energy": 10, "xp": 1000}
        v = _build_verification(same, same)
        assert v["gold_change"] == 0
        assert v["energy_change"] == 0
        assert v["xp_change"] == 0


class TestSessionStatsStructure:
    """Session stats have lifetime + recent_sessions keys."""

    def test_session_stats_structure(self, mock_account):
        """get_session_stats() returns valid structure."""
        from ff_agent.server import get_session_stats

        result = json.loads(get_session_stats())
        assert "lifetime" in result
        assert "recent_sessions" in result

        lifetime = result["lifetime"]
        assert "total_sessions" in lifetime
        assert "total_fish" in lifetime
        assert "total_gold" in lifetime
        assert "total_xp" in lifetime
        assert "total_energy" in lifetime

        assert isinstance(result["recent_sessions"], list)
