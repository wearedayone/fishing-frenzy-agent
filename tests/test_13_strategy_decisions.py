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

    def test_risk_needs_1500_gold(self):
        """Risk threshold is 1000+500=1500."""
        config = STRATEGY_DEFAULTS["risk"]
        state = GameState(gold=1400, energy=0)
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

    def test_risk_auto_with_big_bait(self):
        config = STRATEGY_DEFAULTS["risk"]
        state = GameState(has_bait_big=True)
        assert get_fishing_range(state, config) == "long_range"

    def test_risk_no_big_bait_falls_to_medium(self):
        config = STRATEGY_DEFAULTS["risk"]
        state = GameState(has_bait_big=False, has_bait_medium=True)
        assert get_fishing_range(state, config) == "mid_range"

    def test_risk_no_bait_at_all_falls_to_short(self):
        config = STRATEGY_DEFAULTS["risk"]
        state = GameState(has_bait_big=False, has_bait_medium=False)
        assert get_fishing_range(state, config) == "short_range"

    def test_explicit_short_override(self):
        """Config can override auto with explicit range."""
        config = StrategyConfig(strategy="risk", fishing_strategy="short")
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

    def test_risk_first_upgrade_is_reel(self):
        config = STRATEGY_DEFAULTS["risk"]
        levels = {k: 0 for k in UPGRADE_PRIORITIES["risk"]}
        maxes = {k: 10 for k in levels}
        assert get_next_upgrade(config, levels, maxes) == "Reel"

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

    def test_unknown_risk_defaults_to_moderate(self):
        """Unknown dive_risk falls back to moderate preset (10)."""
        config = StrategyConfig(dive_risk="yolo", dive_max_picks=0)
        assert get_dive_max_picks(config) == 10


# ============================================================
# Boundary / Edge Case Tests
# ============================================================

class TestBoundaryValues:
    """Exact boundary conditions for all decision functions."""

    def test_sushi_exact_threshold_boundary(self):
        """Gold exactly at threshold + reserve should buy sushi."""
        config = STRATEGY_DEFAULTS["balanced"]
        threshold = config.sushi_buy_threshold + config.gold_reserve  # 2500
        state = GameState(gold=threshold, energy=0)
        assert should_buy_sushi(state, config) is True

    def test_sushi_one_below_threshold(self):
        """Gold one below threshold should not buy."""
        config = STRATEGY_DEFAULTS["balanced"]
        threshold = config.sushi_buy_threshold + config.gold_reserve
        state = GameState(gold=threshold - 1, energy=0)
        assert should_buy_sushi(state, config) is False

    def test_dive_exact_threshold_boundary(self):
        """Gold exactly at diving threshold + reserve should dive."""
        config = STRATEGY_DEFAULTS["balanced"]
        threshold = config.diving_gold_threshold + config.gold_reserve  # 3500
        state = GameState(level=30, gold=threshold)
        assert should_dive(state, config) is True

    def test_dive_one_below_threshold(self):
        """Gold one below diving threshold should not dive."""
        config = STRATEGY_DEFAULTS["balanced"]
        threshold = config.diving_gold_threshold + config.gold_reserve
        state = GameState(level=30, gold=threshold - 1)
        assert should_dive(state, config) is False

    def test_dive_level_exactly_30(self):
        """Level exactly 30 with enough gold should dive."""
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(level=30, gold=10000)
        assert should_dive(state, config) is True

    def test_dive_level_29_cannot_dive(self):
        """Level 29 should not dive even with plenty of gold."""
        config = STRATEGY_DEFAULTS["balanced"]
        state = GameState(level=29, gold=100000)
        assert should_dive(state, config) is False

    def test_sushi_session_cap_at_limit(self):
        """Exactly at session cap should not buy."""
        config = StrategyConfig(max_sushi_per_session=5)
        state = GameState(gold=10000, energy=0, sushi_bought_this_session=5)
        assert should_buy_sushi(state, config) is False

    def test_sushi_session_cap_one_below(self):
        """One below session cap should buy."""
        config = StrategyConfig(max_sushi_per_session=5, sushi_buy_threshold=500, gold_reserve=0)
        state = GameState(gold=10000, energy=0, sushi_bought_this_session=4)
        assert should_buy_sushi(state, config) is True


class TestDisposalPriority:
    """Verify the priority ordering of fish disposal decisions."""

    def test_cook_beats_collect(self):
        """When both recipe match and near milestone, cook wins."""
        config = StrategyConfig(cook_before_sell=True)
        state = GameState(has_recipe_match=True, has_fish_near_milestone=True)
        assert get_fish_disposal_action(state, config) == Action.COOK

    def test_collect_beats_sell(self):
        """When near milestone but no recipe, collect wins over sell."""
        config = StrategyConfig(cook_before_sell=True, fish_disposal="sell_all")
        state = GameState(has_recipe_match=False, has_fish_near_milestone=True)
        assert get_fish_disposal_action(state, config) == Action.COLLECT

    def test_hold_ignores_recipe_when_cook_disabled(self):
        """Hold config with cook_before_sell=False should hold even with recipe match."""
        config = StrategyConfig(cook_before_sell=False, fish_disposal="hold")
        state = GameState(has_recipe_match=True, has_fish_near_milestone=False)
        assert get_fish_disposal_action(state, config) == Action.HOLD

    def test_hold_with_near_milestone_collects(self):
        """Near milestone takes priority over hold."""
        config = StrategyConfig(cook_before_sell=False, fish_disposal="hold")
        state = GameState(has_recipe_match=False, has_fish_near_milestone=True)
        assert get_fish_disposal_action(state, config) == Action.COLLECT


