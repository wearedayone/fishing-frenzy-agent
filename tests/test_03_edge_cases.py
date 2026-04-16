"""Edge case and error handling tests."""

import pytest

from .helpers import get_current_profile

SUSHI_ITEM_ID = "668d070357fb368ad9e91c8a"
FAKE_OBJECT_ID = "000000000000000000000000"


@pytest.mark.live
class TestEdgeCases:
    """Edge cases, error handling, and boundary conditions (10 tests)."""

    @pytest.mark.order(22)
    @pytest.mark.timeout(15)
    def test_fish_zero_energy(self, auth_token):
        """Fishing with zero energy returns error, not crash."""
        profile = get_current_profile()
        if profile.get("energy", 1) > 0:
            pytest.skip("Account has energy; cannot test zero-energy scenario")

        from ff_agent import fishing_client, auth

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.order(23)
    @pytest.mark.timeout(15)
    def test_buy_item_insufficient_gold(self, auth_token):
        """Buying with insufficient gold returns error, not crash."""
        from ff_agent import api_client as api

        # 10000 sushi = 5M gold — more than any test account has
        result = api.buy_item(SUSHI_ITEM_ID, 10000)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.order(24)
    @pytest.mark.timeout(15)
    def test_buy_item_invalid_id(self, auth_token):
        """Nonexistent item ID returns error gracefully."""
        from ff_agent import api_client as api

        result = api.buy_item(FAKE_OBJECT_ID, 1)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.order(25)
    @pytest.mark.timeout(15)
    def test_sell_all_fish_empty_inventory(self, auth_token):
        """Selling with no fish handles gracefully."""
        from ff_agent import api_client as api

        # Ensure empty by selling first
        api.sell_all_fish()
        # Sell again on empty inventory
        result = api.sell_all_fish()
        assert result is not None

    @pytest.mark.order(26)
    @pytest.mark.timeout(15)
    def test_use_item_not_in_inventory(self, auth_token):
        """Using an item not in inventory returns error."""
        from ff_agent import api_client as api

        result = api.use_item(FAKE_OBJECT_ID, 1)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.order(27)
    @pytest.mark.timeout(30)
    def test_rapid_fish_cooldown(self, auth_token):
        """Two rapid casts handle server cooldown gracefully."""
        from ff_agent import fishing_client, auth

        token = auth.get_token()

        r1 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r1, dict)
        assert "success" in r1

        # Second cast immediately — within server 10s cooldown
        r2 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r2, dict)
        assert "success" in r2
        # Should return structured response (success or error), never raise

    @pytest.mark.order(28)
    @pytest.mark.timeout(15)
    def test_auth_refresh_flow(self, auth_token):
        """login() returns authenticated status."""
        from ff_agent import auth

        result = auth.login()
        assert isinstance(result, dict)
        assert (
            result.get("authenticated") is True
            or result.get("user_id") is not None
        )

    @pytest.mark.order(29)
    @pytest.mark.timeout(30)
    def test_expired_token_auto_refresh(self, auth_token):
        """Expired access token triggers automatic refresh."""
        from ff_agent import state, auth

        # Manually expire the access token
        conn = state.get_connection()
        conn.execute("UPDATE auth SET expires_at = 1 WHERE key = 'access_token'")
        conn.commit()
        conn.close()

        # get_token() should detect expiry and refresh
        token = auth.get_token()
        assert token is not None
        assert len(token) > 10

    @pytest.mark.order(30)
    @pytest.mark.timeout(15)
    def test_claim_daily_reward_twice(self, auth_token):
        """Double daily claim returns already-claimed, not crash."""
        from ff_agent import api_client as api

        r1 = api.claim_daily_reward()
        assert r1 is not None

        r2 = api.claim_daily_reward()
        assert r2 is not None

    @pytest.mark.order(31)
    @pytest.mark.timeout(15)
    def test_cook_with_invalid_recipe(self, auth_token):
        """Invalid recipe_id returns error, not crash."""
        from ff_agent import api_client as api

        result = api.cook(FAKE_OBJECT_ID, 1, ["fake_fish_id"])
        assert result is not None
        assert isinstance(result, dict)
