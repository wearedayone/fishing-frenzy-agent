"""Mock-based tool tests — verify tool wrappers with fake API data.

Note: api_client._request receives paths WITHOUT the /v1 prefix
(e.g. "/users/me", not "/v1/users/me") since BASE_URL includes /v1.
"""

import json

import pytest

from tests.mock_api import mock_api_client, mock_fishing_client, load_fixture


class TestMockTools:
    """Tool functions with mocked API backends (~8 tests)."""

    def test_get_profile_extracts_fields(self, mock_account):
        """get_profile() extracts correct fields from mock profile."""
        from ff_agent.server import get_profile

        with mock_api_client({("GET", "/users/me"): "profile"}):
            result = json.loads(get_profile())

        assert result["username"] == "TestBot_0xABCD"
        assert result["level"] == 25
        assert result["gold"] == 3200.5
        assert result["energy"] == 14
        assert result["maxEnergy"] == 30
        assert result["karma"] == 85000

    def test_sell_all_fish_with_verification(self, mock_account):
        """sell_all_fish() includes verification with gold delta."""
        from ff_agent.server import sell_all_fish

        profile_before = {
            "gold": 3000, "energy": 14, "level": 25, "exp": 12450,
            "username": "TestBot"
        }
        profile_after = {
            "gold": 3245, "energy": 14, "level": 25, "exp": 12450,
            "username": "TestBot"
        }

        call_count = [0]

        def _request_side_effect(method, path, **kwargs):
            if path == "/users/me":
                call_count[0] += 1
                return profile_before if call_count[0] <= 1 else profile_after
            if path == "/fish/sellAll":
                return load_fixture("sell_all")
            return {"code": 404}

        from unittest.mock import patch
        with patch("ff_agent.api_client._request", side_effect=_request_side_effect):
            result = json.loads(sell_all_fish())

        assert "result" in result
        assert result["verified"]["gold_change"] == 245

    def test_buy_item_sushi_auto_use(self, mock_account):
        """buy_item("sushi") auto-uses and shows energy change."""
        from ff_agent.server import buy_item

        call_count = [0]
        profile_before = {"gold": 3000, "energy": 10, "level": 25, "exp": 0, "username": "T"}
        profile_after = {"gold": 2500, "energy": 15, "level": 25, "exp": 0, "username": "T"}

        def _request_side_effect(method, path, **kwargs):
            if path == "/users/me":
                call_count[0] += 1
                return profile_before if call_count[0] <= 1 else profile_after
            if "/buy" in path or "/use" in path:
                return {"success": True}
            return {"code": 404}

        from unittest.mock import patch
        with patch("ff_agent.api_client._request", side_effect=_request_side_effect):
            result = json.loads(buy_item("sushi"))

        assert result["bought"] == 1
        assert result["item"] == "sushi"
        assert result["used"] is True
        assert result["verified"]["energy_change"] == 5
        assert result["verified"]["gold_change"] == -500

    def test_buy_item_insufficient_gold(self, mock_account):
        """buy_item with insufficient gold returns resource_depleted error."""
        from ff_agent.server import buy_item

        def _request(method, path, **kwargs):
            if "/buy" in path:
                return {"code": 400, "message": "Not enough gold"}
            if path == "/users/me":
                return {"gold": 100, "energy": 10, "level": 1, "exp": 0, "username": "T"}
            return {"code": 404}

        from unittest.mock import patch
        with patch("ff_agent.api_client._request", side_effect=_request):
            result = json.loads(buy_item("sushi"))

        assert result["success"] is False
        assert result["error_type"] == "resource_depleted"

    def test_fish_with_mock_success(self, mock_account):
        """fish() with mocked fishing_client returns structured result."""
        from ff_agent.server import fish

        success_fixture = load_fixture("fish_session_success")

        with mock_fishing_client([success_fixture]) as log:
            result = json.loads(fish("short_range"))

        assert result["success"] is True
        assert result["fish"]["name"] == "Golden Koi"
        assert result["fish"]["quality"] == 5
        assert len(log) == 1

    def test_fish_with_mock_escaped(self, mock_account):
        """fish() handles escaped fish result."""
        from ff_agent.server import fish

        escaped_fixture = load_fixture("fish_session_escaped")

        with mock_fishing_client([escaped_fixture]) as log:
            result = json.loads(fish("short_range"))

        assert result["success"] is False
        assert "escaped" in result.get("error", "").lower()

    def test_get_profile_api_called_once(self, mock_account):
        """get_profile() makes exactly one API call."""
        from ff_agent.server import get_profile

        with mock_api_client({("GET", "/users/me"): "profile"}) as log:
            get_profile()

        assert len(log) == 1
        assert log[0][0] == "GET"
        assert log[0][1] == "/users/me"

    def test_error_on_timeout_classified(self):
        """Timeout errors are classified as transient."""
        from ff_agent.server import _game_error

        result = _game_error("fish", TimeoutError("Request timed out"))
        assert result["error_type"] == "transient"
        assert "try again" in result["suggestion"].lower()
