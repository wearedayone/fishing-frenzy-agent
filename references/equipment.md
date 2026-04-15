# Equipment & Accessories Reference

## Rods

- Check rod condition via `get_inventory()`
- Repair before durability reaches 0 — a broken rod can't fish
- If you have multiple rods, equip the one with best stats

## Accessories (Upgrades)

Call `get_accessories()` at session start. If you have unspent upgrade points, spend them.

### Accessory List

| # | Name | Effect | Priority |
|---|------|--------|----------|
| 1 | Rod Handle | Energy save chance (skip energy cost on cast) | Highest |
| 2 | Icebox | Gold bonus (% more gold per fish sold) | High |
| 3 | Reel | Larger capture zone (higher catch rate) | Medium |
| 4 | Fishing Manual | XP bonus (% more XP per catch) | Medium |
| 5 | Cutting Board | Bait save (chance to keep bait after use) | Low |
| 6 | Lucky Charm | Random item drops from fishing | Low |

### Strategy-Specific Priority

| Strategy | Top Upgrades |
|----------|-------------|
| Balanced | Even distribution |
| Grind | Fishing Manual, Rod Handle |
| Efficiency | Icebox, Rod Handle |

## Pets

Call `collect_pet_fish()` at the start of each session to harvest accumulated fish from pets.

## Tools

### `get_inventory()`
Full inventory including rod condition and durability.

### `equip_rod(rod_id)`
Equip a fishing rod (from inventory).

### `repair_rod(rod_id)`
Repair a damaged rod. Costs gold.

### `collect_pet_fish()`
Collect all accumulated fish from pets.

### `get_accessories()`
Get all accessories with current levels, effects, and available upgrade points.

### `upgrade_accessory(accessory_name)`
Upgrade an accessory by one level. Accepts name (e.g. "Rod Handle") or ID.
