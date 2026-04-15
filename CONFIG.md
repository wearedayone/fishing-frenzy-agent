# Agent Configuration

Edit these values to customize your agent's behavior. The agent reads this file at the start of each session.

## Strategy

```
STRATEGY: balanced
```

Options: `balanced`, `grind`, `efficiency`
(Can also be set per-session via `/play grind`)

## Economy Thresholds

```
SUSHI_BUY_THRESHOLD: 1500
GOLD_RESERVE: 1000
DIVING_GOLD_THRESHOLD: 2500
```

- `SUSHI_BUY_THRESHOLD`: Minimum gold before buying sushi
- `GOLD_RESERVE`: Gold to keep in reserve (never spend below this)
- `DIVING_GOLD_THRESHOLD`: Minimum gold before buying a diving ticket

## Fishing Preferences

```
PREFERRED_RANGE: auto
MAX_SUSHI_PER_SESSION: 3
USE_MULTIPLIER: false
```

- `PREFERRED_RANGE`: `auto` (smart selection), `short_range`, `mid_range`, or `long_range`
- `MAX_SUSHI_PER_SESSION`: Cap on sushi purchases per session (0 = unlimited)
- `USE_MULTIPLIER`: Set to `true` to enable 5x multiplier when energy is high

## Diving

```
DIVE_RISK: moderate
DIVE_MAX_PICKS: 10
```

- `DIVE_RISK`: `conservative` (5-8 picks), `moderate` (9-12), `aggressive` (13-15)
- `DIVE_MAX_PICKS`: Override exact number of picks (0 = use DIVE_RISK preset)

## Upgrade Priority

```
UPGRADE_ORDER: rod_handle, icebox, reel, fishing_manual, cutting_board, lucky_charm
```

Comma-separated list. The agent spends upgrade points in this order.

## Cooking

```
COOK_BEFORE_SELL: true
SPIN_COOKING_WHEEL: true
```

- `COOK_BEFORE_SELL`: Check recipes and cook matching fish before selling
- `SPIN_COOKING_WHEEL`: Spend pearls on cooking wheel after cooking
