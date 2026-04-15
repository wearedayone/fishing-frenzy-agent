"""FastMCP server for Fishing Frenzy Agent — exposes game actions as tools."""

import json
import sys
import os

# Ensure the parent directory is in the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP  # from pip package 'mcp'

from ff_agent import auth as ff_auth
from ff_agent import api_client as api
from ff_agent import fishing_client
from ff_agent import diving_client
from ff_agent import state

# Well-known item IDs
SUSHI_ITEM_ID = "668d070357fb368ad9e91c8a"

ITEM_NAME_MAP = {
    "sushi": SUSHI_ITEM_ID,
}

server = FastMCP(
    "Fishing Frenzy Agent",
    instructions="AI agent tools for playing Fishing Frenzy autonomously.",
)


# ============================================================
# Account & Auth
# ============================================================

@server.tool()
def setup_account() -> str:
    """Create a new wallet, register with Privy, and log into the game.
    Run this once on first use. Returns wallet address and user ID."""
    try:
        result = ff_auth.setup_account()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def login() -> str:
    """Authenticate and get a fresh JWT token. Auto-refreshes if expired.
    Call this at the start of each play session."""
    try:
        result = ff_auth.login()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_profile() -> str:
    """Get current player profile: energy, gold, level, XP, karma,
    equipped rod, and wallet address."""
    try:
        profile = api.get_me()
        # Extract the most useful fields
        user = profile if "username" in profile else profile.get("data", profile)
        summary = {
            "username": user.get("username"),
            "level": user.get("level"),
            "xp": user.get("xp"),
            "gold": user.get("gold"),
            "energy": user.get("energy"),
            "maxEnergy": user.get("maxEnergy"),
            "karma": user.get("karma"),
            "wallet": user.get("walletAddress"),
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Fishing
# ============================================================

@server.tool()
def fish(range_type: str = "short_range", multiplier: int = 1) -> str:
    """Execute one complete fishing session via the REST API.

    Args:
        range_type: "short_range" (1 energy), "mid_range" (2 energy),
                    or "long_range" (3 energy). Higher range = better fish.
        multiplier: Fishing multiplier (1 = normal). Costs more energy for more rewards.

    Returns fish caught, XP gained, gold value, and energy remaining."""
    try:
        token = ff_auth.get_token()
        result = fishing_client.fish_session(token, range_type, multiplier=multiplier)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def fish_batch(range_type: str = "short_range", count: int = 5,
               multiplier: int = 1) -> str:
    """Fish multiple times in sequence. Stops if energy runs out.

    Args:
        range_type: "short_range", "mid_range", or "long_range".
        count: Number of fishing sessions to attempt.
        multiplier: Fishing multiplier (1 = normal).

    Returns summary: total caught, total XP, total gold, successes/failures."""
    try:
        token = ff_auth.get_token()
        result = fishing_client.fish_batch(token, range_type, count, multiplier=multiplier)
        summary = {
            "total_casts": result["total_casts"],
            "successes": result["successes"],
            "failures": result["failures"],
            "total_xp": result["total_xp"],
            "total_gold_value": result["total_gold_value"],
        }
        if result["results"]:
            last = result["results"][-1]
            summary["last_result"] = {
                "success": last.get("success"),
                "error": last.get("error"),
                "fish": last.get("fish"),
                "player": last.get("player"),
            }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Economy
# ============================================================

@server.tool()
def sell_fish(fish_id: str, quantity: int = 1) -> str:
    """Sell a specific fish type from inventory.

    Args:
        fish_id: The fish info ID (from inventory).
        quantity: Number to sell."""
    try:
        result = api.sell_fish(fish_id, quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def sell_all_fish() -> str:
    """Sell ALL fish in inventory at once. Returns total gold earned."""
    try:
        result = api.sell_all_fish()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def buy_item(item_name: str, quantity: int = 1) -> str:
    """Buy an item from the shop by name.

    Args:
        item_name: Item name (e.g. "sushi") or item ID.
        quantity: Number to buy.

    Known items: "sushi" (restores 5 energy, costs 500 gold)."""
    try:
        item_id = ITEM_NAME_MAP.get(item_name.lower(), item_name)
        result = api.buy_item(item_id, quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def use_item(item_name: str) -> str:
    """Use a consumable item (sushi, bait, scroll, etc.).

    Args:
        item_name: Item name (e.g. "sushi") or item ID."""
    try:
        item_id = ITEM_NAME_MAP.get(item_name.lower(), item_name)
        result = api.use_item(item_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_shop() -> str:
    """List all available shop items with prices and descriptions."""
    try:
        result = api.get_shop()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_inventory() -> str:
    """Get full inventory: fish, items, rods, chests, and consumables."""
    try:
        result = api.get_inventory()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Cooking
# ============================================================

@server.tool()
def get_recipes() -> str:
    """Get today's active cooking recipes with requirements and rewards."""
    try:
        result = api.get_active_recipes()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def cook(recipe_id: str, quantity: int, fish_ids: list[str],
         shiny_fish_ids: list[str] = None) -> str:
    """Cook fish into sashimi using a recipe.

    Args:
        recipe_id: The recipe ID (from get_recipes).
        quantity: Number of times to cook.
        fish_ids: List of fish IDs to use as ingredients.
        shiny_fish_ids: Optional list of shiny fish IDs for bonus."""
    try:
        result = api.cook(recipe_id, quantity, fish_ids, shiny_fish_ids)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def sell_sashimi(sashimi_id: str, quantity: int = 1) -> str:
    """Sell sashimi for pearls.

    Args:
        sashimi_id: The sashimi ID to sell.
        quantity: Number to sell."""
    try:
        result = api.sell_sashimi(sashimi_id, quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def spin_cooking_wheel(amount: int = 1) -> str:
    """Spin the cooking wheel using pearls.

    Args:
        amount: Number of spins (each costs pearls)."""
    try:
        result = api.spin_cooking_wheel(amount)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Quests & Daily
# ============================================================

@server.tool()
def claim_daily_reward() -> str:
    """Claim today's daily login reward. Call once per day."""
    try:
        result = api.claim_daily_reward()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_quests() -> str:
    """Get all quests (daily, user) with their current status and progress."""
    try:
        result = api.get_user_quests()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def claim_quest(quest_id: str) -> str:
    """Claim a completed quest's reward.

    Args:
        quest_id: The quest ID to claim (from get_quests)."""
    try:
        result = api.claim_quest(quest_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def verify_social_quest(quest_id: str) -> str:
    """Complete a social quest (e.g. follow on Twitter, join Discord).

    Args:
        quest_id: The social quest ID."""
    try:
        result = api.verify_social_quest(quest_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def spin_daily_wheel() -> str:
    """Spin the daily quest reward wheel (if eligible)."""
    try:
        result = api.spin_daily_wheel()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Equipment
# ============================================================

@server.tool()
def equip_rod(rod_id: str) -> str:
    """Equip a fishing rod.

    Args:
        rod_id: The rod ID to equip (from inventory)."""
    try:
        result = api.equip_rod(rod_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def repair_rod(rod_id: str) -> str:
    """Repair a damaged fishing rod.

    Args:
        rod_id: The rod ID to repair."""
    try:
        result = api.repair_rod(rod_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def collect_pet_fish() -> str:
    """Collect all accumulated fish from your pets."""
    try:
        result = api.collect_pet_fish()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Accessories (Upgrades)
# ============================================================

@server.tool()
def get_accessories() -> str:
    """Get all accessories with current levels and available upgrade points.

    Accessories: Rod Handle (energy save), Reel (capture zone), Lucky Charm (item drops),
    Icebox (gold bonus), Fishing Manual (XP bonus), Cutting Board (bait save)."""
    try:
        result = api.get_accessories()
        if isinstance(result, dict) and "accessories" in result:
            summary = {
                "available_upgrade_points": result.get("availableUpgradePoint", 0),
                "accessories": [],
            }
            for acc in result["accessories"]:
                current_level = acc.get("currentLevel", 0)
                effects = acc.get("effects", [])
                current_effect = next(
                    (e["effect"] for e in effects if e["level"] == current_level), 0
                )
                next_effect = next(
                    (e for e in effects if e["level"] == current_level + 1), None
                )
                summary["accessories"].append({
                    "id": acc.get("accessoryId"),
                    "name": acc.get("name"),
                    "description": acc.get("description"),
                    "level": f"{current_level}/{acc.get('maxLevel', 10)}",
                    "current_effect": f"{current_effect:.0%}",
                    "next_upgrade_cost": next_effect["pointsRequired"] if next_effect else "MAX",
                    "next_effect": f"{next_effect['effect']:.0%}" if next_effect else "MAX",
                })
            return json.dumps(summary, indent=2)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def upgrade_accessory(accessory_name: str) -> str:
    """Upgrade an accessory by one level using upgrade points.

    Args:
        accessory_name: Name or ID of the accessory. Names: "Rod Handle", "Reel",
            "Lucky Charm", "Icebox", "Fishing Manual", "Cutting Board"."""
    try:
        # Resolve name to ID
        accessories = api.get_accessories()
        acc_list = accessories.get("accessories", [])
        target = None
        for acc in acc_list:
            if (accessory_name.lower() in acc.get("name", "").lower()
                    or accessory_name == acc.get("accessoryId")):
                target = acc
                break
        if not target:
            return json.dumps({"error": f"Accessory '{accessory_name}' not found",
                              "available": [a["name"] for a in acc_list]})

        result = api.upgrade_accessory(target["accessoryId"])
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Diving
# ============================================================

@server.tool()
def get_diving_config() -> str:
    """Get diving game configuration: board sizes, coral rewards, ticket costs.
    Diving requires level 30+."""
    try:
        result = api.get_diving_config()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_diving_state() -> str:
    """Check current diving state — whether a dive is in progress."""
    try:
        result = api.get_diving_state()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def buy_diving_ticket(quantity: int = 1) -> str:
    """Buy a gold diving ticket using gold.

    Args:
        quantity: Number of tickets to buy (default 1).

    Only Regular (gold-cost) tickets can be bought via API.
    Premium (RON) and Token (FISH) tickets require on-chain transactions."""
    try:
        result = api.buy_diving_ticket_with_gold("Regular", quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def dive(max_picks: int = 0, multiplier: str = "X1") -> str:
    """Execute a full diving session: use ticket → start → play WebSocket game.

    You must have already bought a gold diving ticket (buy_diving_ticket).
    Requires level 30+.

    Args:
        max_picks: Max cells to reveal before cashing out (0 = play until game ends).
        multiplier: "X1" (normal, 1 ticket) or "X10" (10x rewards, uses 10 tickets).

    Returns dive results: cells revealed, rewards collected, board data."""
    try:
        # Step 1: Use the ticket
        use_result = api.use_diving_ticket("Regular", multiplier)
        if isinstance(use_result, dict) and use_result.get("code") == 400:
            return json.dumps({"error": use_result.get("message", "Failed to use ticket")})

        # Step 2: Start the dive (REST)
        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            return json.dumps({"error": start_result.get("message", "Failed to start dive")})

        # Step 3: Play via WebSocket
        token = ff_auth.get_token()
        result = diving_client.dive_session(token, max_picks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_diving_jackpots() -> str:
    """Get current diving jackpot values for all dive types."""
    try:
        result = api.get_diving_jackpots()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Leaderboard & Stats
# ============================================================

@server.tool()
def get_leaderboard(rank_type: str = "General") -> str:
    """View leaderboard rankings.

    Args:
        rank_type: "General", "Cooking", or "Frenzy_point"."""
    try:
        result = api.get_leaderboard(rank_type)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@server.tool()
def get_session_stats() -> str:
    """Get this agent's local performance stats:
    lifetime totals, recent sessions, and efficiency metrics."""
    try:
        lifetime = state.get_lifetime_stats()
        recent = state.get_session_history(5)
        return json.dumps({
            "lifetime": lifetime,
            "recent_sessions": recent,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    server.run(transport="stdio")
