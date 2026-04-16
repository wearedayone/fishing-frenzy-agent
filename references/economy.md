# Economy Reference

## Energy System

### Daily Reset
- Energy resets **once per day at 2:00 AM UTC**
- Players with **less than 30 energy** receive **+30 energy** (additive, e.g. 5 → 35)
- Players with **30 or more energy** receive **nothing** from the reset
- There is no passive energy regeneration throughout the day

### Sushi & Energy
- Sushi costs **500 gold**, restores **5 energy**
- **No daily purchase limit** — players can buy unlimited sushi
- **Energy can exceed the displayed max** — using 10 sushi at 25/30 energy results in **75/30 energy**
- Energy only has a "soft cap" at 30 for the daily reset check, not a hard cap for sushi

### Sushi Profitability
Sushi is **NOT always profitable**. The agent must calculate whether the expected gold from 5 energy of fishing exceeds the 500g sushi cost:

| Range | Avg Gold/Cast | Casts per Sushi (5 energy) | Expected Return | Profitable? |
|-------|--------------|---------------------------|-----------------|-------------|
| short_range | ~5g (mostly Common) | 5 casts | ~25g | **No** (500g cost, ~25g return) |
| mid_range | ~25g (some Epic) | 2.5 casts | ~62g | **No** |
| long_range | ~60g (some Legendary) | 1.67 casts | ~100g | **No** (but closer) |

**Sushi is a net gold loss for grinding.** It's only worth buying when:
1. The player needs to **complete time-sensitive goals** (quests, events) before energy resets
2. The player has **valuable bait** to use (Mythic Bait + long_range can yield 833-1250g Mythic fish)
3. The player is close to a **Mythic pity guarantee** (29 pity = guaranteed 833-1250g fish)
4. The player prioritizes **XP/leveling** over gold efficiency

The thresholds in CONFIG.md are gold reserves to prevent the agent from bankrupting the account, not profitability calculations.

### Sushi Buy Rules (from CONFIG.md)
| Strategy | Buy Threshold | Reserve |
|----------|--------------|---------|
| Balanced | gold > 1500 | Keep 1000 |
| Grind | gold > 800 | Keep 300 |
| Efficiency | gold > 2000 | Keep 1500 |

## Gold Management

- **Always sell common fish** — they're not worth cooking (1-8g each)
- **Keep rare+ fish** for cooking recipes if recipes are active
- Common fish sell for 1-8g, Mythic fish sell for 833-1250g

## Free Gold Sources
- **Admire aquarium** — 20 gold/day (admire a random top-100 Prestige aquarium)
- **Sell fish** — primary gold income
- **Collection milestones** — rewards from aquarium collection levels
- **Quests/daily reward** — gold from quest completions and daily login

## Item Priority
1. Sushi (energy refill) — ID: `668d070357fb368ad9e91c8a` — only when strategically justified
2. Bait (boosts rarity drop weight — see fishing reference)
3. Save gold for equipment repairs (shiny rod maintenance)

## Tools

### `sell_fish(fish_id, quantity)`
Sell a specific fish type from inventory.

### `sell_all_fish()`
Sell ALL fish in inventory at once. Returns total gold earned.

### `buy_item(item_name, quantity, auto_use=True)`
Buy an item by name (e.g. `"sushi"`) or by item ID. By default, consumable items like sushi are automatically used after buying — so `buy_item("sushi", 2)` will both purchase and consume 2 sushi, restoring 10 energy.

Set `auto_use=False` to buy without using (item goes to inventory).

### `use_item(item_name, quantity=1)`
Use a consumable item from inventory. Supports using multiple at once (e.g. `use_item("sushi", 3)`).

### `get_shop()`
List all available shop items with prices.

### `get_inventory()`
Full inventory: fish, items, rods, chests, consumables.
