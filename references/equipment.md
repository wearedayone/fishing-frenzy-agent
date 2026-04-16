# Equipment & Accessories Reference

## Feature Unlock Levels

| Feature | Level Required |
|---------|---------------|
| Accessories / Upgrades | 5 |
| 5x Fishing Multiplier | 5 |
| Cooking | 15 |
| Diving | 30 |
| 20x Fishing Multiplier | 30 |
| Cavern (New Zone) | 80 |

## Rods

There are two rod categories:

### Default Rod
- Every player can fish without a rod — no rod is required
- The default (no-rod) state has no special bonuses

### Shiny Rods (NFT)
- NFT rods give a **chance to catch shiny fish** (which are also NFTs and have real value)
- Rod durability decreases with use
- **Durability = 0 → rod breaks** and cannot be used anymore (player can still fish without it, but loses the shiny fish chance)
- Durability does NOT affect catch rate — it's binary (works or broken)
- **Repair shiny rods proactively** — don't let them reach 0

### Rod Decision Rules
1. At session start, check `get_inventory()` for equipped rod
2. If a shiny rod is equipped and durability is low → `repair_rod()` immediately
3. If multiple rods in inventory → equip the one with best shiny chance
4. If no rod → fishing still works, just no shiny fish chance

## Accessories (Upgrades)

**Unlocked at Level 5.** All 6 accessories unlock together — no individual level gates.

Call `get_accessories()` at session start. If you have unspent upgrade points, spend them.

### Accessory List

| # | Name | Effect | Description |
|---|------|--------|-------------|
| 1 | Rod Handle | Chance to skip energy cost on cast | Saves energy over many casts |
| 2 | Reel | Larger capture zone in fishing minigame | Higher catch rate (fewer escapes) |
| 3 | Icebox | % more gold per fish sold | Direct gold income boost |
| 4 | Fishing Manual | % more XP per catch | Faster leveling |
| 5 | Cutting Board | Chance to not consume bait | Stretches bait supply |
| 6 | Lucky Charm | Chance for random item drops from fishing | Free items (bait, sushi, etc.) |

### Upgrade Point Costs

Upgrade point costs **increase with level** — higher levels cost more points. The exact costs per level are available in the `effects` array from `get_accessories()`, where each level entry has a `pointsRequired` field.

The agent should check the actual `pointsRequired` before upgrading and consider whether a cheaper low-level upgrade on a secondary accessory is better than an expensive high-level upgrade on the primary.

### Max Level

Each accessory has a `maxLevel` (default 10). At max level, the MCP tool shows `next_upgrade_cost: "MAX"`.

### Upgrade Strategy

The upgrade priority depends on the agent's goals:

| Goal | Top Upgrades | Reasoning |
|------|-------------|-----------|
| Save energy (more casts) | Rod Handle | Skip energy cost = free casts |
| Maximize gold | Icebox | Direct % gold bonus on all sells |
| Maximize XP / level fast | Fishing Manual | % XP boost compounds over all catches |
| Reduce fish escapes | Reel | Larger capture zone = higher success rate |
| Stretch bait supply | Cutting Board | Important when using Mythic Bait (pity system) |
| Free items | Lucky Charm | Passive value from random drops |

The CONFIG.md `UPGRADE_ORDER` setting controls the priority. The agent should adapt this based on current situation (e.g. if holding Mythic Bait, prioritize Cutting Board).

## Pets

### Overview
- Pets are obtained from **limited-time events** (battle passes, seasonal events, guild competitions)
- 38 total pets documented across 4 rarity tiers
- Pets passively generate fish daily — **must be collected or they are wasted**

### Daily Fish Generation

| Pet Rarity | # of Pets | Daily Fish | Notes |
|-----------|-----------|------------|-------|
| Common | 4 | 2-4 fish | Basic fish types |
| Rare | 16 | 2-4 fish | Moderate variety |
| Epic | 6 | 2-4 fish | Better fish types |
| Legendary | 12 | 3-7 fish | Access to rare fish (Blue Lobster, Frog) + shiny variants at 0.03-0.4% |

### Pet Decision Rules
1. Call `collect_pet_fish()` at the **start of every session** — uncollected fish are lost
2. Each pet has a unique drop table with different fish species and rates
3. Legendary pets can generate Mythic fish (Blue Lobster, Frog) at <2% and shiny variants at very low rates
4. No pet leveling or evolution — pets are static once obtained

## Tools

### `get_inventory()`
Full inventory including rod condition, durability, and equipped rod.

### `equip_rod(rod_id)`
Equip a fishing rod (from inventory).

### `repair_rod(rod_id)`
Repair a damaged rod. Costs gold.

### `collect_pet_fish()`
Collect all accumulated fish from pets. **Do this daily or fish are lost.**

### `get_accessories()`
Get all accessories with current levels, effects, and available upgrade points.
- Response includes `effects` array with `pointsRequired` per level

### `upgrade_accessory(accessory_name)`
Upgrade an accessory by one level. Accepts name (e.g. "Rod Handle") or ID.
