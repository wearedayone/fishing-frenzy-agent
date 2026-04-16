"""Strategy benchmark tests — verify strategies produce different behavior.

Simulates a full session's worth of decisions with each strategy and asserts
they diverge in expected ways.
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


def simulate_session(strategy_name: str) -> dict:
    """Simulate a session's worth of decisions for a given strategy.

    Returns a summary of all decisions made.
    """
    config = STRATEGY_DEFAULTS[strategy_name]

    # Starting state: fresh session, 30 energy, 5000 gold, level 35
    state = GameState(
        gold=5000,
        energy=30,
        max_energy=30,
        level=35,
        has_bait_medium=True,
        has_bait_big=True,
        has_recipe_match=True,
        has_fish_near_milestone=False,
    )

    decisions = {
        "strategy": strategy_name,
        "fishing_ranges": [],
        "sushi_decisions": [],
        "disposal_actions": [],
        "casts": 0,
        "total_energy_used": 0,
        "dive_decision": should_dive(state, config),
        "dive_picks": get_dive_max_picks(config),
        "first_upgrade": None,
    }

    # Determine upgrade priority
    levels = {k: 0 for k in UPGRADE_PRIORITIES.get(strategy_name, UPGRADE_PRIORITIES["balanced"])}
    maxes = {k: 10 for k in levels}
    decisions["first_upgrade"] = get_next_upgrade(config, levels, maxes)

    # Simulate fishing loop
    energy_per_cast = {"short_range": 1, "mid_range": 2, "long_range": 3}
    while state.energy > 0:
        fishing_range = get_fishing_range(state, config)
        cost = energy_per_cast.get(fishing_range, 1)
        if state.energy < cost:
            break

        decisions["fishing_ranges"].append(fishing_range)
        decisions["casts"] += 1
        decisions["total_energy_used"] += cost
        state.energy -= cost

        # After each cast, decide disposal
        disposal = get_fish_disposal_action(state, config)
        decisions["disposal_actions"].append(disposal)

    # After energy depleted, check sushi
    state.gold = 5000  # Reset gold for sushi check
    decisions["sushi_decisions"].append(should_buy_sushi(state, config))

    return decisions


class TestStrategyBenchmark:
    """Verify strategies produce verifiably different behavior."""

    @pytest.fixture(autouse=True)
    def _run_simulations(self):
        self.grind = simulate_session("grind")
        self.balanced = simulate_session("balanced")
        self.efficiency = simulate_session("efficiency")

    def test_grind_uses_short_range(self):
        """Grind always uses short_range."""
        assert all(r == "short_range" for r in self.grind["fishing_ranges"])

    def test_balanced_uses_mid_range(self):
        """Balanced uses mid_range (when bait available)."""
        assert all(r == "mid_range" for r in self.balanced["fishing_ranges"])

    def test_efficiency_uses_long_range(self):
        """Efficiency uses long_range (when bait available)."""
        assert all(r == "long_range" for r in self.efficiency["fishing_ranges"])

    def test_grind_casts_more_than_efficiency(self):
        """Grind (1 energy/cast) makes more casts than efficiency (3 energy/cast)."""
        assert self.grind["casts"] > self.efficiency["casts"]

    def test_different_first_upgrades(self):
        """Each strategy has a different first upgrade priority."""
        upgrades = {
            self.grind["first_upgrade"],
            self.balanced["first_upgrade"],
            self.efficiency["first_upgrade"],
        }
        assert len(upgrades) == 3, (
            f"Expected 3 different upgrades, got: "
            f"grind={self.grind['first_upgrade']}, "
            f"balanced={self.balanced['first_upgrade']}, "
            f"efficiency={self.efficiency['first_upgrade']}"
        )

    def test_grind_skips_cooking(self):
        """Grind has cook_before_sell=False, so disposal is SELL even with recipe match."""
        assert Action.COOK not in self.grind["disposal_actions"]
        assert Action.SELL in self.grind["disposal_actions"]

    def test_balanced_and_efficiency_cook(self):
        """Balanced and efficiency both cook when recipe matches."""
        assert Action.COOK in self.balanced["disposal_actions"]
        assert Action.COOK in self.efficiency["disposal_actions"]
