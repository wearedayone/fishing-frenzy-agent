# Diving Reference

## Requirements
- Level 30+
- Gold diving ticket: 2,500 gold each

## Ticket Types
| Type | Cost | Purchasable via API? |
|------|------|---------------------|
| Regular | 2,500 gold | Yes |
| Premium | RON (on-chain) | No — requires blockchain tx |
| Token | FISH token (on-chain) | No — requires blockchain tx |

The agent can only buy and use Regular (gold) tickets.

## Gameplay

The diving game is a grid-based minigame (10x6 board). Each cell may contain:
- Gold rewards
- Items (bait, chests)
- Jackpot prizes

### Risk Levels
| Approach | Picks | Risk |
|----------|-------|------|
| Conservative | 5-8 | Low — cash out early with guaranteed rewards |
| Moderate | 9-12 | Medium — good balance of risk/reward |
| Aggressive | 13-15 | High — more rewards but higher chance of game-ending cell |

### Multiplier Modes
- `X1`: Normal mode, uses 1 ticket
- `X10`: 10x rewards, uses 10 tickets

## Tools

### `buy_diving_ticket(quantity)`
Buy gold diving ticket(s). Costs 2,500 gold each.

### `dive(max_picks, multiplier)`
Execute a full diving session (use ticket → start → play WebSocket game).
- `max_picks`: Max cells to reveal before cashing out (0 = play until game ends)
- `multiplier`: `"X1"` (normal) or `"X10"` (10x, uses 10 tickets)

### `get_diving_config()`
Get diving game configuration: board sizes, coral rewards, ticket costs.

### `get_diving_state()`
Check if a dive is currently in progress.

### `get_diving_jackpots()`
Get current jackpot values for all dive types.
