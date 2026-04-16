"""FastMCP server for Fishing Frenzy Agent — exposes game actions as tools."""

import json
import os
import sys

# Ensure the parent directory is in the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP  # from pip package 'mcp'

from ff_agent import auth as ff_auth
from ff_agent import api_client as api
from ff_agent import fishing_client
from ff_agent import diving_client
from ff_agent import state
from ff_agent import strategy as strat

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
# Error Classification & Verification Helpers
# ============================================================

def _game_error(action: str, error, api_response: dict = None) -> dict:
    """Build a structured, actionable error response."""
    error_str = str(error)
    error_lower = error_str.lower()

    # Classify the error
    if isinstance(error, ff_auth.AuthError) or "401" in error_str or "unauthorized" in error_lower:
        error_type = "auth"
        suggestion = "Call login() to re-authenticate"
    elif any(s in error_lower for s in ("timeout", "timed out", "connection")):
        error_type = "transient"
        suggestion = "Try again in a few seconds"
    elif any(s in error_lower for s in ("not enough", "insufficient", "low energy", "low gold")):
        error_type = "resource_depleted"
        if "energy" in error_lower:
            suggestion = "Buy and use sushi to restore 5 energy (costs 500 gold)"
        else:
            suggestion = "Fish and sell to earn more gold"
    elif any(s in error_lower for s in ("already", "claimed", "completed")):
        error_type = "game_logic"
        suggestion = "Already done — skip and continue to next action"
    elif any(s in error_lower for s in ("not found", "invalid", "does not exist")):
        error_type = "blocked"
        suggestion = "Check the ID is correct (use get_inventory or get_quests to find valid IDs)"
    elif any(s in error_lower for s in ("level", "unlock", "requirement")):
        error_type = "blocked"
        suggestion = "Level requirement not met — keep fishing to level up"
    elif "cooldown" in error_lower or "10 seconds" in error_lower:
        error_type = "game_logic"
        suggestion = "Wait for the 10-second fishing cooldown before casting again"
    else:
        error_type = "unknown"
        suggestion = "Check the error message and try a different approach"

    # Also classify from API response body
    if api_response and isinstance(api_response, dict):
        code = api_response.get("code", api_response.get("statusCode"))
        msg = api_response.get("message", "")
        if code and code != 200:
            error_str = msg or error_str
            msg_lower = msg.lower() if msg else ""
            if any(s in msg_lower for s in ("not enough", "insufficient")):
                error_type = "resource_depleted"
                if "energy" in msg_lower:
                    suggestion = "Buy and use sushi to restore 5 energy (costs 500 gold)"
                elif "gold" in msg_lower:
                    suggestion = "Fish and sell to earn more gold"
                else:
                    suggestion = "Check resource requirements"
            elif any(s in msg_lower for s in ("already", "claimed")):
                error_type = "game_logic"
                suggestion = "Already done — skip and continue"

    return {
        "success": False,
        "error_type": error_type,
        "error": error_str,
        "suggestion": suggestion,
        "action": action,
    }


def _tool_error(e, api_response=None):
    """Build game error, auto-detecting the calling tool name."""
    action = sys._getframe(1).f_code.co_name
    return _game_error(action, e, api_response)


def _get_profile_snapshot() -> dict | None:
    """Quick profile snapshot for verification gates. Returns None on failure."""
    try:
        profile = api.get_me()
        if not isinstance(profile, dict):
            return None
        user = profile if "gold" in profile else profile.get("data", profile)
        if not isinstance(user, dict):
            return None
        return {
            "gold": user.get("gold", 0),
            "energy": user.get("energy", 0),
            "level": user.get("level", 0),
            "xp": user.get("exp", user.get("xp", 0)),
        }
    except Exception:
        return None


def _build_verification(before: dict | None, after: dict | None) -> dict | None:
    """Build a verification dict from before/after snapshots. Returns None if either failed."""
    if before is None or after is None:
        return None
    return {
        "gold_before": before.get("gold", 0),
        "gold_after": after.get("gold", 0),
        "gold_change": after.get("gold", 0) - before.get("gold", 0),
        "energy_before": before.get("energy", 0),
        "energy_after": after.get("energy", 0),
        "energy_change": after.get("energy", 0) - before.get("energy", 0),
        "xp_before": before.get("xp", 0),
        "xp_after": after.get("xp", 0),
        "xp_change": after.get("xp", 0) - before.get("xp", 0),
    }


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
        return json.dumps(_game_error("setup_account", e))


