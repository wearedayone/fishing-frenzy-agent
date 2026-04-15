# Fishing Frenzy Agent

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

32 tools total across all game systems.

## How It Works

```
fishing-frenzy-agent/
├── SKILL.md                  ← Strategy brain (edit this to compete!)
├── ff_agent/
│   ├── server.py             ← MCP server — 32 game action tools
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
