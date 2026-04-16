# Collecting / Aquarium Reference

## Overview

Collecting permanently consumes fish to add them to the player's Aquarium. Collected fish **cannot be recovered** — they are gone from inventory forever (cannot be sold or cooked after).

This is the **3rd fish disposal option** alongside selling and cooking.

## How It Works

1. Submit fish from inventory into the Aquarium collection
2. Each submitted fish grants **Collection EXP**
3. Collection EXP increases two separate levels:
   - **Overall Collection Level** — total EXP across all fish types
   - **Individual Fish Level** — per-species count (shiny variants tracked separately)
4. Both level types grant **rewards at milestones**

## Rewards

- **Milestone rewards** at collection level thresholds (exact rewards TBD — inspect API response)
- **Aquarium display** — higher collection levels add more fish visuals to the aquarium
- **Collection Leaderboard** — ranks by lifetime Aquarium EXP (persists across weekly resets)
- **Admiration** — once per day, admire a random top-100 Prestige aquarium for **20 gold**

## When to Collect vs Sell vs Cook

| Fish Type | Sell | Cook | Collect |
|-----------|------|------|---------|
| Common fish (no recipe match) | Good — quick gold | N/A | Consider if near a milestone |
| Common fish (recipe match) | Skip | Best — pearls → wheel | Skip |
| Rare+ fish (recipe match) | Skip | Best | Skip |
| Shiny (NFT) fish | Hold/sell on market | Better cooking rewards | Tracked separately — valuable for collection |
| Duplicate commons (already collected) | Best — no collection value | If recipe matches | Low value unless stacking levels |

## Decision Rules for the Agent

1. Check collection status — which fish are near a milestone?
2. If a fish would push a species to the next collection level reward → **collect**
3. If a fish matches an active recipe → **cook**
4. Otherwise → **sell** (or hold if `FISH_DISPOSAL=hold`)

## Available Tools

| Tool | Purpose |
|------|---------|
| `get_fish_collection()` | View full collection progress — all species, counts, milestones |
| `collect_fish(fish_id, quantity)` | Collect a specific fish (permanently consumes from inventory) |
| `collect_all_non_nft_fish()` | Collect all non-NFT fish at once |
| `get_collection_overview()` | Aquarium levels, total EXP, milestone progress |
| `claim_collection_rewards()` | Claim available aquarium level milestone rewards |
| `claim_fish_collection_reward(collection_id)` | Claim reward for a specific collection entry |
| `admire_aquarium()` | Admire a top-100 aquarium for 20 gold (once/day) |
