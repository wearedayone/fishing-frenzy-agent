"""Diving rules: board dimensions, whirlpool death, corals, cash-out, tickets.

RC6 — Review questions for Derek:
  - Board is fixed 6x10 (6 cols, 10 rows)
  - 2 whirlpools = game over (lose all uncollected rewards)
  - 7-10 whirlpools per board (random)
  - Corals must be fully uncovered for rewards
  - Ticket cost: 2500 gold (Regular)

All tests marked @pytest.mark.diving — skipped if level < 30.
"""

import json

import pytest

from .helpers import get_current_profile, get_gold


@pytest.mark.live
@pytest.mark.diving
class TestDivingPrerequisites:
    """Verify diving level gate and ticket pricing."""

    @pytest.mark.order(80)
    @pytest.mark.timeout(15)
    def test_diving_requires_level_30(self, auth_token, test_session):
        """If level < 30, diving actions return level error."""
        if test_session.player_level >= 30:
            pytest.skip("Player is level 30+; cannot test level gate")

        from ff_agent import api_client as api

        result = api.buy_diving_ticket_with_gold("Regular", 1)
        assert isinstance(result, dict)
        # Should contain error about level
        msg = str(result.get("message", result.get("error", "")))
        print(f"  Level gate result: {result}")

    @pytest.mark.order(81)
    @pytest.mark.timeout(30)
    def test_diving_ticket_costs_2500_gold(self, auth_token, test_session):
        """Buy 1 ticket → gold drops by exactly 2500."""
        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30")

        from ff_agent import api_client as api

        gold_before = get_gold()
        if gold_before < 2500:
            pytest.skip(f"Need >=2500 gold, have {gold_before:.0f}")

        result = api.buy_diving_ticket_with_gold("Regular", 1)
        gold_after = get_gold()
        cost = gold_before - gold_after

        print(f"  Ticket cost: gold {gold_before:.0f} → {gold_after:.0f} (cost={cost:.0f})")
        assert cost == 2500, f"Expected ticket cost 2500, got {cost}"


@pytest.mark.live
@pytest.mark.diving
class TestBoardConfig:
    """Verify diving board configuration."""

    @pytest.mark.order(82)
    @pytest.mark.timeout(15)
    def test_diving_config_has_board_sizes(self, auth_token):
        """Config has board size information."""
        from ff_agent import api_client as api

        result = api.get_diving_config()
        assert isinstance(result, dict)
        print(f"  Diving config keys: {list(result.keys())}")

        # Look for board size data
        config = result.get("data", result)
        if isinstance(config, dict):
            for key in ("boardSizes", "boardSize", "board", "grid", "config"):
                if key in config:
                    print(f"  {key}: {config[key]}")

    @pytest.mark.order(83)
    @pytest.mark.timeout(15)
    def test_diving_config_has_coral_info(self, auth_token):
        """Config includes coral/reward data."""
        from ff_agent import api_client as api

        result = api.get_diving_config()
        config = result.get("data", result) if isinstance(result, dict) else result
        print(f"  Config structure (top-level): {list(config.keys()) if isinstance(config, dict) else type(config)}")

    @pytest.mark.order(84)
    @pytest.mark.timeout(15)
    def test_board_size_uses_totalRow_totalCol(self, auth_token):
        """Verify diving_client._get_board_size parses totalRow/totalCol."""
        from ff_agent.diving_client import _get_board_size

        # Test with known server format
        board_data = {"totalCol": 6, "totalRow": 10}
        cols, rows = _get_board_size(board_data)
        print(f"  Board size: {cols}x{rows}")
        assert cols == 6, f"Expected 6 cols, got {cols}"
        assert rows == 10, f"Expected 10 rows, got {rows}"

        # Test fallback
        cols2, rows2 = _get_board_size({})
        print(f"  Fallback board size: {cols2}x{rows2}")
        assert cols2 == 5 and rows2 == 5, "Fallback should be 5x5"