class TestUpgradeEdgeCases:
    """Edge cases for upgrade priority logic."""

    def test_missing_accessory_in_levels(self):
        """Accessory not in current_levels defaults to level 0."""
        config = STRATEGY_DEFAULTS["balanced"]
        levels = {}  # no levels at all
        maxes = {k: 10 for k in UPGRADE_PRIORITIES["balanced"]}
        result = get_next_upgrade(config, levels, maxes)
        # Should return the first in balanced priority since all are at level 0
        assert result == "Rod Handle"

    def test_partial_maxed_skips_correctly(self):
        """First two in balanced priority are maxed; picks third."""
        config = STRATEGY_DEFAULTS["balanced"]
        order = UPGRADE_PRIORITIES["balanced"]
        levels = {name: (10 if i < 2 else 0) for i, name in enumerate(order)}
        maxes = {k: 10 for k in order}
        # First two (Rod Handle, Icebox) maxed, should pick Reel
        assert get_next_upgrade(config, levels, maxes) == order[2]

    def test_custom_order_with_unknown_name(self):
        """Custom order with a name not in levels skips gracefully."""
        config = StrategyConfig(upgrade_order="Nonexistent, Reel, Icebox")
        levels = {"Reel": 0, "Icebox": 0}
        maxes = {"Reel": 10, "Icebox": 10}
        # "Nonexistent" has current=0, max=10 by default, but max_levels.get
        # returns 10 as default, so current(0) < max(10) => picks "Nonexistent"
        # Actually: current_levels.get("Nonexistent", 0)=0, max_levels.get("Nonexistent", 10)=10
        # So it returns "Nonexistent" since 0 < 10
        result = get_next_upgrade(config, levels, maxes)
        assert result == "Nonexistent"

    def test_custom_order_all_maxed_or_missing(self):
        """Custom order where listed items are maxed returns None."""
        config = StrategyConfig(upgrade_order="Reel, Icebox")
        levels = {"Reel": 10, "Icebox": 10}
        maxes = {"Reel": 10, "Icebox": 10}
        assert get_next_upgrade(config, levels, maxes) is None


class TestFishingRangeEdgeCases:
    """Edge cases for fishing range selection."""

    def test_unknown_strategy_defaults_to_short(self):
        """Unknown strategy name in auto mode falls back to short."""
        config = StrategyConfig(strategy="turbo", fishing_strategy="auto")
        state = GameState()
        assert get_fishing_range(state, config) == "short_range"

    def test_explicit_medium_with_bait(self):
        """Explicit medium with medium bait uses mid_range."""
        config = StrategyConfig(fishing_strategy="medium")
        state = GameState(has_bait_medium=True)
        assert get_fishing_range(state, config) == "mid_range"

    def test_explicit_medium_no_bait_falls_to_short(self):
        """Explicit medium without bait falls to short."""
        config = StrategyConfig(fishing_strategy="medium")
        state = GameState(has_bait_medium=False)
        assert get_fishing_range(state, config) == "short_range"

    def test_explicit_long_with_big_bait_only(self):
        """Explicit long with big bait (no medium) stays long."""
        config = StrategyConfig(fishing_strategy="long")
        state = GameState(has_bait_big=True, has_bait_medium=False)
        assert get_fishing_range(state, config) == "long_range"


class TestStrategyDefaults:
    """Verify strategy templates have expected structure."""

    def test_all_three_strategies_exist(self):
        """grind, balanced, and risk all defined."""
        assert "grind" in STRATEGY_DEFAULTS
        assert "balanced" in STRATEGY_DEFAULTS
        assert "risk" in STRATEGY_DEFAULTS

    def test_all_strategies_have_matching_upgrade_priorities(self):
        """Each strategy has an upgrade priority list."""
        for name in STRATEGY_DEFAULTS:
            assert name in UPGRADE_PRIORITIES, f"Missing upgrade priority for {name}"
            assert len(UPGRADE_PRIORITIES[name]) == 6, f"Expected 6 accessories for {name}"

    def test_grind_is_most_aggressive_on_sushi(self):
        """Grind has the lowest sushi threshold."""
        grind = STRATEGY_DEFAULTS["grind"]
        balanced = STRATEGY_DEFAULTS["balanced"]
        assert grind.sushi_buy_threshold < balanced.sushi_buy_threshold

    def test_grind_has_unlimited_sushi(self):
        """Grind max_sushi_per_session is 0 (unlimited)."""
        assert STRATEGY_DEFAULTS["grind"].max_sushi_per_session == 0

    def test_risk_has_aggressive_diving(self):
        """Risk strategy uses aggressive dive risk."""
        assert STRATEGY_DEFAULTS["risk"].dive_risk == "aggressive"

    def test_balanced_cooks_before_sell(self):
        """Balanced strategy cooks before selling."""
        assert STRATEGY_DEFAULTS["balanced"].cook_before_sell is True

    def test_grind_skips_cooking(self):
        """Grind strategy does not cook before selling."""
        assert STRATEGY_DEFAULTS["grind"].cook_before_sell is False


class TestGameStateDefaults:
    """Verify GameState default construction."""

    def test_default_state_has_zero_gold(self):
        state = GameState()
        assert state.gold == 0

    def test_default_state_has_zero_energy(self):
        state = GameState()
        assert state.energy == 0

    def test_default_state_level_1(self):
        state = GameState()
        assert state.level == 1

    def test_default_no_bait(self):
        state = GameState()
        assert state.has_bait_medium is False
        assert state.has_bait_big is False

    def test_default_no_recipe_match(self):
        state = GameState()
        assert state.has_recipe_match is False
        assert state.has_fish_near_milestone is False

    def test_default_zero_sushi_bought(self):
        state = GameState()
        assert state.sushi_bought_this_session == 0
