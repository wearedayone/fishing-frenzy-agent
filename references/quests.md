# Quests Reference

## Quest Types

### Daily Quests
- **Reset at 2:00 AM UTC** each day (same time as energy reset)
- Involve gameplay actions: fishing, selling, cooking, diving, etc.
- Each completed quest awards **points** toward the daily wheel
- The agent should **aim to complete all daily quests** each session — they drive progression and unlock the wheel

### Account-Bound Quests
- One-time quests that persist across sessions (e.g. "Link your X account", "Join Discord")
- Do not reset — once completed, they stay completed
- Social quests: call `verify_social_quest(quest_id)` to complete

### Quest Rewards
- Each quest has a reward value visible in the API response (gold, XP, items, etc.)
- The agent can inspect reward values to prioritize if needed, but all daily quests are worth completing

## Daily Wheel

### Eligibility
- The player must accumulate **2,000 points** from completing daily quests to spin
- Points come from individual quest completions (e.g. "Complete 1 dive" = 600 pts, "Daily on-chain check-in" = 600 pts)
- Points reset daily with the quests at 2:00 AM UTC

### Strategy
- Check quest point values and prioritize quests that get to 2,000 pts fastest
- Some quests grant large point values (600 pts) — identify these early
- The wheel spin is a significant daily reward — worth adjusting the game loop to reach 2,000 pts

## Karma Wheel (xFISH)

- Accounts with **120,000+ Karma** unlock an additional wheel spin
- This wheel awards **xFISH** tokens, which have in-game value (can be spent in-game)
- Check karma via `get_profile()` — the `karma` field
- If karma >= 120k, spin this wheel each session for free xFISH

## Workflow

1. Call `get_quests()` to see all quests with status and point values
2. Identify which daily quests are closest to completion or give the most points
3. Play the game loop with quest completion in mind (e.g. switch to long_range if a quest requires it)
4. Call `claim_quest(quest_id)` for any completed quests
5. Once points >= 2,000: call `spin_daily_wheel()`
6. If karma >= 120,000: spin karma wheel for xFISH
7. Social quests: call `verify_social_quest(quest_id)` for one-time social tasks

## Daily Reward

Call `claim_daily_reward()` once per day for the login bonus. Resets at 2:00 AM UTC. Do this early in each session.

## Tools

### `claim_daily_reward()`
Claim today's daily login reward.

### `get_quests()`
List all quests (daily, user) with current status, progress, point values, and rewards.

### `claim_quest(quest_id)`
Claim a completed quest's reward.

### `verify_social_quest(quest_id)`
Complete a social quest (auto-verifies for account-bound social tasks).

### `spin_daily_wheel()`
Spin the daily quest reward wheel. Requires 2,000+ quest points for the day.
