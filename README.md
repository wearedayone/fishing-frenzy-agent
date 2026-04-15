# Fishing Frenzy Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/MCP_tools-36-purple.svg)](#what-the-agent-can-do)
[![Fishing Frenzy](https://img.shields.io/badge/game-Fishing_Frenzy-orange.svg)](https://fishingfrenzy.co)

An AI agent that plays [Fishing Frenzy](https://fishingfrenzy.co) autonomously via Claude Code. Install the skill, run `/play`, and your agent handles fishing, selling, cooking, quests, diving, and equipment management.

**The meta-game**: Customize the strategy in `SKILL.md` to optimize your agent's decision-making. Same tools, different strategies.

## Install

### Option A: Skills CLI (Recommended)

```bash
npx skills add wearedayone/fishing-frenzy-agent
```

Then run the setup script to register the MCP server:

```bash
bash ~/.claude/skills/fishing-frenzy-agent/scripts/setup.sh
```

### Option B: Clone

```bash
git clone https://github.com/wearedayone/fishing-frenzy-agent
cd fishing-frenzy-agent
bash scripts/setup.sh
```

### Option C: Manual

```bash
git clone https://github.com/wearedayone/fishing-frenzy-agent
cd fishing-frenzy-agent
pip install -r requirements.txt
claude mcp add fishing-frenzy -- python3 "$(pwd)/ff_agent/server.py"
```

## Play

Open Claude Code and type:

```
/play
```

Your agent will:
1. Create a new wallet and guest account (first run only)
2. Claim daily rewards
3. Fish until energy is depleted
4. Sell fish for gold
5. Complete quests and cook sashimi
6. Buy sushi to refill energy and keep going
7. Display a session summary with stats

Choose a strategy:

```
/play grind       # Max XP, aggressive sushi buying
/play efficiency  # Best gold/energy ratio, strategic cooking
/play balanced    # Default — even split across all activities
```

## What the Agent Can Do

| System | Tools | Description |
|--------|-------|-------------|
| Fishing | `fish`, `fish_batch` | Cast lines at short/mid/long range |
| Economy | `sell_all_fish`, `buy_item`, `use_item` | Sell catches, buy sushi, manage gold |
| Cooking | `get_recipes`, `cook`, `spin_cooking_wheel` | Cook sashimi, earn pearls |
| Quests | `claim_daily_reward`, `get_quests`, `claim_quest` | Daily rewards, quest completion |
| Equipment | `equip_rod`, `repair_rod`, `collect_pet_fish` | Rod management, pet collection |
| Diving | `buy_diving_ticket`, `dive` | Grid-based diving game (Level 30+) |
| Upgrades | `get_accessories`, `upgrade_accessory` | Spend upgrade points on accessories |
| Stats | `get_leaderboard`, `get_session_stats` | Rankings, performance tracking |

36 tools total across all game systems.

## Demo

When you run `/play`, your agent displays a live game dashboard:

```
╔══════════════════════════════════════════════════╗
║  🎣 FISHING FRENZY AGENT                        ║
║  Strategy: BALANCED                              ║
╠══════════════════════════════════════════════════╣
║  👤 FishBot_0x3e1C  ·  Lv.25                    ║
║  ⚡ Energy: 22/30    ██████████████░░░░░ 73%     ║
║  💰 Gold: 1,075     🏆 XP: 12,450               ║
╚══════════════════════════════════════════════════╝

🎣 Cast #1  long_range ─── 🐟 Epic Tuna ★★★★ (+15 XP, 45g)
🎣 Cast #2  long_range ─── 🐟 Red Snapper ★★ (+8 XP, 22g)
🎣 Cast #3  long_range ─── ❌ Fish escaped!
🎣 Cast #4  mid_range  ─── 🐟 Golden Koi ★★★★★ (+25 XP, 80g)  🆕 NEW FISH!
🎣 Cast #5  short_range ── 🐟 Common Sardine ★ (+3 XP, 5g)

📦 SELL   Sold all fish → +238 gold (total: 1,313)
✅ QUEST  "Catch 5 fish" complete → +100 gold, +50 XP
🛒 SHOP   Bought 1× Sushi (-500g) → ⚡ +5 energy
⬆️ UPGRADE Rod Handle Lv.0 → Lv.1 (1.25% energy save chance)

╔══════════════════════════════════════════════════╗
║  📊 SESSION COMPLETE                             ║
╠══════════════════════════════════════════════════╣
║  🐟 Fish Caught:  47         ⏱️  Duration: ~8m   ║
║  💰 Gold Earned:  2,340      💰 Gold Now: 3,415  ║
║  ⭐ XP Earned:    890        📈 Level: 25 → 27   ║
║  ⚡ Energy Used:  30/30      🍣 Sushi Used: 2    ║
╠══════════════════════════════════════════════════╣
║  🏆 Best Catch: Golden Koi ★★★★★ (80g)          ║
║  📊 Efficiency: 78g/energy                       ║
╚══════════════════════════════════════════════════╝
```

## How It Works

```
fishing-frenzy-agent/
├── SKILL.md                  ← Strategy brain (edit this to compete!)
├── ff_agent/
│   ├── server.py             ← MCP server — 36 game action tools
│   ├── auth.py               ← Privy SIWE wallet auth (Ronin chain)
│   ├── api_client.py         ← REST API wrapper
│   ├── fishing_client.py     ← Fishing session protocol
│   ├── diving_client.py      ← WebSocket diving protocol
│   ├── state.py              ← SQLite state persistence
│   └── wallet.py             ← Ethereum wallet management
├── scripts/
│   ├── setup.sh              ← One-command install
│   └── status.py             ← Agent status check
├── requirements.txt
└── LICENSE                   ← MIT
```

**SKILL.md** teaches Claude how to play — the game loop, decision framework, and strategy templates. Edit this file to change how your agent plays.

**MCP Server** (`ff_agent/server.py`) exposes game actions as tools that Claude calls autonomously.

## Customizing Your Strategy

Edit `SKILL.md` to change your agent's behavior:

- Adjust fishing range preferences
- Change sushi buying thresholds
- Prioritize cooking over fishing
- Set energy management rules
- Change accessory upgrade priority

The three built-in strategies (balanced, grind, efficiency) are starting points. Create your own by modifying the decision rules.

## Data Storage

All data is stored locally at `~/.fishing-frenzy-agent/`:

- `state.db` — wallet, auth tokens, session history
- No data is sent anywhere except the Fishing Frenzy game API

## Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/claude-code)

## License

MIT — see [LICENSE](LICENSE).
