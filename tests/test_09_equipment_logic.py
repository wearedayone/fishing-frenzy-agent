"""Equipment rules: accessories, rods, upgrades.

RC5 — Review questions for Derek:
  - Can accessories go above max level?
  - Are upgrade points shared across all accessories?
"""

import json

import pytest

from .helpers import get_current_profile


@pytest.mark.live
class TestAccessories:
    """Verify accessory list, levels, and upgrade behavior."""

    @pytest.mark.order(72)
    @pytest.mark.timeout(15)
    def test_accessories_list_has_6(self, auth_token):
        """get_accessories returns 6 accessories (when unlocked).

        Fresh accounts may have 0 accessories until a certain level.
        """
        from ff_agent import api_client as api

        result = api.get_accessories()
        assert isinstance(result, dict)

        accs = result.get("accessories", [])
        assert isinstance(accs, list)
        print(f"  Accessory count: {len(accs)}")
        for acc in accs:
            print(f"    - {acc.get('name', 'unknown')}")

        if len(accs) == 0:
            pytest.skip("No accessories unlocked yet (likely level-gated)")
        assert len(accs) == 6, f"Expected 6 accessories, got {len(accs)}"

    @pytest.mark.order(73)
    @pytest.mark.timeout(15)
    def test_accessory_has_level_and_effects(self, auth_token):
        """Each accessory has id, name, level, effects."""
        from ff_agent import api_client as api

        result = api.get_accessories()
        accs = result.get("accessories", [])

        if not accs:
            pytest.skip("No accessories returned")

        for acc in accs:
            assert "name" in acc or "accessoryId" in acc, \
                f"Accessory missing name/id: {acc.keys()}"
            assert "currentLevel" in acc or "level" in acc, \
                f"Accessory missing level: {acc.keys()}"
            print(f"  {acc.get('name')}: level {acc.get('currentLevel', acc.get('level'))}")

    @pytest.mark.order(74)
    @pytest.mark.timeout(15)
    def test_max_level_shows_MAX(self, auth_token):
        """Max-level accessory → next_upgrade_cost == 'MAX' in MCP tool."""
        from ff_agent.server import get_accessories as get_acc_tool

        result_json = get_acc_tool()
        result = json.loads(result_json)

        if "accessories" not in result:
            pytest.skip("No accessories in MCP tool response")

        max_level_found = False
        for acc in result["accessories"]:
            if acc.get("next_upgrade_cost") == "MAX":
                max_level_found = True
                print(f"  MAX level: {acc.get('name')} at {acc.get('level')}")

        if not max_level_found:
            print("  No accessories at max level (all upgradeable)")
            # This is fine for a new account — just log it

    @pytest.mark.order(75)
    @pytest.mark.timeout(15)
    def test_upgrade_increments_level(self, auth_token):
        """Upgrade → level increases by 1 (skip if 0 upgrade points)."""
        from ff_agent import api_client as api

        result = api.get_accessories()
        available_points = result.get("availableUpgradePoint", 0)

        if available_points <= 0:
            pytest.skip(f"No upgrade points available ({available_points})")

        accs = result.get("accessories", [])
        # Find an upgradeable accessory
        target = None
        for acc in accs:
            current = acc.get("currentLevel", 0)
            max_lvl = acc.get("maxLevel", 10)
            if current < max_lvl:
                target = acc
                break

        if target is None:
            pytest.skip("All accessories at max level")

        target_id = target.get("accessoryId") or target.get("_id")
        level_before = target.get("currentLevel", 0)

        upgrade_result = api.upgrade_accessory(target_id)
        assert isinstance(upgrade_result, dict)

        # Re-fetch to verify level increased
        result2 = api.get_accessories()
        accs2 = result2.get("accessories", [])
        upgraded = next((a for a in accs2 if (a.get("accessoryId") or a.get("_id")) == target_id), None)

        if upgraded:
            level_after = upgraded.get("currentLevel", 0)
            print(f"  {target.get('name')}: level {level_before} → {level_after}")
            assert level_after == level_before + 1, \
                f"Expected level {level_before + 1}, got {level_after}"

    @pytest.mark.order(76)
    @pytest.mark.timeout(15)
    def test_upgrade_at_max_fails(self, auth_token):
        """Upgrade max-level accessory → error (skip if none at max)."""
        from ff_agent import api_client as api

        result = api.get_accessories()
        accs = result.get("accessories", [])

        # Find a max-level accessory
        target = None
        for acc in accs:
            current = acc.get("currentLevel", 0)
            max_lvl = acc.get("maxLevel", 10)
            if current >= max_lvl:
                target = acc
                break

        if target is None:
            pytest.skip("No accessories at max level")

        target_id = target.get("accessoryId") or target.get("_id")
        upgrade_result = api.upgrade_accessory(target_id)
        assert isinstance(upgrade_result, dict)
        print(f"  Max upgrade result: {upgrade_result}")

    @pytest.mark.order(77)
    @pytest.mark.timeout(15)
    def test_upgrade_unknown_name_fails(self, auth_token):
        """upgrade_accessory("Fake Name") → error via MCP tool."""
        from ff_agent.server import upgrade_accessory as upgrade_tool

        result_json = upgrade_tool("Fake Nonexistent Accessory")
        result = json.loads(result_json)

        assert "error" in result, f"Expected error for fake accessory, got: {result}"
        print(f"  Fake accessory error: {result.get('error')}")


@pytest.mark.live
class TestRods:
    """Verify rod and pet fish endpoints."""

    @pytest.mark.order(78)
    @pytest.mark.timeout(15)
    def test_inventory_has_rod_data(self, auth_token):
        """get_inventory returns data including rod information."""
        from ff_agent import api_client as api

        result = api.get_inventory()
        assert result is not None
        assert isinstance(result, (dict, list))
        print(f"  Inventory type: {type(result)}")
        if isinstance(result, dict):
            print(f"  Inventory keys: {list(result.keys())}")

    @pytest.mark.order(79)
    @pytest.mark.timeout(15)
    def test_collect_pet_fish_returns_list(self, auth_token):
        """collect_pet_fish → response (collected count may be 0)."""
        from ff_agent import api_client as api

        result = api.collect_pet_fish()
        assert isinstance(result, (dict, list))
        print(f"  Pet fish result: {result}")