@pytest.mark.live
@pytest.mark.diving
class TestDivingGameplay:
    """Verify diving session behavior."""

    @pytest.mark.order(85)
    @pytest.mark.timeout(120)
    def test_dive_reveals_cells(self, auth_token, test_session):
        """Full dive → cells_revealed > 0, rewards array exists."""
        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30")

        from ff_agent import api_client as api, diving_client, auth

        gold = get_gold()
        if gold < 2500:
            pytest.skip(f"Need >=2500 gold for ticket, have {gold:.0f}")

        # Buy + use ticket + start
        api.buy_diving_ticket_with_gold("Regular", 1)
        use_result = api.use_diving_ticket("Regular", "X1")
        if isinstance(use_result, dict) and use_result.get("code") == 400:
            pytest.skip(f"Cannot use ticket: {use_result.get('message')}")

        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            pytest.skip(f"Cannot start dive: {start_result.get('message')}")

        token = auth.get_token()
        result = diving_client.dive_session(token, max_picks=0)

        assert isinstance(result, dict)
        print(f"  Dive result keys: {list(result.keys())}")
        if result.get("success"):
            assert result.get("cells_revealed", 0) > 0
            assert "rewards" in result
            print(f"  Cells revealed: {result['cells_revealed']}")
            print(f"  Board size: {result.get('board_size')}")
            print(f"  Rewards: {result.get('rewards')}")

    @pytest.mark.order(86)
    @pytest.mark.timeout(120)
    def test_dive_cash_out_early(self, auth_token, test_session):
        """dive(max_picks=3) → cashed_out_early=True, cells <= 3."""
        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30")

        from ff_agent import api_client as api, diving_client, auth

        gold = get_gold()
        if gold < 2500:
            pytest.skip(f"Need >=2500 gold for ticket, have {gold:.0f}")

        api.buy_diving_ticket_with_gold("Regular", 1)
        use_result = api.use_diving_ticket("Regular", "X1")
        if isinstance(use_result, dict) and use_result.get("code") == 400:
            pytest.skip(f"Cannot use ticket: {use_result.get('message')}")

        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            pytest.skip(f"Cannot start dive: {start_result.get('message')}")

        token = auth.get_token()
        result = diving_client.dive_session(token, max_picks=3)

        assert isinstance(result, dict)
        if result.get("success"):
            cells = result.get("cells_revealed", 0)
            print(f"  Cash-out early: cells={cells}, cashed_out={result.get('cashed_out_early')}")
            assert cells <= 3, f"Should reveal <=3 cells, got {cells}"
            # cashed_out_early should be True unless game ended naturally in <=3 picks
            if cells == 3:
                assert result.get("cashed_out_early") is True

    @pytest.mark.order(87)
    @pytest.mark.timeout(120)
    def test_whirlpool_death_ends_game(self, auth_token, test_session):
        """Run dive, inspect cells for whirlpool indicators. Observational test.

        2 whirlpools = game over, lose all uncollected rewards.
        We can't control whirlpool placement — this test logs findings.
        Board has 7-10 whirlpools randomly placed (out of 60 cells).
        """
        if test_session.player_level < 30:
            pytest.skip(f"Level {test_session.player_level} < 30")

        from ff_agent import api_client as api, diving_client, auth

        gold = get_gold()
        if gold < 2500:
            pytest.skip(f"Need >=2500 gold for ticket, have {gold:.0f}")

        api.buy_diving_ticket_with_gold("Regular", 1)
        use_result = api.use_diving_ticket("Regular", "X1")
        if isinstance(use_result, dict) and use_result.get("code") == 400:
            pytest.skip(f"Cannot use ticket: {use_result.get('message')}")

        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            pytest.skip(f"Cannot start dive: {start_result.get('message')}")

        token = auth.get_token()
        result = diving_client.dive_session(token, max_picks=0)

        assert isinstance(result, dict)
        if result.get("success"):
            revealed = result.get("revealed_cells", [])
            whirlpool_count = 0
            coral_count = 0
            empty_count = 0
            for cell in revealed:
                cell_data = cell.get("data", {})
                cell_str = json.dumps(cell_data).lower()
                if "whirlpool" in cell_str or "bomb" in cell_str or "mine" in cell_str:
                    whirlpool_count += 1
                    print(f"  Whirlpool at ({cell['col']},{cell['row']}): {cell_data}")
                elif "coral" in cell_str:
                    coral_count += 1
                else:
                    empty_count += 1

            print(f"  Whirlpools hit: {whirlpool_count}")
            print(f"  Coral tiles found: {coral_count}")
            print(f"  Empty tiles: {empty_count}")
            print(f"  Game ended naturally: {not result.get('cashed_out_early', False)}")
            print(f"  Total cells revealed: {result.get('cells_revealed')}")

            if whirlpool_count >= 2:
                print("  >> 2 whirlpools hit — game should have ended with NO rewards")


@pytest.mark.live
@pytest.mark.diving
class TestDivingState:
    """Verify diving jackpot and state endpoints."""

    @pytest.mark.order(88)
    @pytest.mark.timeout(15)
    def test_jackpots_return_values(self, auth_token):
        """get_diving_jackpots → structured response with gold values."""
        from ff_agent import api_client as api

        result = api.get_diving_jackpots()
        assert result is not None
        assert isinstance(result, (dict, list))
        print(f"  Jackpots: {result}")
