"""Diving tests — conditional on Level 30+."""

import pytest


@pytest.mark.live
@pytest.mark.diving
class TestDiving:
    """Diving gameplay (5 tests). Requires level 30+ and gold."""

    @pytest.mark.order(32)
    @pytest.mark.timeout(15)
    def test_get_diving_config(self, auth_token):
        """Diving config endpoint returns board configuration."""
        from ff_agent import api_client as api

        result = api.get_diving_config()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.order(33)
    @pytest.mark.timeout(15)
    def test_get_diving_state(self, auth_token):
        """Diving state endpoint returns status."""
        from ff_agent import api_client as api

        result = api.get_diving_state()
        assert result is not None

    @pytest.mark.order(34)
    @pytest.mark.timeout(15)
    def test_get_diving_jackpots(self, auth_token):
        """Diving jackpots endpoint returns values."""
        from ff_agent import api_client as api

        result = api.get_diving_jackpots()
        assert result is not None

    @pytest.mark.order(35)
    @pytest.mark.timeout(30)
    def test_buy_diving_ticket(self, auth_token, test_session):
        """Buy a gold diving ticket (skip if level < 30 or gold < 2500)."""
        from ff_agent import api_client as api
        from .helpers import get_current_profile

        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30; diving unavailable")

        profile = get_current_profile()
        gold = profile.get("gold", 0)
        if gold < 2500:
            pytest.skip(f"Insufficient gold ({gold:.0f}) for diving ticket")

        result = api.buy_diving_ticket_with_gold("Regular", 1)
        assert result is not None

    @pytest.mark.order(36)
    @pytest.mark.timeout(120)
    def test_dive_full_session(self, auth_token, test_session):
        """Full WebSocket diving session with cell reveals."""
        from ff_agent import api_client as api, diving_client, auth

        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30; diving unavailable")

        # Use ticket
        use_result = api.use_diving_ticket("Regular", "X1")
        if isinstance(use_result, dict) and use_result.get("code") == 400:
            pytest.skip(f"Cannot use ticket: {use_result.get('message')}")

        # Start dive
        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            pytest.skip(f"Cannot start dive: {start_result.get('message')}")

        # Play via WebSocket
        token = auth.get_token()
        result = diving_client.dive_session(token, max_picks=3)

        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "cells_revealed" in result
            assert "board_size" in result
