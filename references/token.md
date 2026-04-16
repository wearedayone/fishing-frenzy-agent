# Token System Reference

## Token Types

### xFISH (Non-tradeable)
- In-game currency, **cannot be traded** on markets
- Earned from: Karma passes, daily quests, cooking wheel, diving rewards
- Spent on: Rod repairs, Karma passes, diving tickets (on-chain)
- Can be **converted to FISH** via the token dashboard

### FISH (Tradeable)
- On-chain token, **can be traded** on markets
- Spent on: Karma passes, diving tickets (on-chain), special sales
- Not directly earned from gameplay — obtained via xFISH conversion or purchase

## Karma

Karma determines access to game features. Earned through:
1. Token staking (xFISH or FISH)
2. Founder's Pass staking
3. Liquidity pool provision
4. In-game purchases
5. Wallet token acquisition
6. Game Karma (gameplay-based formula)

### Karma Thresholds
| Threshold | Unlocks |
|-----------|---------|
| 120,000 | Daily Karma wheel (xFISH rewards) |
| 200,000 | Prestige Leaderboard eligibility |

## Token Flow

```
Gameplay → xFISH (non-tradeable)
              ↓ convert
           FISH (tradeable) → sell on market
              ↓ or
           Stake → Karma → unlock features
```

## Available Tools

| Tool | Purpose |
|------|---------|
| `get_wallet_balances()` | Check RON, FISH, and xFISH balances on-chain |
| `stake_fish_tokens(amount, duration_months)` | Stake FISH tokens for Karma |
| `onchain_checkin()` | Daily on-chain check-in (costs small RON fee) |

**Not yet available:**
- Convert xFISH → FISH (requires additional contract ABI discovery)
