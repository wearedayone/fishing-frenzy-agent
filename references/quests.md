# Quests Reference

## Quest Types

- **Daily quests**: Reset each day. Often involve fishing, selling, or cooking.
- **User quests**: Persistent progression quests.
- **Social quests**: Follow on Twitter, join Discord, etc. Auto-verify when claimed.

## Workflow

1. Call `get_quests()` to see all quests with status
2. Many quests complete automatically through normal play (fishing, selling, etc.)
3. Call `claim_quest(quest_id)` for any quest showing as "completed"
4. Social quests: call `verify_social_quest(quest_id)` — these auto-verify

## Daily Reward

Call `claim_daily_reward()` once per day for the login bonus. Do this early in each session.

## Daily Wheel

Call `spin_daily_wheel()` if eligible — free daily spin for bonus rewards.

## Tools

### `claim_daily_reward()`
Claim today's daily login reward.

### `get_quests()`
List all quests (daily, user) with current status and progress.

### `claim_quest(quest_id)`
Claim a completed quest's reward.

### `verify_social_quest(quest_id)`
Complete a social quest (auto-verifies).

### `spin_daily_wheel()`
Spin the daily quest reward wheel (if eligible).
