# Cooking Reference

## Workflow

1. Call `get_recipes()` to see today's active cooking recipes
2. Check if you have the required fish types in inventory
3. Call `cook(recipe_id, quantity, fish_ids)` to create sashimi
4. Sell sashimi for pearls, or spin cooking wheel

**Rule**: Only cook if you have enough matching fish. Don't buy fish just to cook.

## Cooking Wheel

Spend pearls to spin the cooking wheel for xFISH rewards. The Efficiency strategy prioritizes cooking wheel spins.

## Tools

### `get_recipes()`
Get today's active cooking recipes with requirements and rewards.

### `cook(recipe_id, quantity, fish_ids, shiny_fish_ids)`
Cook fish into sashimi.
- `recipe_id`: From `get_recipes()`
- `quantity`: Number of times to cook
- `fish_ids`: List of fish IDs to use as ingredients
- `shiny_fish_ids`: Optional list of shiny fish for bonus

### `sell_sashimi(sashimi_id, quantity)`
Sell sashimi for pearls.

### `spin_cooking_wheel(amount)`
Spend pearls to spin cooking wheel. Each spin costs pearls.
