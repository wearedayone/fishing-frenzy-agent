"""Core gameplay loop tests: fish -> sell -> buy -> cook -> quests."""

import time

import pytest

from .helpers import get_current_profile, wait_for_cooldown

SUSHI_ITEM_ID = "668d070357fb368ad9e91c8a"


@pytest.mark.live
class TestCoreLoop:
    """Core gameplay loop (14 tests)."""

    @pytest.mark.order(8)
    @pytest.mark.timeout(10)
    def test_start_play_session(self, auth_token, test_session):
        """Start a tracked play session, get session ID."""
        from ff_agent import state

        session_id = state.start_session("balanced")
        assert isinstance(session_id, int)
        assert session_id > 0
        test_session.session_id = session_id

    @pytest.mark.order(9)
    @pytest.mark.timeout(10)
    def test_get_session_stats_empty(self, auth_token):
        """Session stats work with minimal history."""
        from ff_agent import state

        lifetime = state.get_lifetime_stats()
        for key in ("total_sessions", "total_fish", "total_gold",
                     "total_xp", "total_energy"):
            assert key in lifetime, f"Missing stat: {key}"

    @pytest.mark.order(10)
    @pytest.mark.timeout(60)
    def test_fish_single_cast(self, auth_token, test_session):
        """Single fishing cast returns expected result structure."""
        from ff_agent import fishing_client, auth

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")

        assert isinstance(result, dict)
        assert "success" in result

        if result["success"]:
            assert "fish" in result
            fish = result["fish"]
            for key in ("name", "quality", "xp_gain", "sell_price"):
                assert key in fish, f"Fish missing key: {key}"
            assert "player" in result
            test_session.has_fish_in_inventory = True
        else:
            # Even failures have structured responses
            assert "error" in result

    @pytest.mark.order(11)
    @pytest.mark.timeout(120)
    def test_fish_batch(self, auth_token, test_session):
        """Batch fishing returns per-cast results and summary totals."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        token = auth.get_token()
        result = fishing_client.fish_batch(token, "short_range", count=3)

        assert isinstance(result, dict)
        for key in ("total_casts", "successes", "failures",
                     "total_xp", "total_gold_value", "results"):
            assert key in result, f"Batch missing key: {key}"
        assert isinstance(result["results"], list)
        assert result["total_casts"] <= 3

        if result["successes"] > 0:
            test_session.has_fish_in_inventory = True

    @pytest.mark.order(12)
    @pytest.mark.timeout(15)
    def test_get_inventory(self, auth_token):
        """Inventory endpoint returns data."""
        from ff_agent import api_client as api

        result = api.get_inventory()
        assert result is not None
        assert isinstance(result, (dict, list))

    @pytest.mark.order(13)
    @pytest.mark.timeout(15)
    def test_sell_all_fish(self, auth_token, test_session):
        """Selling all fish increases (or maintains) gold balance."""
        from ff_agent import api_client as api

        profile = get_current_profile()
        test_session.gold_before_sell = profile.get("gold", 0)

        result = api.sell_all_fish()
        assert result is not None

        profile = get_current_profile()
        test_session.gold_after_sell = profile.get("gold", 0)
        assert test_session.gold_after_sell >= test_session.gold_before_sell

    @pytest.mark.order(14)
    @pytest.mark.timeout(15)
    def test_get_shop(self, auth_token):
        """Shop endpoint returns items."""
        from ff_agent import api_client as api

        result = api.get_shop()
        assert result is not None

    @pytest.mark.order(15)
    @pytest.mark.timeout(15)
    def test_buy_sushi_auto_use(self, auth_token, test_session):
        """Buy + use sushi: energy increases (skip if < 500 gold)."""
        from ff_agent import api_client as api

        profile = get_current_profile()
        gold = profile.get("gold", 0)
        if gold < 500:
            pytest.skip(f"Insufficient gold ({gold:.0f}) for sushi purchase")

        energy_before = profile.get("energy", 0)

        buy_result = api.buy_item(SUSHI_ITEM_ID, 1)
        assert buy_result is not None

        use_result = api.use_item(SUSHI_ITEM_ID, 1)
        assert use_result is not None

        profile = get_current_profile()
        energy_after = profile.get("energy", 0)
        assert energy_after >= energy_before

    @pytest.mark.order(16)
    @pytest.mark.timeout(15)
    def test_get_recipes(self, auth_token):
        """Active recipes endpoint returns data."""
        from ff_agent import api_client as api

        result = api.get_active_recipes()
        assert result is not None

    @pytest.mark.order(17)
    @pytest.mark.timeout(15)
    def test_claim_daily_reward(self, auth_token):
        """Daily reward claim succeeds or returns already-claimed."""
        from ff_agent import api_client as api

        result = api.claim_daily_reward()
        assert result is not None

    @pytest.mark.order(18)
    @pytest.mark.timeout(15)
    def test_get_quests(self, auth_token, test_session):
        """Quest list returns data."""
        from ff_agent import api_client as api

        result = api.get_user_quests()
        assert result is not None

    @pytest.mark.order(19)
    @pytest.mark.timeout(15)
    def test_get_accessories(self, auth_token):
        """Accessory list returns data with expected structure."""
        from ff_agent import api_client as api

        result = api.get_accessories()
        assert result is not None
        if isinstance(result, dict) and "accessories" in result:
            accs = result["accessories"]
            assert isinstance(accs, list)
            if accs:
                acc = accs[0]
                assert "name" in acc or "accessoryId" in acc

    @pytest.mark.order(20)
    @pytest.mark.timeout(15)
    def test_get_chests(self, auth_token):
        """Chest inventory endpoint returns data (may be empty)."""
        from ff_agent import api_client as api

        result = api.get_inventory_chests()
        assert result is not None

    @pytest.mark.order(21)
    @pytest.mark.timeout(15)
    def test_end_play_session(self, auth_token, test_session):
        """End session and verify lifetime stats include session data."""
        from ff_agent import state

        if test_session.session_id is None:
            pytest.skip("No session to end")

        state.update_session(
            test_session.session_id,
            fish_caught=5,
            gold_earned=100.0,
            xp_earned=50,
            energy_spent=5,
        )
        state.end_session(test_session.session_id)

        lifetime = state.get_lifetime_stats()
        assert lifetime["total_sessions"] >= 1
        assert lifetime["total_fish"] >= 5
        assert lifetime["total_gold"] >= 100.0
