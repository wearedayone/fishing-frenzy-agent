# Fishing Reference

## Ranges

| Range | Energy | Fish Quality | Best For |
|-------|--------|-------------|----------|
| `short_range` | 1 | Common-Uncommon | Low level, energy conservation |
| `mid_range` | 2 | Uncommon-Rare | Balanced value |
| `long_range` | 3 | Rare-Epic | Max value per session |

## Range Decision Rules

- **Energy < 3**: Use `short_range`
- **Energy >= 10**: Use `long_range` for best value
- **Energy 3-9**: Use `mid_range` as default
- **5x multiplier**: Only use when energy >= 15 (costs 5x the range energy)

## Tools

### `fish(range_type, multiplier)`
Execute one fishing session.
- `range_type`: `"short_range"`, `"mid_range"`, or `"long_range"`
- `multiplier`: 1 (normal) or higher for multiplied rewards
- Returns: fish caught, XP gained, gold value, energy remaining

### `fish_batch(range_type, count, multiplier)`
Fish multiple times in sequence. Stops if energy runs out.
- `count`: Number of sessions to attempt
- Returns: summary with total caught, XP, gold, successes/failures, and individual results

## Fishing Loop

Use `fish_batch()` for efficiency (handles cooldowns automatically). After each batch:
1. Display results cast-by-cast from the results array
2. Display updated dashboard
3. Check if energy allows another batch
4. If energy depleted, move to sell phase
