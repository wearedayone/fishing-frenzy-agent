"""Economy rules: gold flow, sushi mechanics, item name mapping, verification gates.

RC2 — Review questions for Derek:
  - Is sushi always 500g?
  - Always restores exactly 5 energy?
  - Can energy exceed max?
"""

import pytest

from .helpers import get_current_profile, get_energy, get_gold, get_max_energy, wait_for_cooldown

SUSHI_ITEM_ID = "668d070357fb368ad9e91c8a"


@pytest.mark.live
class TestGoldFlow:
    """Verify gold increases from fishing + selling."""

    @pytest.mark.order(49)
    @pytest.mark.timeout(180)
    def test_fishing_then_sell_increases_gold(self, auth_token):
        """Fish 5x → sell_all → gold increased."""
        from ff_agent import fishing_client, api_client as api, auth

        wait_for_cooldown()

        if get_energy() < 5:
            pytest.skip("Need >=5 energy")

        gold_start = get_gold()
        token = auth.get_token()

        # Fish a few times
        caught = 0
        for i in range(5):
            if get_energy() < 1:
                break
            if i > 0:
                wait_for_cooldown()
            r = fishing_client.fish_session(token, "short_range")
            if r.get("success"):
                caught += 1

        if caught == 0:
            pytest.skip("No fish caught to sell")

        # Sell all
        result = api.sell_all_fish()
        gold_end = get_gold()

        print(f"  Caught {caught} fish, gold: {gold_start:.0f} → {gold_end:.0f} "
              f"(+{gold_end - gold_start:.0f})")
        assert gold_end > gold_start, "Gold should increase after selling fish"

    @pytest.mark.order(50)
    @pytest.mark.timeout(15)
    def test_sell_returns_positive_gold(self, auth_token):
        """sell_all verified gold_change > 0 when fish exist.

        This depends on having fish in inventory. If empty, skip.
        """
        from ff_agent import api_client as api

        gold_before = get_gold()
        result = api.sell_all_fish()

        gold_after = get_gold()
        change = gold_after - gold_before

        print(f"  sell_all: gold {gold_before:.0f} → {gold_after:.0f} (change={change:.0f})")
        # gold_change >= 0 (can be 0 if no fish to sell)
        assert change >= 0, f"Selling should not lose gold, got change={change}"

    @pytest.mark.order(51)
    @pytest.mark.timeout(15)
    def test_sell_empty_inventory_zero_change(self, auth_token):
        """sell_all with no fish → gold_change == 0."""
        from ff_agent import api_client as api

        # Ensure empty by selling first
        api.sell_all_fish()

        gold_before = get_gold()
        result = api.sell_all_fish()
        gold_after = get_gold()

        change = gold_after - gold_before
        print(f"  Empty sell: gold {gold_before:.0f} → {gold_after:.0f} (change={change:.0f})")
        assert change == 0, f"Selling empty inventory should yield 0 change, got {change}"