@server.tool()
def login() -> str:
    """Authenticate and get a fresh JWT token. Auto-refreshes if expired.
    Call this at the start of each play session."""
    try:
        result = ff_auth.login()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_game_error("login", e))


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
        return json.dumps(_tool_error(e))


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
        if result.get("success"):
            state.log_action("fish", params={"range": range_type, "multiplier": multiplier},
                             result={"fish": result.get("fish", {}).get("name")})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_game_error("fish", e))


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
        # Build per-cast results for cast-by-cast display
        casts = []
        for r in result.get("results", []):
            cast = {
                "success": r.get("success", False),
                "range": r.get("range", range_type),
            }
            if r.get("success"):
                fish = r.get("fish", {})
                cast["fish_name"] = fish.get("name", "Unknown")
                cast["quality"] = fish.get("quality", 0)
                cast["xp"] = fish.get("xp_gain", 0)
                cast["gold"] = fish.get("sell_price", 0)
                cast["new_unlocks"] = r.get("new_unlocks", [])
                player = r.get("player", {})
                cast["level"] = player.get("level")
                cast["energy"] = player.get("energy_remaining")
            else:
                cast["error"] = r.get("error", "Unknown error")
            casts.append(cast)

        summary = {
            "total_casts": result["total_casts"],
            "successes": result["successes"],
            "failures": result["failures"],
            "total_xp": result["total_xp"],
            "total_gold_value": result["total_gold_value"],
            "casts": casts,
        }
        state.log_action("fish_batch", params={"range": range_type, "count": count},
                         result={"successes": result["successes"], "total_gold": result["total_gold_value"]})
        return json.dumps(summary, indent=2)
    except Exception as e:
        return json.dumps(_game_error("fish_batch", e))


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
        return json.dumps(_game_error("sell_fish", e))


@server.tool()
def sell_all_fish() -> str:
    """Sell ALL fish in inventory at once. Returns total gold earned with verification."""
    try:
        before = _get_profile_snapshot()
        result = api.sell_all_fish()
        after = _get_profile_snapshot()
        verified = _build_verification(before, after)
        result_out = {"result": result}
        if verified:
            result_out["verified"] = verified
        state.log_action("sell_all_fish", result=result,
                         gold_before=before.get("gold") if before else None,
                         gold_after=after.get("gold") if after else None)
        return json.dumps(result_out, indent=2)
    except Exception as e:
        return json.dumps(_game_error("sell_all_fish", e))


@server.tool()
def buy_item(item_name: str, quantity: int = 1, auto_use: bool = True) -> str:
    """Buy an item from the shop by name. For consumables like sushi, auto-uses after buying.

    Args:
        item_name: Item name (e.g. "sushi") or item ID.
        quantity: Number to buy.
        auto_use: If True, automatically use consumable items after buying (default: True).

    Known items: "sushi" (restores 5 energy, costs 500 gold)."""
    try:
        item_id = ITEM_NAME_MAP.get(item_name.lower(), item_name)
        before = _get_profile_snapshot()
        buy_result = api.buy_item(item_id, quantity)
        if buy_result.get("code") and buy_result["code"] != 200:
            return json.dumps(_game_error("buy_item", buy_result.get("message", "Purchase failed"), buy_result))

        if auto_use:
            use_result = api.use_item(item_id, quantity)
            after = _get_profile_snapshot()
            verified = _build_verification(before, after)
            result_out = {
                "bought": quantity,
                "item": item_name,
                "used": True,
                "result": use_result,
            }
            if verified:
                result_out["verified"] = verified
            state.log_action("buy_item", params={"item": item_name, "quantity": quantity, "auto_use": True},
                             gold_before=before.get("gold") if before else None,
                             gold_after=after.get("gold") if after else None,
                             energy_before=before.get("energy") if before else None,
                             energy_after=after.get("energy") if after else None)
            return json.dumps(result_out, indent=2)

        after = _get_profile_snapshot()
        verified = _build_verification(before, after)
        result_out = {"bought": quantity, "item": item_name, "used": False, "result": buy_result}
        if verified:
            result_out["verified"] = verified
        state.log_action("buy_item", params={"item": item_name, "quantity": quantity, "auto_use": False},
                         gold_before=before.get("gold") if before else None,
                         gold_after=after.get("gold") if after else None)
        return json.dumps(result_out, indent=2)
    except Exception as e:
        return json.dumps(_game_error("buy_item", e))


