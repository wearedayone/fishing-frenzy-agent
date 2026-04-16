"""Pure strategy decision tests — zero network, zero I/O.

Tests all 6 decision functions across the 3 strategy templates.
"""

import pytest

from ff_agent.strategy import (
    Action,
    GameState,
    StrategyConfig,
    STRATEGY_DEFAULTS,
    UPGRADE_PRIORITIES,
    should_buy_sushi,
    should_dive,
    get_fishing_range,
    get_fish_disposal_action,
    get_next_upgrade,
    get_dive_max_picks,
)


# ============================================================
# Sushi Decisions
# ============================================================

class TestSushiDecision:
    """Sushi buying at different gold/energy/strategy combos."""

    def test_grind_buys_sushi_at_threshold(self):
        """Grind strategy buys sushi at 800+500 reserve = 1300 gold."""
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(gold=1400, energy=0)
        assert should_buy_sushi(state, config) is True

    def test_grind_skips_below_threshold(self):
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(gold=1200, energy=0)
        assert should_buy_sushi(state, config) is False

    def test_balanced_skips_at_900_gold(self):
        """Balanced threshold is 1500+1000=2500, so 900 gold → skip."""
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(gold=900, energy=0)
        assert should_buy_sushi(state, config) is False

    def test_balanced_buys_at_high_gold(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(gold=2600, energy=0)
        assert should_buy_sushi(state, config) is True

    def test_efficiency_needs_3000_gold(self):
        """Efficiency threshold is 2000+1000=3000."""
        config = STRATEGY_DEFAULTS["efficiency"]
        state = GameState(gold=2800, energy=0)
        assert should_buy_sushi(state, config) is False

    def test_skips_when_energy_positive(self):
        """Never buy sushi if energy > 0."""
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(gold=5000, energy=1)
        assert should_buy_sushi(state, config) is False

    def test_respects_session_cap(self):
        """Balanced caps at 3 sushi per session."""
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(gold=5000, energy=0, sushi_bought_this_session=3)
        assert should_buy_sushi(state, config) is False

    def test_grind_unlimited_sushi(self):
        """Grind has max_sushi=0 (unlimited)."""
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(gold=5000, energy=0, sushi_bought_this_session=10)
        assert should_buy_sushi(state, config) is True


# ============================================================
# Diving Decisions
# ============================================================

class TestDivingDecision:
    """Level gate, gold threshold, gold reserve."""

    def test_level_25_cannot_dive(self):
        state = GameState(level=25, gold=10000)
        config = STRATEGY_DEFAULTS["balanced"]
        assert should_dive(state, config) is False

    def test_level_30_sufficient_gold(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(level=30, gold=4000)  # 2500+1000=3500, 4000 ok
        assert should_dive(state, config) is True

    def test_level_30_insufficient_gold(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(level=30, gold=3000)  # below 3500
        assert should_dive(state, config) is False

    def test_grind_lower_reserve(self):
        """Grind has 500 reserve → needs 2500+500=3000."""
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(level=35, gold=3100)
        assert should_dive(state, config) is True


# ============================================================
# Fishing Range
# ============================================================

class TestFishingRange:
    """Range selection per strategy, bait fallback, auto mode."""

    def test_grind_auto_selects_short(self):
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState()
        assert get_fishing_range(state, config) == "short_range"

    def test_balanced_auto_with_bait_selects_mid(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(has_bait_medium=True)
        assert get_fishing_range(state, config) == "mid_range"

    def test_balanced_auto_no_bait_falls_back_short(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(has_bait_medium=False)
        assert get_fishing_range(state, config) == "short_range"

    def test_efficiency_auto_with_big_bait(self):
        config = STRATEGY_DEFAULTS["efficiency"]
        state = GameState(has_bait_big=True)
        assert get_fishing_range(state, config) == "long_range"

    def test_efficiency_no_big_bait_falls_to_medium(self):
        config = STRATEGY_DEFAULTS["efficiency"]
        state = GameState(has_bait_big=False, has_bait_medium=True)
        assert get_fishing_range(state, config) == "mid_range"

    def test_efficiency_no_bait_at_all_falls_to_short(self):
        config = STRATEGY_DEFAULTS["efficiency"]
        state = GameState(has_bait_big=False, has_bait_medium=False)
        assert get_fishing_range(state, config) == "short_range"

    def test_explicit_short_override(self):
        """Config can override auto with explicit range."""
        config = StrategyConfig(strategy="efficiency", fishing_strategy="short")
        state = GameState(has_bait_big=True)
        assert get_fishing_range(state, config) == "short_range"

    def test_explicit_long_no_bait_falls_back(self):
        config = StrategyConfig(fishing_strategy="long")
        state = GameState(has_bait_big=False, has_bait_medium=False)
        assert get_fishing_range(state, config) == "short_range"


# ============================================================
# Fish Disposal
# ============================================================

class TestFishDisposal:
    """Cook vs sell vs collect vs hold per strategy."""

    def test_cook_when_recipe_match(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(has_recipe_match=True)
        assert get_fish_disposal_action(state, config) == Action.COOK

    def test_grind_skips_cooking(self):
        """Grind has cook_before_sell=False."""
        config = STRATEGY_DEFAULTS["grind"]
        state = GameState(has_recipe_match=True)
        assert get_fish_disposal_action(state, config) == Action.SELL

    def test_collect_near_milestone(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(has_recipe_match=False, has_fish_near_milestone=True)
        assert get_fish_disposal_action(state, config) == Action.COLLECT

    def test_default_sell(self):
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState()
        assert get_fish_disposal_action(state, config) == Action.SELL

    def test_hold_config(self):
        config = StrategyConfig(fish_disposal="hold")
        state = GameState()
        assert get_fish_disposal_action(state, config) == Action.HOLD


# ============================================================
# Upgrade Priority
# ============================================================

class TestUpgradePriority:
    """First upgrade per strategy, max skip, custom order."""

    def test_grind_first_upgrade_is_fishing_manual(self):
        config = STRATEGY_DEFAULTS["grind"]
        levels = {"Fishing Manual": 0, "Rod Handle": 0, "Reel": 0,
                  "Icebox": 0, "Lucky Charm": 0, "Cutting Board": 0}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Fishing Manual"

    def test_balanced_first_upgrade_is_rod_handle(self):
        config = STRATEGY_DEFAULTS["balanced"]
        levels = {k: 0 for k in UPGRADE_PRIORITIES["balanced"]}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Rod Handle"

    def test_efficiency_first_upgrade_is_icebox(self):
        config = STRATEGY_DEFAULTS["efficiency"]
        levels = {k: 0 for k in UPGRADE_PRIORITIES["efficiency"]}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Icebox"

    def test_skips_maxed_accessory(self):
        config = STRATEGY_DEFAULTS["grind"]
        levels = {"Fishing Manual": 10, "Rod Handle": 0, "Reel": 0,
                  "Icebox": 0, "Lucky Charm": 0, "Cutting Board": 0}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Rod Handle"

    def test_all_maxed_returns_none(self):
        config = STRATEGY_DEFAULTS["balanced"]
        levels = {k: 10 for k in UPGRADE_PRIORITIES["balanced"]}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) is None

    def test_custom_upgrade_order(self):
        config = StrategyConfig(upgrade_order="Reel, Icebox, Rod Handle")
        levels = {"Reel": 0, "Icebox": 0, "Rod Handle": 0}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Reel"


# ============================================================
# Dive Pick Count
# ============================================================

class TestDivePickCount:
    """Risk presets and explicit override."""

    def test_conservative_preset(self):
        config = StrategyConfig(dive_risk="conservative", dive_max_picks=0)
        assert get_dive_max_picks(config) == 7

    def test_moderate_preset(self):
        config = StrategyConfig(dive_risk="moderate", dive_max_picks=0)
        assert get_dive_max_picks(config) == 10

    def test_aggressive_preset(self):
        config = StrategyConfig(dive_risk="aggressive", dive_max_picks=0)
        assert get_dive_max_picks(config) == 14

    def test_explicit_override(self):
        config = StrategyConfig(dive_risk="conservative", dive_max_picks=12)
        assert get_dive_max_picks(config) == 12
