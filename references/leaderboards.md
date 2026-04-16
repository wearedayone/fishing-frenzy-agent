# Leaderboards Reference

## Overview

Weekly competitions where players compete in fishing and cooking. Rewards include chests (the only source of rod NFTs).

## Leaderboard Types

### Prestige Leaderboard
- **Requirement**: 200,000+ Karma at the **start** of the leaderboard period
- Players who reach 200k Karma mid-period stay in Open for that cycle
- Higher-tier rewards

### Open Leaderboard
- Available to all players
- No Karma requirement

## Weekly Reset

- Leaderboards reset **weekly**
- Players compete on fishing and cooking performance during the period
- Collection Leaderboard (Aquarium EXP) is separate and **does not reset** — lifetime accumulation

## Rewards

- **Chests** — Pioneer and Rift types (see chests reference)
- Chests from leaderboards **must be minted** before opening (on-chain transaction)
- Higher placement = better chest rarity

## Strategy

1. Call `get_leaderboard()` to check current standing
2. Focus fishing/cooking effort during the week to climb rankings
3. After weekly reset, check for chest rewards in inventory
4. Leaderboard chests need minting (currently not automatable by agent)

## Tools

### `get_leaderboard(rank_type)`
View rankings. Types: `"General"`, `"Cooking"`, `"Frenzy_point"`.
