# Chests Reference

## Overview

Chests are the **primary reward from leaderboards** and the **only way to get rod NFTs**.

## Chest Types

### Pioneer Chests
- Rarities: Common, Rare, Epic, Legendary
- Rod NFTs: Trail, Scout's, Pathfinder, Stargazer rods
- Source: Leaderboard rewards

### Rift Chests
- Rarities: Common, Rare, Epic, Legendary
- Rod NFTs: Shade, Fracture, Midnight, Abyss rods
- Source: Leaderboard rewards

## Contents

Each chest contains:
- **Gold** — varying amounts by rarity
- **Rod NFTs** — rarity-dependent drop rates (the main draw)
- **Non-NFT rods** — consolation when NFT roll fails

Higher-rarity chests have better NFT odds:
- **Legendary** — multiple guaranteed roll opportunities
- **Common** — ~45% chance of no NFTs

## Minting Requirement

**Leaderboard chests must be minted (on-chain) before they can be opened.** This is a blockchain transaction step — the chest exists as an NFT that must be claimed/minted to the player's wallet before the open action works.

The current `open_chests()` tool opens non-NFT chests. For leaderboard chests:
1. Chest appears in inventory after leaderboard rewards
2. **Mint the chest** (on-chain transaction required)
3. Then open the minted chest

## Starter/Reward Chests

Some chests (starter chests, event reward chests) do **not** require minting — they can be opened directly via `open_chests()`.

## Tools

### `get_chests()`
List all chests in inventory with types and quantities.

### `open_chests(chest_ids)`
Open non-NFT chests. Opens all available if no IDs specified.

### `mint_leaderboard_chests(chest_token_ids)`
Mint leaderboard chests on-chain. After minting, use `open_chests()` to open them.
