"""Pure decision-logic for Fishing Frenzy strategies.

All functions are pure (no I/O, no network calls) — they take game state in
and return decisions out. This makes them fully testable without mocking.
"""

from dataclasses import dataclass, field
from enum import Enum


class Action(Enum):
    SELL = "sell"
    COOK = "cook"
    COLLECT = "collect"
    HOLD = "hold"


@dataclass
class GameState:
    """Snapshot of current game state relevant to decision-making."""
    gold: float = 0
    energy: int = 0
    max_energy: int = 30
    level: int = 1
    karma: int = 0
    # Inventory flags
    has_bait_medium: bool = False
    has_bait_big: bool = False
    has_recipe_match: bool = False
    has_fish_near_milestone: bool = False
    # Session tracking
    sushi_bought_this_session: int = 0


@dataclass
class StrategyConfig:
    """Configuration knobs that differ per strategy. Maps to CONFIG.md values."""
    strategy: str = "balanced"
    sushi_buy_threshold: float = 1500
    gold_reserve: float = 1000
    diving_gold_threshold: float = 2500
    fishing_strategy: str = "auto"  # auto, short, medium, long
    fish_disposal: str = "sell_all"  # sell_all, hold
    max_sushi_per_session: int = 3
    use_multiplier: bool = False
    dive_risk: str = "moderate"  # conservative, moderate, aggressive
    dive_max_picks: int = 0  # 0 = use dive_risk preset
    upgrade_order: str = "auto"
    cook_before_sell: bool = True
    spin_cooking_wheel: bool = True


# Strategy templates from SKILL.md
STRATEGY_DEFAULTS: dict[str, StrategyConfig] = {
    "grind": StrategyConfig(
        strategy="grind",
        sushi_buy_threshold=800,
        gold_reserve=500,
        diving_gold_threshold=2500,
        fishing_strategy="auto",
        fish_disposal="sell_all",
        max_sushi_per_session=0,  # unlimited
        cook_before_sell=False,
        dive_risk="moderate",
        upgrade_order="auto",
    ),
    "balanced": StrategyConfig(
        strategy="balanced",
        sushi_buy_threshold=1500,
        gold_reserve=1000,
        diving_gold_threshold=2500,
        fishing_strategy="auto",
        fish_disposal="sell_all",
        max_sushi_per_session=3,
        cook_before_sell=True,
        dive_risk="moderate",
        upgrade_order="auto",
    ),
    "efficiency": StrategyConfig(
        strategy="efficiency",
        sushi_buy_threshold=2000,
        gold_reserve=1000,
        diving_gold_threshold=2500,
        fishing_strategy="auto",
        fish_disposal="sell_all",
        max_sushi_per_session=2,
        cook_before_sell=True,
        dive_risk="conservative",
        upgrade_order="auto",
    ),
}

# Upgrade priority per strategy (when upgrade_order == "auto")
UPGRADE_PRIORITIES: dict[str, list[str]] = {
    "grind": [
        "Fishing Manual", "Rod Handle", "Reel",
        "Icebox", "Lucky Charm", "Cutting Board",
    ],
    "balanced": [
        "Rod Handle", "Icebox", "Reel",
        "Fishing Manual", "Cutting Board", "Lucky Charm",
    ],
    "efficiency": [
        "Icebox", "Rod Handle", "Cutting Board",
        "Reel", "Fishing Manual", "Lucky Charm",
    ],
}


def should_buy_sushi(state: GameState, config: StrategyConfig) -> bool:
    """Decide whether to buy sushi (500 gold → +5 energy).

    Returns True if:
    - Player has 0 energy
    - Gold exceeds the strategy's sushi threshold + gold reserve
    - Session sushi cap not exceeded (0 = unlimited)
    """
    if state.energy > 0:
        return False

    effective_threshold = config.sushi_buy_threshold + config.gold_reserve
    if state.gold < effective_threshold:
        return False

    if config.max_sushi_per_session > 0 and state.sushi_bought_this_session >= config.max_sushi_per_session:
        return False

    return True


def should_dive(state: GameState, config: StrategyConfig) -> bool:
    """Decide whether to do a diving session.

    Requirements:
    - Level >= 30
    - Gold >= diving_gold_threshold + gold_reserve
    """
    if state.level < 30:
        return False

    if state.gold < config.diving_gold_threshold + config.gold_reserve:
        return False

    return True


def get_fishing_range(state: GameState, config: StrategyConfig) -> str:
    """Determine which fishing range to use.

    When fishing_strategy is 'auto', maps from the strategy name.
    Falls back to shorter range if required bait isn't available.
    """
    if config.fishing_strategy != "auto":
        desired = config.fishing_strategy
    else:
        # Auto: map strategy → range
        strategy_range_map = {
            "grind": "short",
            "balanced": "medium",
            "efficiency": "long",
        }
        desired = strategy_range_map.get(config.strategy, "short")

    # Check bait availability and fall back
    if desired == "long":
        if not state.has_bait_big:
            desired = "medium"
    if desired == "medium":
        if not state.has_bait_medium:
            desired = "short"

    range_map = {
        "short": "short_range",
        "medium": "mid_range",
        "long": "long_range",
    }
    return range_map.get(desired, "short_range")


def get_fish_disposal_action(state: GameState, config: StrategyConfig) -> Action:
    """Determine what to do with fish after catching.

    Order: Cook (if recipe match + cook_before_sell) → Collect (near milestones)
           → Sell or Hold based on config.
    """
    if config.cook_before_sell and state.has_recipe_match:
        return Action.COOK

    if state.has_fish_near_milestone:
        return Action.COLLECT

    if config.fish_disposal == "hold":
        return Action.HOLD

    return Action.SELL


def get_next_upgrade(
    config: StrategyConfig,
    current_levels: dict[str, int],
    max_levels: dict[str, int],
) -> str | None:
    """Pick the next accessory to upgrade based on strategy priority.

    Args:
        config: Strategy configuration.
        current_levels: {"Fishing Manual": 3, "Rod Handle": 0, ...}
        max_levels: {"Fishing Manual": 10, ...}

    Returns the name of the next accessory to upgrade, or None if all maxed.
    """
    if config.upgrade_order != "auto":
        # Custom order: parse comma-separated list
        order = [s.strip() for s in config.upgrade_order.split(",")]
    else:
        order = UPGRADE_PRIORITIES.get(config.strategy, UPGRADE_PRIORITIES["balanced"])

    for name in order:
        current = current_levels.get(name, 0)
        maximum = max_levels.get(name, 10)
        if current < maximum:
            return name

    return None


def get_dive_max_picks(config: StrategyConfig) -> int:
    """Get the maximum number of cells to reveal during a dive.

    If dive_max_picks > 0, use that exact value.
    Otherwise map dive_risk to a preset range midpoint.
    """
    if config.dive_max_picks > 0:
        return config.dive_max_picks

    risk_picks = {
        "conservative": 7,   # midpoint of 5-8
        "moderate": 10,       # midpoint of 9-12
        "aggressive": 14,     # midpoint of 13-15
    }
    return risk_picks.get(config.dive_risk, 10)
