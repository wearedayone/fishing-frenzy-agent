# Agent Configuration

Edit these values to customize your agent's behavior. The agent reads this file at the start of each session.

## Strategy

```
STRATEGY: balanced
```

Options: `balanced`, `grind`, `risk`
(Can also be set per-session via `/play-fishing-frenzy grind`)

## Economy Thresholds

```
SUSHI_BUY_THRESHOLD: 1500
GOLD_RESERVE: 1000
DIVING_GOLD_THRESHOLD: 2500
```

- `SUSHI_BUY_THRESHOLD`: Minimum gold before buying sushi
- `GOLD_RESERVE`: Gold to keep in reserve (never spend below this)
- `DIVING_GOLD_THRESHOLD`: Minimum gold before buying a diving ticket

## Fishing

```
FISHING_STRATEGY: auto
FISH_DISPOSAL: sell_all
MAX_SUSHI_PER_SESSION: 3
USE_MULTIPLIER: false
```

- `FISHING_STRATEGY`: Which range/bait pairing to use
  - `auto` — determined by the active strategy (Grind=Short, Balanced=Medium, Risk=Long)
  - `short` — short_range, no bait (1 energy/cast, max volume)
  - `medium` — mid_range + Medium Bait (2 energy/cast, epic-weighted drops)
  - `long` — long_range + Big Bait (3 energy/cast, legendary-weighted drops)
  - Falls back to Short if the required bait is not in inventory
- `FISH_DISPOSAL`: What to do with caught fish after cooking
  - `sell_all` — sell all remaining fish (default)
  - `hold` — keep fish in inventory, do not sell (for manual decisions)
  - Note: cooking always happens first (if `COOK_BEFORE_SELL=true`). Collecting for aquarium
    milestones is handled automatically. Fish disposal order:
    Cook (recipe matches) → Collect (near milestones) → Sell or Hold (remainder)
- `MAX_SUSHI_PER_SESSION`: Cap on sushi purchases per session (0 = unlimited)
- `USE_MULTIPLIER`: Set to `true` to enable 5x multiplier when energy is high

## Diving

```
DIVE_RISK: moderate
DIVE_MAX_PICKS: 0
```

- `DIVE_RISK`: `conservative` (5-8 picks), `moderate` (9-12), `aggressive` (13-15)
- `DIVE_MAX_PICKS`: Override exact number of picks (0 = use DIVE_RISK preset)

## Upgrade Priority

```
UPGRADE_ORDER: auto
```

Options:
- `auto` — the agent picks upgrade order based on the active strategy (see SKILL.md strategy templates)
- Comma-separated list to override, e.g. `icebox, rod_handle, reel, fishing_manual, cutting_board, lucky_charm`

When `auto`, the agent adapts upgrades to its goals:
- Selling a lot → **Icebox** (% gold bonus on all sells)
- Leveling fast → **Fishing Manual** (% XP boost)
- Using bait → **Cutting Board** (chance to not consume bait)
- Catching more fish → **Reel** (larger capture zone, fewer escapes)
- Conserving energy → **Rod Handle** (chance to skip energy cost)
- Passive value → **Lucky Charm** (random item drops)

## Cooking

```
COOK_BEFORE_SELL: true
SPIN_COOKING_WHEEL: true
```

- `COOK_BEFORE_SELL`: Check recipes and cook matching fish before selling
- `SPIN_COOKING_WHEEL`: Spend pearls on cooking wheel after cooking

## Notifications

```
RON_REMINDER: true
```

- `RON_REMINDER`: Show the RON deposit reminder at session start when wallet has 0 RON balance. Set to `false` to dismiss permanently.
