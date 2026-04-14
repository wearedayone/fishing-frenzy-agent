# Fishing Frenzy Agent

An AI agent that plays [Fishing Frenzy](https://fishingfrenzy.co) autonomously via Claude Code. Install the plugin, run `/play`, and your agent handles fishing, selling, cooking, quests, and equipment management.

**The meta-game**: Customize the strategy in `skills/play/SKILL.md` to optimize your agent's decision-making. Same tools, different strategies.

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/wearedayone/fishing-frenzy-agent
cd fishing-frenzy-agent
pip install -r requirements.txt
```

### 2. Add to Claude Code

```bash
claude mcp add fishing-frenzy -- python3 ff_agent/server.py
```

Or add the plugin directory:

```bash
claude --plugin-dir ./fishing-frenzy-agent
```

### 3. Play

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
7. Report session stats

## How It Works

```
fishing-frenzy-agent/
├── .claude-plugin/
│   └── plugin.json            ← Plugin manifest
├── skills/
│   └── play/
│       └── SKILL.md           ← Strategy brain (edit this to compete!)
├── ff_agent/
│   ├── server.py              ← MCP server — 25 game action tools
│   ├── auth.py                ← Privy SIWE wallet auth
│   ├── api_client.py          ← REST API wrapper
│   ├── fishing_client.py      ← REST fishing protocol
│   ├── state.py               ← SQLite state persistence
│   └── wallet.py              ← Ethereum wallet management
├── .mcp.json                  ← MCP server config
├── requirements.txt
└── LICENSE                    ← MIT
```

**MCP Server** exposes game actions as tools that Claude can call:
- `setup_account()` / `login()` / `get_profile()`
- `fish()` / `fish_batch()` — REST-based fishing sessions
- `sell_all_fish()` / `buy_item()` / `use_item()`
- `get_recipes()` / `cook()` / `spin_cooking_wheel()`
- `claim_daily_reward()` / `get_quests()` / `claim_quest()`
- `equip_rod()` / `repair_rod()` / `collect_pet_fish()`
- `get_leaderboard()` / `get_session_stats()`

**SKILL.md** teaches Claude how to play — the game loop, decision framework, and strategy templates. Edit this file to change how your agent plays.

## Customizing Your Strategy

Open `skills/play/SKILL.md` and modify the strategy sections:

### Built-in Strategies

| Strategy | Focus | Best For |
|----------|-------|----------|
| `balanced` | Even split of fishing, cooking, quests | Default, well-rounded |
| `grind` | Max casts, sell everything, aggressive sushi | XP farming, early levels |
| `efficiency` | Long range only, cook strategically | Gold optimization, later game |

Run with a specific strategy:

```
/play grind
```

### Make Your Own

Edit the Decision Rules, Economy, and Cooking sections in SKILL.md to create custom strategies. The agent follows whatever rules you write.

## Data Storage

All data is stored locally at `~/.fishing-frenzy-agent/`:

- `state.db` — wallet, auth tokens, session history
- No data is sent anywhere except the Fishing Frenzy API

## Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/claude-code)
- Dependencies: `mcp`, `httpx`, `eth-account`

## License

MIT — see [LICENSE](LICENSE).
