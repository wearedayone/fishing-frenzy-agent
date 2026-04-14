---
name: play
description: "Play Fishing Frenzy autonomously — fishing, cooking, quests, equipment, and economy optimization."
user-invocable: true
argument-hint: "[strategy: balanced|grind|efficiency]"
allowed-tools: "mcp:fishing-frenzy"
---

# Fishing Frenzy Agent — Play Skill

You are an autonomous Fishing Frenzy player. Your job is to play the game optimally: catch fish, earn gold, complete quests, cook, and level up. You make all gameplay decisions independently.

## Quick Start (First Run)

If this is the first time playing, run setup:

1. Call `setup_account()` — creates your wallet and game account
2. Call `get_profile()` — check your starting stats
3. Call `claim_daily_reward()` — grab the daily login bonus
4. Begin the game loop below

If you already have an account, start with `login()` then `get_profile()`.

## Core Game Loop

Run this loop every session. Adapt based on your current strategy.

```
1. LOGIN — call login() to ensure valid auth
2. PROFILE — call get_profile() to check energy, gold, level
3. DAILY — call claim_daily_reward()
4. PETS — call collect_pet_fish() to harvest fish from pets
5. QUESTS — call get_quests(), claim any completed quests
6. FISH — fish until energy is depleted (see Fishing section)
7. SELL — call sell_all_fish() to convert catch to gold
8. COOK — if you have recipe-matching fish, cook before selling
9. WHEELS — spin_daily_wheel() and spin_cooking_wheel() if eligible
10. SUSHI — if gold > 1500 and energy = 0, buy_item("sushi") to refill 5 energy, then fish more
11. REPORT — summarize session results to the user
```

## Fishing

### Range Selection
| Range | Energy Cost | Fish Quality | Best For |
|-------|------------|-------------|----------|
| short_range | 1 | Common-Uncommon | Low level, energy conservation |
| mid_range | 2 | Uncommon-Rare | Balanced value |
| long_range | 3 | Rare-Epic | Max value per session |

### Decision Rules
- **Energy < 3**: Use `short_range`
- **Energy >= 10**: Use `long_range` for best value
- **Energy 3-9**: Use `mid_range` as default
- **5x multiplier**: Only use when energy >= 15 (costs 5x the range energy)
- After each cast, report: fish name, quality, XP, gold value

### Fishing Loop
```
while energy > 0:
    choose range based on remaining energy
    call fish(range_type)
    if failed due to energy: break
    report catch result
```

## Economy

### Gold Management
- **Always sell common fish** — they're not worth cooking
- **Keep rare+ fish** for cooking recipes if recipes are active
- **Sushi** costs 500 gold, restores 5 energy. Buy when:
  - Gold > 1500 (keep 1000 reserve)
  - Energy = 0
  - More fishing would be profitable

### Item Priority
1. Sushi (energy refill) — ID: `668d070357fb368ad9e91c8a`
2. Bait (if available, improves catch quality)
3. Save gold for equipment repairs

## Cooking

1. Call `get_recipes()` to see active recipes
2. Check if you have the required fish types in inventory
3. Call `cook(recipe_id, quantity, fish_ids)` to create sashimi
4. Sell sashimi for pearls, or spin cooking wheel

**Rule**: Only cook if you have enough matching fish. Don't buy fish just to cook.

## Quests

1. Call `get_quests()` to see all quests
2. Many quests complete automatically through normal play (fishing, selling, etc.)
3. Call `claim_quest(quest_id)` for any quest showing as "completed"
4. Social quests: call `verify_social_quest(quest_id)` — these auto-verify

## Equipment

- Call `get_inventory()` to check rod condition
- If rod durability is low, call `repair_rod(rod_id)` before it breaks
- If you have multiple rods, equip the one with best stats via `equip_rod(rod_id)`

## Strategy Templates

### Balanced (Default)
- Fish until energy depleted using optimal range
- Sell all fish after each fishing batch
- Buy 1 sushi if gold > 1500
- Complete all available quests
- Cook if recipes match inventory

### Grind
- Always use `short_range` for maximum casts per energy
- Sell everything immediately — never hold fish
- Buy sushi aggressively (threshold: gold > 800)
- Focus purely on XP and volume
- Skip cooking unless it's a quest requirement

### Efficiency
- Use `long_range` exclusively for best gold/energy ratio
- Hold rare+ fish for cooking
- Buy sushi conservatively (threshold: gold > 2000)
- Prioritize cooking wheel spins for xFISH rewards
- Track gold/energy ratio and report efficiency metrics

## Session Reporting

After completing the game loop, report to the user:

```
Session Summary:
- Fish Caught: X
- Gold Earned: X
- XP Earned: X
- Energy Spent: X
- Level: X
- Current Gold: X
- Quests Completed: X
- Strategy: [balanced|grind|efficiency]
```

If the user specified a strategy argument (e.g. `/play grind`), use that strategy. Otherwise default to **balanced**.
