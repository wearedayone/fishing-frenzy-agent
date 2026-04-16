"""Error classification: error types, suggestions, graceful failures.

RC8 — Review questions for Derek:
  - Are all error types accounted for?
  - Are suggestions actionable enough for the agent?
"""

import json

import pytest

from .helpers import get_current_profile, get_gold

FAKE_OBJECT_ID = "000000000000000000000000"


@pytest.mark.live
class TestErrorTypes:
    """Verify error classification produces correct error_type values."""

    @pytest.mark.order(95)
    @pytest.mark.timeout(15)
    def test_auth_error_suggests_login(self, auth_token):
        """Force auth error → error_type='auth', suggestion mentions 'login'."""
        from ff_agent.server import _game_error

        err = _game_error("test_action", "401 Unauthorized")
        assert err["error_type"] == "auth"
        assert "login" in err["suggestion"].lower()
        print(f"  Auth error: {err}")

    @pytest.mark.order(96)
    @pytest.mark.timeout(15)
    def test_resource_error_suggests_recovery(self, auth_token):
        """Resource depleted → error_type='resource_depleted'."""
        from ff_agent.server import _game_error

        # Energy depleted
        err_energy = _game_error("fish", "Not enough energy")
        assert err_energy["error_type"] == "resource_depleted"
        assert "sushi" in err_energy["suggestion"].lower() or "energy" in err_energy["suggestion"].lower()
        print(f"  Energy error: {err_energy}")

        # Gold depleted
        err_gold = _game_error("buy_item", "Insufficient gold")
        assert err_gold["error_type"] == "resource_depleted"
        print(f"  Gold error: {err_gold}")

    @pytest.mark.order(97)
    @pytest.mark.timeout(15)
    def test_game_logic_error_on_double_claim(self, auth_token):
        """Double daily claim → error_type='game_logic'."""
        from ff_agent.server import _game_error

        err = _game_error("claim_daily_reward", "Already claimed today")
        assert err["error_type"] == "game_logic"
        print(f"  Game logic error: {err}")

    @pytest.mark.order(98)
    @pytest.mark.timeout(15)
    def test_invalid_id_error_graceful(self, auth_token):
        """buy_item(nonexistent) → structured error, not crash."""
        from ff_agent.server import buy_item as buy_tool

        result_json = buy_tool("nonexistent_item_00000000", 1, False)
        result = json.loads(result_json)
        assert isinstance(result, dict)
        print(f"  Invalid item result: {result}")
        # Should have error info, not be a traceback
        assert "error" in result or "result" in result


@pytest.mark.live
class TestVerificationOnFailure:
    """Verify that failed operations don't change game state."""

    @pytest.mark.order(99)
    @pytest.mark.timeout(15)
    def test_failed_buy_no_gold_change(self, auth_token):
        """Insufficient gold buy → gold unchanged."""
        from ff_agent.server import buy_item as buy_tool

        gold_before = get_gold()

        # Try to buy 10000 sushi (5M gold)
        result_json = buy_tool("sushi", 10000, False)
        result = json.loads(result_json)

        gold_after = get_gold()
        print(f"  Gold: {gold_before:.0f} → {gold_after:.0f}")
        assert gold_after == gold_before, \
            f"Gold changed on failed buy: {gold_before:.0f} → {gold_after:.0f}"

    @pytest.mark.order(100)
    @pytest.mark.timeout(15)
    def test_profile_snapshot_failure_handled(self, auth_token):
        """_build_verification returns None when a snapshot is None."""
        from ff_agent.server import _build_verification

        result = _build_verification(None, {"gold": 100, "energy": 10, "xp": 50})
        assert result is None

        result2 = _build_verification({"gold": 100, "energy": 10, "xp": 50}, None)
        assert result2 is None

        # Both valid → should return dict
        result3 = _build_verification(
            {"gold": 100, "energy": 10, "xp": 50},
            {"gold": 200, "energy": 8, "xp": 60},
        )
        assert result3 is not None
        assert result3["gold_change"] == 100
        assert result3["energy_change"] == -2
        assert result3["xp_change"] == 10
        print(f"  Verification: {result3}")


@pytest.mark.live
class TestErrorStructure:
    """Verify all errors have consistent structure."""

    @pytest.mark.order(101)
    @pytest.mark.timeout(15)
    def test_all_errors_have_type_and_message(self, auth_token):
        """Every _game_error has error_type, error, suggestion, and action."""
        from ff_agent.server import _game_error

        test_cases = [
            ("fish", "Not enough energy"),
            ("buy_item", "Insufficient gold"),
            ("login", "401 Unauthorized"),
            ("dive", "Connection timeout"),
            ("claim_quest", "Quest already completed"),
            ("sell_fish", "Item not found"),
            ("fish", "Please wait 10 seconds"),
        ]

        for action, error_msg in test_cases:
            err = _game_error(action, error_msg)
            assert "error_type" in err, f"Missing error_type for: {error_msg}"
            assert "error" in err, f"Missing error for: {error_msg}"
            assert "suggestion" in err, f"Missing suggestion for: {error_msg}"
            assert "action" in err, f"Missing action for: {error_msg}"
            assert err["action"] == action
            assert err["success"] is False
            print(f"  {action}/{error_msg} → type={err['error_type']}")

    @pytest.mark.order(102)
    @pytest.mark.timeout(15)
    def test_suggestions_are_actionable(self, auth_token):
        """Suggestions reference specific tool names or actions."""
        from ff_agent.server import _game_error

        # Auth → should mention login()
        err = _game_error("fish", "401 Unauthorized")
        assert "login" in err["suggestion"].lower()

        # Energy → should mention sushi or energy
        err = _game_error("fish", "Not enough energy")
        assert any(w in err["suggestion"].lower() for w in ("sushi", "energy", "buy"))

        # Not found → should mention inventory or quests
        err = _game_error("sell_fish", "Item not found")
        assert any(w in err["suggestion"].lower() for w in ("inventory", "quest", "id", "check"))

        # Cooldown → should mention wait
        err = _game_error("fish", "Please wait 10 seconds")
        assert any(w in err["suggestion"].lower() for w in ("wait", "cooldown", "10"))

        print("  All suggestions are actionable")
