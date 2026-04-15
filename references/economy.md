# Economy Reference

## Gold Management

- **Always sell common fish** — they're not worth cooking
- **Keep rare+ fish** for cooking recipes if recipes are active
- **Sushi** costs 500 gold, restores 5 energy

### Sushi Buy Rules
| Strategy | Buy Threshold | Reserve |
|----------|--------------|---------|
| Balanced | gold > 1500 | Keep 1000 |
| Grind | gold > 800 | Keep 300 |
| Efficiency | gold > 2000 | Keep 1500 |

Only buy sushi when energy = 0 and more fishing would be profitable.

## Item Priority
1. Sushi (energy refill) — ID: `668d070357fb368ad9e91c8a`
2. Bait (if available, improves catch quality)
3. Save gold for equipment repairs

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
