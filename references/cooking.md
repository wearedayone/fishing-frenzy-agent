# Cooking Reference

## Overview

Cooking converts fish into sashimi, which is sold for **pearls**. Pearls can only be spent on the **cooking wheel** (xFISH rewards). There is no other use for pearls.

## Fish Disposal Strategy

Players have **3 mutually exclusive options** for each fish caught:
1. **Cook** — use as a recipe ingredient to create sashimi → pearls → cooking wheel (longer pipeline, potential xFISH)
2. **Collect** — permanently consume into the Aquarium for Collection EXP and milestone rewards (see `collecting.md`)
3. **Sell** — convert to gold immediately (simple, guaranteed value)

The agent should process fish in this priority order:
1. **Cook first** — does this fish match an active recipe? → Cook it
2. **Collect second** — is this fish near an aquarium collection milestone? → Collect it
3. **Sell last** — sell everything remaining

Special considerations:
- **Shiny (NFT) fish** → Better cooking rewards, tracked separately in aquarium. Decide based on current goal
- **Common fish with no recipe match** → Sell (or collect if near milestone)
- Fish that are collected are **permanently consumed** — cannot be recovered

## Recipes

- Recipes require **specific fish species** as components (e.g. 2× Bream + 3× Salmon)
- Each recipe has different fish type and quantity requirements
- Some recipes require **shiny fish only** (NFT fish caught with shiny rods)
- Recipes rotate — check `get_recipes()` each session for current active recipes
- **Cooking level does NOT affect which recipes are available**
- **Cooking unlocks at fishing Level 15**

## Shiny Fish in Cooking

- Shiny fish are NFTs, caught using NFT rods (which have a % chance per cast)
- Using shiny fish as ingredients yields **better rewards** than normal fish
- The `shiny_fish_ids` parameter in `cook()` is for passing shiny fish separately from normal fish
- Decision: shiny fish are valuable both as NFTs (hold/sell on market) and as cooking ingredients (better rewards) — the agent should consider which yields more value

## Cooking Level

- Cooking level scales the same way fishing level scales (XP-based progression)
- Cooking does NOT gate recipe availability
- Higher cooking level may improve rewards (needs verification)

## Cooking Wheel

- **Only way to spend pearls** — save them or spin, no other option
- Rewards include xFISH tokens
- The Efficiency strategy prioritizes spinning the cooking wheel
- Decision: spin immediately vs save for potential future pearl uses (currently none exist)

## Workflow

1. Call `get_recipes()` to see today's active cooking recipes
2. Check recipe `components` — each lists required fish species + quantities
3. Cross-reference with inventory (`get_inventory()`) for matching fish
4. If matching fish exist: `cook(recipe_id, quantity, fish_ids, shiny_fish_ids)`
5. Sell sashimi for pearls: `sell_sashimi(sashimi_id, quantity)`
6. Spin cooking wheel: `spin_cooking_wheel(amount)`

**Important**: Cook BEFORE selling (`sell_all_fish`), or you'll sell the fish you need as ingredients. The game loop in SKILL.md must do step 11 (cook) before step 10 (sell).

## Tools

### `get_recipes()`
Get today's active cooking recipes with requirements and rewards.
- Response includes `components` array with fish species and quantities per recipe

### `cook(recipe_id, quantity, fish_ids, shiny_fish_ids)`
Cook fish into sashimi.
- `recipe_id`: From `get_recipes()`
- `quantity`: Number of times to cook
- `fish_ids`: List of normal fish IDs to use as ingredients
- `shiny_fish_ids`: Optional list of shiny (NFT) fish IDs for bonus rewards

### `sell_sashimi(sashimi_id, quantity)`
Sell sashimi for pearls.

### `spin_cooking_wheel(amount)`
Spend pearls to spin cooking wheel. Each spin costs pearls.
