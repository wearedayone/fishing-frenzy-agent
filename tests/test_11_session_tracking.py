"""Session tracking: state DB, action log, stats accumulation.

RC7 — Review questions for Derek:
  - Are action log entries complete after each game action?
  - Do lifetime stats accumulate correctly across sessions?
"""

import pytest

from .helpers import get_current_profile, get_gold, wait_for_cooldown


@pytest.mark.live
class TestSessionTracking:
    """Verify play session lifecycle and stats."""

    @pytest.mark.order(89)
    @pytest.mark.timeout(10)
    def test_start_session_returns_id(self, auth_token):
        """start_play_session → valid session_id."""
        from ff_agent import state

        session_id = state.start_session("balanced")
        assert isinstance(session_id, int)
        assert session_id > 0
        print(f"  Session ID: {session_id}")

    @pytest.mark.order(90)
    @pytest.mark.timeout(10)
    def test_end_session_records_stats(self, auth_token):
        """End session with stats → included in history."""
        from ff_agent import state

        session_id = state.start_session("grind")
        state.update_session(session_id, fish_caught=10, gold_earned=500.0,
                             xp_earned=200, energy_spent=10)
        state.end_session(session_id)

        history = state.get_session_history(limit=1)
        assert len(history) >= 1

        latest = history[0]
        assert latest["id"] == session_id
        assert latest["fish_caught"] == 10
        assert latest["gold_earned"] == 500.0
        assert latest["xp_earned"] == 200
        assert latest["energy_spent"] == 10
        assert latest["ended_at"] is not None
        print(f"  Session #{session_id}: {latest}")

    @pytest.mark.order(91)
    @pytest.mark.timeout(10)
    def test_lifetime_stats_accumulate(self, auth_token):
        """After 2 sessions, totals = sum of both."""
        from ff_agent import state

        # Get current stats
        stats_before = state.get_lifetime_stats()

        # Create session 1
        s1 = state.start_session("test_a")
        state.update_session(s1, fish_caught=3, gold_earned=150.0, xp_earned=50, energy_spent=3)
        state.end_session(s1)

        # Create session 2
        s2 = state.start_session("test_b")
        state.update_session(s2, fish_caught=7, gold_earned=350.0, xp_earned=100, energy_spent=7)
        state.end_session(s2)

        stats_after = state.get_lifetime_stats()

        fish_delta = stats_after["total_fish"] - stats_before["total_fish"]
        gold_delta = stats_after["total_gold"] - stats_before["total_gold"]
        xp_delta = stats_after["total_xp"] - stats_before["total_xp"]
        energy_delta = stats_after["total_energy"] - stats_before["total_energy"]
        session_delta = stats_after["total_sessions"] - stats_before["total_sessions"]

        print(f"  Delta: fish={fish_delta}, gold={gold_delta}, "
              f"xp={xp_delta}, energy={energy_delta}, sessions={session_delta}")

        assert fish_delta == 10, f"Expected +10 fish, got +{fish_delta}"
        assert gold_delta == 500.0, f"Expected +500 gold, got +{gold_delta}"
        assert xp_delta == 150, f"Expected +150 xp, got +{xp_delta}"
        assert energy_delta == 10, f"Expected +10 energy, got +{energy_delta}"
        assert session_delta == 2, f"Expected +2 sessions, got +{session_delta}"


@pytest.mark.live
class TestActionLog:
    """Verify action log entries from game actions."""

    @pytest.mark.order(92)
    @pytest.mark.timeout(60)
    def test_fish_action_logged(self, auth_token):
        """After fish(), action_log has entry with action='fish'."""
        from ff_agent import state, fishing_client, auth

        wait_for_cooldown()

        if get_current_profile().get("energy", 0) < 1:
            pytest.skip("Need energy to fish")

        # Log a fish action manually (like server.py does)
        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")

        state.log_action(
            "fish",
            params={"range": "short_range"},
            result={"success": result.get("success")},
        )

        log = state.get_action_log(limit=5)
        fish_entries = [e for e in log if e["action"] == "fish"]
        assert len(fish_entries) >= 1, "No 'fish' entries in action log"
        print(f"  Fish log entry: {fish_entries[0]}")

    @pytest.mark.order(93)
    @pytest.mark.timeout(15)
    def test_sell_action_has_gold_delta(self, auth_token):
        """After sell_all via MCP tool, log has gold_before and gold_after."""
        from ff_agent import state

        gold_before = get_gold()
        state.log_action(
            "sell_all_fish",
            result={"sold": True},
            gold_before=gold_before,
            gold_after=gold_before,  # No actual sell, just testing log
        )

        log = state.get_action_log(limit=5)
        sell_entries = [e for e in log if e["action"] == "sell_all_fish"]
        assert len(sell_entries) >= 1, "No 'sell_all_fish' entries in action log"

        entry = sell_entries[0]
        assert entry["gold_before"] is not None, "gold_before not logged"
        assert entry["gold_after"] is not None, "gold_after not logged"
        print(f"  Sell log: gold_before={entry['gold_before']}, "
              f"gold_after={entry['gold_after']}")

    @pytest.mark.order(94)
    @pytest.mark.timeout(10)
    def test_log_entries_have_timestamps(self, auth_token):
        """All log entries have non-null timestamps."""
        from ff_agent import state

        # Ensure at least one entry exists
        state.log_action("test_timestamp_check")

        log = state.get_action_log(limit=10)
        assert len(log) >= 1, "Action log is empty"

        for entry in log:
            assert entry["timestamp"] is not None, \
                f"Entry #{entry['id']} missing timestamp"

        print(f"  Checked {len(log)} log entries — all have timestamps")