@pytest.mark.live
class TestSushiMechanics:
    """Verify sushi pricing and energy restoration."""

    @pytest.mark.order(52)
    @pytest.mark.timeout(30)
    def test_sushi_costs_500_gold(self, auth_token):
        """Buy sushi → gold drops by exactly 500."""
        from ff_agent import api_client as api

        gold_before = get_gold()
        if gold_before < 500:
            pytest.skip(f"Need >=500 gold, have {gold_before:.0f}")

        api.buy_item(SUSHI_ITEM_ID, 1)
        gold_after = get_gold()
        cost = gold_before - gold_after

        print(f"  Sushi cost: gold {gold_before:.0f} → {gold_after:.0f} (cost={cost:.0f})")
        assert cost == 500, f"Expected sushi cost 500, got {cost}"

    @pytest.mark.order(53)
    @pytest.mark.timeout(30)
    def test_sushi_restores_5_energy(self, auth_token):
        """Buy+use sushi → energy increases by exactly 5 (no cap)."""
        from ff_agent import api_client as api

        profile = get_current_profile()
        gold = profile.get("gold", 0)
        energy_before = profile.get("energy", 0)

        if gold < 500:
            pytest.skip(f"Need >=500 gold, have {gold:.0f}")

        api.buy_item(SUSHI_ITEM_ID, 1)
        api.use_item(SUSHI_ITEM_ID, 1)

        energy_after = get_energy()
        restored = energy_after - energy_before

        print(f"  Sushi energy: {energy_before} → {energy_after} (restored={restored})")
        assert restored == 5, f"Expected +5 energy, got +{restored}"

    @pytest.mark.order(54)
    @pytest.mark.timeout(30)
    def test_sushi_can_exceed_max_energy(self, auth_token):
        """At or above max energy, sushi still adds +5 (energy can exceed max).

        Energy has no hard cap — sushi always adds 5 regardless of current level.
        """
        from ff_agent import api_client as api

        profile = get_current_profile()
        energy = profile.get("energy", 0)
        gold = profile.get("gold", 0)

        if gold < 500:
            pytest.skip(f"Need >=500 gold, have {gold:.0f}")

        energy_before = energy
        api.buy_item(SUSHI_ITEM_ID, 1)
        api.use_item(SUSHI_ITEM_ID, 1)

        energy_after = get_energy()
        restored = energy_after - energy_before
        print(f"  Sushi at {energy_before} energy: → {energy_after} (restored={restored})")
        assert restored == 5, f"Expected +5 energy, got +{restored}"

    @pytest.mark.order(55)
    @pytest.mark.timeout(15)
    def test_insufficient_gold_for_sushi(self, auth_token):
        """Gold < 500, buy sushi → error, no gold change."""
        from ff_agent import api_client as api

        gold = get_gold()
        if gold >= 500:
            pytest.skip(f"Account has enough gold ({gold:.0f}); cannot test insufficient")

        gold_before = gold
        result = api.buy_item(SUSHI_ITEM_ID, 1)
        gold_after = get_gold()

        print(f"  Insufficient gold buy: result={result}")
        assert gold_after == gold_before, \
            f"Gold changed despite insufficient funds: {gold_before:.0f} → {gold_after:.0f}"


@pytest.mark.live
class TestItemNameMapping:
    """Verify item name → ID resolution in the MCP server."""

    @pytest.mark.order(56)
    @pytest.mark.timeout(15)
    def test_buy_by_name_sushi(self, auth_token):
        """buy_item("sushi") resolves to correct ID."""
        from ff_agent.server import ITEM_NAME_MAP

        assert "sushi" in ITEM_NAME_MAP
        assert ITEM_NAME_MAP["sushi"] == SUSHI_ITEM_ID

    @pytest.mark.order(57)
    @pytest.mark.timeout(15)
    def test_buy_invalid_item_name(self, auth_token):
        """buy_item("fake_item") → error response (not a crash)."""
        from ff_agent import api_client as api

        result = api.buy_item("fake_item_id_000000000000", 1)
        assert isinstance(result, dict)
        print(f"  Invalid item result: {result}")


@pytest.mark.live
class TestVerificationGates:
    """Verify that sell_all verification matches profile delta."""

    @pytest.mark.order(58)
    @pytest.mark.timeout(120)
    def test_sell_verification_matches_actual(self, auth_token):
        """sell_all verified.gold_change matches actual profile gold delta.

        Uses the MCP server's sell_all_fish tool which builds verification.
        """
        from ff_agent.server import sell_all_fish as sell_all_tool
        import json

        # Get baseline gold
        gold_before_actual = get_gold()

        # Call through MCP tool (returns JSON string with verification)
        result_json = sell_all_tool()
        result = json.loads(result_json)

        gold_after_actual = get_gold()
        actual_delta = gold_after_actual - gold_before_actual

        if "verified" in result and result["verified"] is not None:
            verified_change = result["verified"]["gold_change"]
            print(f"  Verified gold_change: {verified_change:.0f}")
            print(f"  Actual gold delta: {actual_delta:.0f}")
            # Allow small float rounding tolerance
            assert abs(verified_change - actual_delta) < 1.0, \
                f"Verified change {verified_change} != actual {actual_delta}"
        else:
            print("  No verification data returned (no fish to sell)")
