# Fishing Reference

## Fish Rarity Tiers

| Rarity | # Species | XP Range | Gold Range | Example Fish |
|--------|-----------|----------|------------|-------------|
| Common | 8 | 100-750 | 1-8 | Anchovy, Bream |
| Rare | 6 | 1,000-4,750 | 10-49 | Red Snapper, Rainbow Trout |
| Epic | 5 | 6,000-8,500 | 63-89 | Salmon, Pike |
| Legendary | 5 | 10,000-15,000 | 104-156 | Tuna, Sturgeon |
| Mythic | 2 | 80,000-120,000 | 833-1,250 | Blue Lobster, Frog |

**Quality mapping**: The API returns quality 1-5: **1=Common, 2=Rare, 3=Epic, 4=Legendary, 5=Mythic**. There is no "Uncommon" tier.

## Ranges & Drop Tables

Each range has a **different drop table** — higher ranges increase the weight of rarer fish:

| Range | Energy | Drop Table Bias | Best For |
|-------|--------|----------------|----------|
| `short_range` | 1 | Heavily Common, small Rare chance | Energy conservation, grinding volume |
| `mid_range` | 2 | More Epic weighted | Balanced value, cooking ingredients |
| `long_range` | 3 | More Legendary weighted | Max gold/XP per session, Mythic Bait pairing |

The range does NOT guarantee a specific rarity — it shifts the probability distribution. You can still catch Common fish on long_range and Rare fish on short_range.

## Range/Bait Strategies

The agent uses **3 fishing strategies** that pair a range with its matching bait:

| Strategy | Range | Bait | Energy/Cast | Drop Table | Best For |
|----------|-------|------|-------------|------------|----------|
| **Short** | `short_range` | None | 1 | Common-heavy | Max casts per energy, volume grinding |
| **Medium** | `mid_range` | Medium Bait | 2 | Epic-weighted | Balanced value, cooking ingredients |
| **Long** | `long_range` | Big Bait | 3 | Legendary-weighted | Best gold/XP per cast, high-value fish |

**How to choose:**
- **Short** when energy is limited, need common fish for recipes, or grinding volume
- **Medium** when you have Medium Bait and want epic fish for cooking/quests
- **Long** when you have Big Bait and want max gold/XP value per cast
- If no bait is available for Medium/Long, Short is the fallback (no point in higher energy cost without the bait boost)

**Energy constraints:**
- **Energy < 2**: Must use Short
- **Energy < 3**: Cannot use Long
- **5x multiplier**: Need energy >= range × 5
- **20x multiplier**: Need energy >= range × 20 (plus 1,200 gold)

**Special case — Mythic Bait**: Use `long_range` + Mythic Bait (2,000% Mythic boost). Only meaningful in the Legendary-weighted drop table. See pity system below.

## Bait Types

| Bait | Effect | Paired With |
|------|--------|-------------|
| Small Bait | 250% boost to **Rare** drop weight | short_range |
| Medium Bait | 200% boost to **Epic** drop weight | mid_range |
| Big Bait | 150% boost to **Legendary** drop weight | long_range |
| Mythic Bait | 2,000% boost to **Mythic** drop weight | long_range |

Bait is consumed on use. The agent should check inventory for bait at session start and select the matching strategy.

## Mythic Bait Pity System

Mythic Bait has a guaranteed catch mechanic:

- Each Mythic Bait cast that does NOT catch a Mythic fish adds **1 pity**
- After accumulating **29 pity**, the next Mythic Bait cast **guarantees** a Mythic fish
- Pity resets to 0 when a Mythic fish is caught
- **Multiplier scaling**: x5/x20 multipliers scale both pity gained AND the pity threshold proportionally (so 5x gives 5 pity per cast but threshold is effectively the same number of casts)

**Implication**: If the agent has Mythic Bait, it should track pity count. After ~29 Mythic Bait casts without a Mythic, the next one is guaranteed.

## Multipliers

All multipliers are **convenience only** — no mathematical advantage. Higher multipliers save time (fewer cooldowns) but yield the same rewards-per-energy ratio.

| Multiplier | Energy Cost | Gold Cost | Rewards | Use Case |
|-----------|------------|-----------|---------|----------|
| 1x | range × 1 | 0 | 1× gold/XP | Default |
| 5x | range × 5 | 0 | exactly 5× gold/XP | Save time, same efficiency (unlocks at **Level 5**) |
| 20x | range × 20 | 1,200 gold | exactly 20× gold/XP | Speed dump — **less efficient** (unlocks at **Level 30**) |

**Decision rules:**
- **1x**: Use when energy is low or you want to observe each cast
- **5x**: Safe to use anytime to save time — identical gold/energy ratio to 1x
- **20x**: Only use when the user explicitly wants to dump energy fast. Never use for efficiency — the 1,200 gold cost makes it a net loss compared to 1x/5x

## Tools

### `fish(range_type, multiplier)`
Execute one fishing session.
- `range_type`: `"short_range"`, `"mid_range"`, or `"long_range"`
- `multiplier`: 1, 5, or 20
- Returns: fish caught, XP gained, gold value, energy remaining

### `fish_batch(range_type, count, multiplier)`
Fish multiple times in sequence. Stops if energy runs out.
- `count`: Number of sessions to attempt
- Returns: summary with total caught, XP, gold, successes/failures, and individual results

## Event Themes

The game periodically runs **event themes** — alternate fishing zones with:
- **Different drop tables** — event-exclusive fish species not available in the default zone
- **Event currencies** — special currencies that drop alongside normal fish, used to purchase limited-time items (pets, cosmetics, etc.)
- **Event shops** — temporary shops where event currencies can be spent

### Theme Decision Rules
1. At session start, check for active events
2. **If an event theme is active, fish there** — event-exclusive drops are time-limited and typically more valuable than the default zone
3. If no event is active, use the default theme
4. When an event is running, check the event shop for desirable items (pets especially)

Examples of past event themes: Lunar New Year, Christmas — each with unique fish species and special rewards.

**Current gap**: `get_active_themes()` exists in `fishing_client.py` but is not yet exposed as an MCP tool. The agent currently always uses `DEFAULT_THEME_ID`.

## Fish Escape Mechanic

Fish escapes are **skill-based**, not random. Two failure modes:
1. **Failed hook**: Player doesn't react in time when the fish bites
2. **Failed reel-in**: Fish isn't caught within the time limit during the minigame

The agent simulates this by generating frame data (`[fishY, netY]` pairs) submitted to the server. The server evaluates these frames to determine success. If the generated frames poorly simulate the minigame, the agent will have a higher-than-necessary escape rate.

**Note**: Escaped fish still cost energy — the energy is spent on the cast, not the catch.

## Fishing Loop

Use `fish_batch()` for efficiency (handles cooldowns automatically). After each batch:
1. Display results cast-by-cast from the results array
2. Display updated dashboard
3. Check if energy allows another batch
4. If energy depleted, move to sell phase
