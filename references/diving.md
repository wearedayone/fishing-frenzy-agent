# Diving Reference

## Requirements
- **Level 30+** (see equipment reference for all unlock levels)
- Requires a diving ticket per dive

## Ticket Types
| Type | Cost | Purchasable via API? |
|------|------|---------------------|
| Regular | 2,500 gold | Yes |
| Premium | 6 RON (on-chain) | No — requires blockchain tx |
| Token | 1,200 xFISH or FISH (on-chain) | No — requires blockchain tx |

The agent can only buy and use Regular (gold) tickets.

## Board

The board is a **fixed-size grid** (6 columns × 10 rows = 60 cells). Board size does not change between dives.

Each cell contains one of 3 things:
1. **Coral** — reveals part of a coral formation. Fully uncovering an entire coral awards rewards
2. **Whirlpool** — costs 1 life. 2 whirlpools = game over with **NO rewards**
3. **Empty space** — nothing happens

## Whirlpools (Lives System)

- Players start each dive with **2 lives**
- Revealing a whirlpool **costs 1 life**
- **2 whirlpools revealed = game over** — player loses ALL uncollected rewards from that dive
- Number of whirlpools per board is **random** (7-10 whirlpools), with varying probability:
  - Distribution roughly: 16.67%-33.33% chance for each count in the 7-10 range
- The high whirlpool count (7-10 out of 60 cells) means ~12-17% of cells are deadly

## Corals (Reward System)

Corals are multi-tile formations similar to **Battleship pieces**:
- **Small corals**: Single tile — revealed in one click
- **Big corals**: Multiple connected tiles in shapes (L-shape, rectangular, other configurations)
- Corals must be **fully uncovered** to collect their rewards
- Like **Carcassonne**, revealed coral edges give visual hints about where adjacent coral tiles are — the agent should use this to strategically click adjacent cells to complete partially-revealed corals

### Coral Rewards
Rewards depend on coral **color** and **size**:
- Colors: Red, Pink, Brown, Small
- Reward types: Gold, RON, xFISH, Sashimi, Sushi, fishing rods, Fin Fragments
- Bigger corals = better rewards

### Coral Count
The number of corals per board is **random** — sometimes more, sometimes fewer. Combined with random whirlpool count, each board has a different risk/reward profile.

## Jackpot

- Each dive has a chance to win the **jackpot**
- Base jackpot values: 250,000 Gold / 120,000 xFISH (accumulates — 1% of all dives feed the pool)
- Win chance: **0.001%** (X1 mode) or **0.01%** (X10 mode — 10x better odds)
- Requirement: must have **collected a big coral** during the dive to qualify

## Cash-Out Mechanic

- Players can **cash out at any time** using the Collect button
- Cash-out secures all rewards from fully-uncovered corals so far
- The strategic decision: cash out early (safe, guaranteed rewards) vs keep picking (more rewards but risk hitting 2nd whirlpool and losing everything)
- **Partially uncovered corals give no rewards** — only fully revealed ones count

## Multiplier Modes
| Mode | Tickets Used | Rewards | Jackpot Chance |
|------|-------------|---------|---------------|
| X1 | 1 ticket | Normal | 0.001% |
| X10 | 10 tickets | 10× rewards | 0.01% (10× better) |

## Strategy

### Risk Levels (from CONFIG.md)
| Approach | Picks | Risk |
|----------|-------|------|
| Conservative | 5-8 | Low — cash out early with small guaranteed rewards |
| Moderate | 9-12 | Medium — balance of risk and reward |
| Aggressive | 13-15 | High — more corals found but higher whirlpool risk |

### Smart Diving Rules
1. **Track lives**: If 1 whirlpool already hit, consider cashing out — next whirlpool = lose everything
2. **Follow coral edges**: When a coral tile is partially revealed, click adjacent cells to complete it (like Carcassonne/Battleship deduction)
3. **Complete before collecting**: Partially-uncovered corals give nothing — try to finish what you've started
4. **Jackpot requires a big coral**: If going for jackpot, prioritize completing big coral formations
5. **X10 for jackpot hunters**: 10× jackpot chance makes X10 worthwhile for jackpot-focused play

### Current Agent Limitation
The agent currently picks cells **randomly** (`random.shuffle(all_cells)`). A smarter approach would:
- Track which cells have been revealed and what they contained
- When a coral edge is found, prioritize adjacent cells to complete the formation
- Avoid cells in whirlpool-dense areas (though whirlpool positions are hidden)

## Tools

### `buy_diving_ticket(quantity)`
Buy gold diving ticket(s). Costs 2,500 gold each.

### `dive(max_picks, multiplier)`
Execute a full diving session (use ticket → start → play WebSocket game).
- `max_picks`: Max cells to reveal before cashing out (0 = play until game ends)
- `multiplier`: `"X1"` (normal) or `"X10"` (10x, uses 10 tickets)

### `get_diving_config()`
Get diving game configuration: board sizes, coral rewards, ticket costs, whirlpool counts.

### `get_diving_state()`
Check if a dive is currently in progress.

### `get_diving_jackpots()`
Get current jackpot values for all dive types.