@server.tool()
def use_item(item_name: str, quantity: int = 1) -> str:
    """Use a consumable item (sushi, bait, scroll, etc.) from inventory.

    Args:
        item_name: Item name (e.g. "sushi") or item ID.
        quantity: Number to use."""
    try:
        item_id = ITEM_NAME_MAP.get(item_name.lower(), item_name)
        result = api.use_item(item_id, quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def get_shop() -> str:
    """List all available shop items with prices and descriptions."""
    try:
        result = api.get_shop()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def get_inventory() -> str:
    """Get full inventory: fish, items, rods, chests, and consumables."""
    try:
        result = api.get_inventory()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


@server.tool()
def spin_cooking_wheel(amount: int = 1) -> str:
    """Spin the cooking wheel using pearls.

    Args:
        amount: Number of spins (each costs pearls)."""
    try:
        result = api.spin_cooking_wheel(amount)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# Quests & Daily
# ============================================================

@server.tool()
def claim_daily_reward() -> str:
    """Claim today's daily login reward. Call once per day."""
    try:
        before = _get_profile_snapshot()
        result = api.claim_daily_reward()
        after = _get_profile_snapshot()
        verified = _build_verification(before, after)
        result_out = {"result": result}
        if verified:
            result_out["verified"] = verified
        state.log_action("claim_daily_reward", result=result,
                         gold_before=before.get("gold") if before else None,
                         gold_after=after.get("gold") if after else None)
        return json.dumps(result_out, indent=2)
    except Exception as e:
        return json.dumps(_game_error("claim_daily_reward", e))


@server.tool()
def get_quests() -> str:
    """Get all quests (daily, user) with their current status and progress."""
    try:
        result = api.get_user_quests()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def claim_quest(quest_id: str) -> str:
    """Claim a completed quest's reward.

    Args:
        quest_id: The quest ID to claim (from get_quests)."""
    try:
        before = _get_profile_snapshot()
        result = api.claim_quest(quest_id)
        after = _get_profile_snapshot()
        verified = _build_verification(before, after)
        result_out = {"result": result}
        if verified:
            result_out["verified"] = verified
        state.log_action("claim_quest", params={"quest_id": quest_id}, result=result,
                         gold_before=before.get("gold") if before else None,
                         gold_after=after.get("gold") if after else None)
        return json.dumps(result_out, indent=2)
    except Exception as e:
        return json.dumps(_game_error("claim_quest", e))


@server.tool()
def verify_social_quest(quest_id: str) -> str:
    """Complete a social quest (e.g. follow on Twitter, join Discord).

    Args:
        quest_id: The social quest ID."""
    try:
        result = api.verify_social_quest(quest_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def spin_daily_wheel() -> str:
    """Spin the daily quest reward wheel (if eligible)."""
    try:
        result = api.spin_daily_wheel()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


@server.tool()
def repair_rod(rod_id: str) -> str:
    """Repair a damaged fishing rod.

    Args:
        rod_id: The rod ID to repair."""
    try:
        result = api.repair_rod(rod_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def collect_pet_fish() -> str:
    """Collect all accumulated fish from your pets."""
    try:
        result = api.collect_pet_fish()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
                effects = acc.get("effects") or []
                current_effect = next(
                    (e.get("effect", 0) for e in effects if isinstance(e, dict) and e.get("level") == current_level), 0
                )
                next_effect = next(
                    (e for e in effects if isinstance(e, dict) and e.get("level") == current_level + 1), None
                )
                acc_info = {
                    "id": acc.get("accessoryId"),
                    "name": acc.get("name"),
                    "description": acc.get("description"),
                    "level": f"{current_level}/{acc.get('maxLevel', 10)}",
                }
                if isinstance(current_effect, (int, float)):
                    acc_info["current_effect"] = f"{current_effect:.0%}"
                else:
                    acc_info["current_effect"] = str(current_effect)
                if next_effect and isinstance(next_effect, dict):
                    acc_info["next_upgrade_cost"] = next_effect.get("pointsRequired", "?")
                    effect_val = next_effect.get("effect")
                    acc_info["next_effect"] = f"{effect_val:.0%}" if isinstance(effect_val, (int, float)) else str(effect_val)
                else:
                    acc_info["next_upgrade_cost"] = "MAX"
                    acc_info["next_effect"] = "MAX"
                summary["accessories"].append(acc_info)
            return json.dumps(summary, indent=2)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


@server.tool()
def get_diving_state() -> str:
    """Check current diving state — whether a dive is in progress."""
    try:
        result = api.get_diving_state()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


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
            return json.dumps(_game_error("dive", use_result.get("message", "Failed to use ticket"), use_result))

        # Step 2: Start the dive (REST)
        start_result = api.start_diving()
        if isinstance(start_result, dict) and start_result.get("code") in (400, 404):
            return json.dumps(_game_error("dive", start_result.get("message", "Failed to start dive"), start_result))

        # Step 3: Play via WebSocket
        token = ff_auth.get_token()
        result = diving_client.dive_session(token, max_picks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def get_diving_jackpots() -> str:
    """Get current diving jackpot values for all dive types."""
    try:
        result = api.get_diving_jackpots()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# Chests
# ============================================================

@server.tool()
def get_chests() -> str:
    """Get all chests in your inventory with types and quantities."""
    try:
        result = api.get_inventory_chests()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


def _extract_chest_ids(inv) -> list[str]:
    """Extract chest IDs from any inventory response format."""
    ids = []
    items = []
    if isinstance(inv, list):
        items = inv
    elif isinstance(inv, dict):
        # Try all common response shapes
        for key in ("chests", "data", "items", "inventory"):
            candidate = inv.get(key)
            if isinstance(candidate, list):
                items = candidate
                break
        if not items:
            # Single chest object
            cid = inv.get("_id") or inv.get("id")
            if cid:
                return [str(cid)]
    for c in items:
        if isinstance(c, dict):
            cid = c.get("_id") or c.get("id")
            if cid:
                ids.append(str(cid))
        elif isinstance(c, str):
            ids.append(c)
    return ids


@server.tool()
def open_chests(chest_ids: list[str] = None) -> str:
    """Open chests from inventory. Opens all non-NFT chests if no IDs specified.

    Args:
        chest_ids: Optional list of specific chest IDs to open.
                   If empty/None, fetches inventory and opens all available chests."""
    try:
        if not chest_ids:
            # Fetch all chests and open them
            inv = api.get_inventory_chests()
            chest_ids = _extract_chest_ids(inv)

        if not chest_ids:
            return json.dumps({"message": "No chests to open"})

        if len(chest_ids) == 1:
            result = api.open_chest(chest_ids[0])
        else:
            result = api.open_chests_batch(chest_ids)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# Fish Collection & Aquarium
# ============================================================

@server.tool()
def get_fish_collection() -> str:
    """View full fish collection progress — all species, counts, and milestones."""
    try:
        result = api.get_fish_collection()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def collect_fish(fish_id: str, quantity: int = 1) -> str:
    """Collect a specific fish into the aquarium. PERMANENTLY consumes the fish from inventory.

    Args:
        fish_id: The fish info ID (from inventory).
        quantity: Number to collect."""
    try:
        result = api.collect_fish(fish_id, quantity)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def collect_all_non_nft_fish() -> str:
    """Collect ALL non-NFT fish into the aquarium at once.
    PERMANENTLY consumes all non-NFT fish from inventory.
    Use when you want to maximize collection EXP quickly."""
    try:
        result = api.collect_all_fish()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def get_collection_overview() -> str:
    """Get aquarium overview: collection levels, total EXP, and milestone progress."""
    try:
        result = api.get_collection_overview()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def claim_collection_rewards() -> str:
    """Claim any available aquarium level milestone rewards."""
    try:
        result = api.claim_collection_overview_reward()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def claim_fish_collection_reward(collection_id: str) -> str:
    """Claim reward for a specific fish collection entry.

    Args:
        collection_id: The collection entry ID (from get_fish_collection)."""
    try:
        result = api.claim_collection_reward(collection_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def admire_aquarium() -> str:
    """Admire a random top-100 Prestige aquarium for 20 gold. Once per day.
    Earns collection EXP and counts toward daily quests."""
    try:
        result = api.admire_aquarium()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# On-Chain / Blockchain
# ============================================================

@server.tool()
def get_wallet_balances() -> str:
    """Get on-chain wallet balances: RON, FISH, and xFISH.
    Reads directly from the Ronin blockchain."""
    try:
        from ff_agent import chain
        ron = chain.get_ron_balance()
        fish = chain.get_fish_balance()
        xfish = chain.get_xfish_balance()
        return json.dumps({
            "RON": round(ron, 6),
            "FISH": round(fish, 2),
            "xFISH": round(xfish, 2),
        }, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def onchain_checkin() -> str:
    """Perform the daily on-chain check-in. Costs a small RON fee.
    Different from claim_daily_reward — this is the blockchain check-in
    that awards Karma and streak bonuses."""
    try:
        from ff_agent import chain
        result = chain.daily_checkin()
        state.log_action("onchain_checkin", result=result)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def mint_leaderboard_chests(chest_token_ids: list[int]) -> str:
    """Mint leaderboard chests on-chain so they can be opened.

    Leaderboard chests exist as NFTs that must be minted before opening.
    After minting, use open_chests() to open them.

    Args:
        chest_token_ids: List of chest token IDs to mint (from get_chests)."""
    try:
        from ff_agent import chain
        result = chain.mint_chests(chest_token_ids)
        state.log_action("mint_leaderboard_chests",
                         params={"chest_token_ids": chest_token_ids},
                         result=result)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def stake_fish_tokens(amount: float, duration_months: int = 1) -> str:
    """Stake FISH tokens for Karma. Requires FISH in wallet.

    Args:
        amount: Amount of FISH to stake (e.g. 100.0).
        duration_months: Lock duration in months (1, 3, 6, or 12).
            Longer durations earn more Karma."""
    try:
        from ff_agent import chain
        result = chain.stake_fish(amount, duration_months)
        state.log_action("stake_fish_tokens",
                         params={"amount": amount, "duration_months": duration_months},
                         result=result)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# Session & Heartbeat
# ============================================================

@server.tool()
def start_play_session(strategy: str = "balanced") -> str:
    """Start a tracked play session. Call at the beginning of /play.

    Args:
        strategy: The strategy being used ("balanced", "grind", "efficiency").

    Returns the session ID for tracking."""
    try:
        session_id = state.start_session(strategy)
        return json.dumps({"session_id": session_id, "strategy": strategy, "status": "started"})
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def end_play_session(session_id: int, fish_caught: int = 0,
                     gold_earned: float = 0, xp_earned: int = 0,
                     energy_spent: int = 0) -> str:
    """End a tracked play session and record final stats.

    Args:
        session_id: From start_play_session.
        fish_caught: Total fish caught this session.
        gold_earned: Total gold earned this session.
        xp_earned: Total XP earned this session.
        energy_spent: Total energy spent this session."""
    try:
        state.update_session(session_id, fish_caught, gold_earned, xp_earned, energy_spent)
        state.end_session(session_id)
        lifetime = state.get_lifetime_stats()
        return json.dumps({
            "session_id": session_id,
            "status": "ended",
            "lifetime": lifetime,
        }, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


# ============================================================
# Strategy Advice
# ============================================================

def _parse_config() -> strat.StrategyConfig:
    """Parse CONFIG.md into a StrategyConfig. Falls back to balanced defaults."""
    import re
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CONFIG.md")
    try:
        with open(config_path) as f:
            content = f.read()
    except FileNotFoundError:
        return strat.STRATEGY_DEFAULTS["balanced"]

    def _val(key, default=""):
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else default

    strategy_name = _val("STRATEGY", "balanced")
    base = strat.STRATEGY_DEFAULTS.get(strategy_name, strat.STRATEGY_DEFAULTS["balanced"])

    return strat.StrategyConfig(
        strategy=strategy_name,
        sushi_buy_threshold=float(_val("SUSHI_BUY_THRESHOLD", str(base.sushi_buy_threshold))),
        gold_reserve=float(_val("GOLD_RESERVE", str(base.gold_reserve))),
        diving_gold_threshold=float(_val("DIVING_GOLD_THRESHOLD", str(base.diving_gold_threshold))),
        fishing_strategy=_val("FISHING_STRATEGY", base.fishing_strategy),
        fish_disposal=_val("FISH_DISPOSAL", base.fish_disposal),
        max_sushi_per_session=int(_val("MAX_SUSHI_PER_SESSION", str(base.max_sushi_per_session))),
        use_multiplier=_val("USE_MULTIPLIER", "false").lower() == "true",
        dive_risk=_val("DIVE_RISK", base.dive_risk),
        dive_max_picks=int(_val("DIVE_MAX_PICKS", str(base.dive_max_picks))),
        upgrade_order=_val("UPGRADE_ORDER", base.upgrade_order),
        cook_before_sell=_val("COOK_BEFORE_SELL", "true").lower() == "true",
        spin_cooking_wheel=_val("SPIN_COOKING_WHEEL", "true").lower() == "true",
    )


@server.tool()
def get_strategy_advice(gold: float = 0, energy: int = 0, level: int = 1,
                        has_bait_medium: bool = False, has_bait_big: bool = False,
                        has_recipe_match: bool = False, sushi_bought: int = 0) -> str:
    """Get strategy recommendations based on current game state and CONFIG.md settings.

    Pass your current state to get concrete decisions: which range to fish,
    whether to buy sushi, whether to dive, what to do with fish, and which
    accessory to upgrade next.

    Args:
        gold: Current gold balance.
        energy: Current energy.
        level: Player level.
        has_bait_medium: Whether Medium Bait is in inventory.
        has_bait_big: Whether Big Bait is in inventory.
        has_recipe_match: Whether current fish match an active recipe.
        sushi_bought: Number of sushi already bought this session."""
    try:
        config = _parse_config()
        game_state = strat.GameState(
            gold=gold, energy=energy, level=level,
            has_bait_medium=has_bait_medium, has_bait_big=has_bait_big,
            has_recipe_match=has_recipe_match,
            sushi_bought_this_session=sushi_bought,
        )

        advice = {
            "strategy": config.strategy,
            "fishing_range": strat.get_fishing_range(game_state, config),
            "should_buy_sushi": strat.should_buy_sushi(game_state, config),
            "should_dive": strat.should_dive(game_state, config),
            "fish_disposal": strat.get_fish_disposal_action(game_state, config).value,
            "dive_max_picks": strat.get_dive_max_picks(config),
            "thresholds": {
                "sushi_buy_at": config.sushi_buy_threshold + config.gold_reserve,
                "dive_at": config.diving_gold_threshold + config.gold_reserve,
                "gold_reserve": config.gold_reserve,
            },
        }
        return json.dumps(advice, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


@server.tool()
def get_next_upgrade_advice() -> str:
    """Get which accessory to upgrade next based on strategy and current levels.

    Reads CONFIG.md strategy and fetches current accessory levels from the game API."""
    try:
        config = _parse_config()
        accessories = api.get_accessories()
        acc_list = accessories.get("accessories", [])

        current_levels = {}
        max_levels = {}
        for acc in acc_list:
            name = acc.get("name", "")
            current_levels[name] = acc.get("currentLevel", 0)
            max_levels[name] = acc.get("maxLevel", 10)

        recommendation = strat.get_next_upgrade(config, current_levels, max_levels)
        available_points = accessories.get("availableUpgradePoint", 0)

        result = {
            "recommended_upgrade": recommendation,
            "available_points": available_points,
            "can_upgrade": recommendation is not None and available_points > 0,
            "current_levels": current_levels,
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


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
        return json.dumps(_tool_error(e))


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    server.run(transport="stdio")
