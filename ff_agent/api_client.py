"""REST API client for Fishing Frenzy with auto-auth-refresh."""

import httpx
from . import auth

BASE_URL = "https://api.fishingfrenzy.co/v1"


def _headers() -> dict:
    token = auth.get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "https://fishingfrenzy.co",
        "Referer": "https://fishingfrenzy.co/",
    }


def _request(method: str, path: str, **kwargs) -> dict:
    """Make an authenticated request with auto-retry on 401."""
    with httpx.Client(timeout=15) as client:
        resp = client.request(
            method, f"{BASE_URL}{path}", headers=_headers(), **kwargs
        )
        if resp.status_code == 401:
            auth.login()
            resp = client.request(
                method, f"{BASE_URL}{path}", headers=_headers(), **kwargs
            )
        # Return the JSON response even for 4xx errors (game API uses 400 for
        # business logic like "already claimed" or "not enough energy")
        return resp.json()


# --- Profile ---

def get_me() -> dict:
    """Get current user profile (energy, gold, level, XP, etc.)."""
    return _request("GET", "/users/me")


def get_general_config() -> dict:
    """Get game general configuration."""
    return _request("GET", "/general-config")


# --- Inventory ---

def get_inventory() -> dict:
    """Get full inventory (fish, items, rods, chests)."""
    return _request("GET", "/inventory")


def get_fish_inventory() -> dict:
    """Get fish-only inventory."""
    return _request("GET", "/inventory/fish")


# --- Fishing Economy ---

def sell_fish(fish_id: str, quantity: int = 1) -> dict:
    """Sell a specific fish type."""
    return _request("POST", "/fish/sell",
                     json={"fishInfoId": fish_id, "quantity": quantity})


def sell_all_fish() -> dict:
    """Sell all fish in inventory."""
    return _request("POST", "/fish/sellAll")


# --- Shop & Items ---

def get_shop() -> dict:
    """Get available shop items."""
    return _request("GET", "/items")


def buy_item(item_id: str, quantity: int = 1) -> dict:
    """Buy an item from the shop."""
    from . import state
    user_id = state.get_auth("user_id")
    return _request("GET", f"/items/{item_id}/buy?userId={user_id}&quantity={quantity}")


def use_item(item_id: str, quantity: int = 1) -> dict:
    """Use a consumable item (sushi, bait, scroll)."""
    from . import state
    user_id = state.get_auth("user_id")
    return _request("GET", f"/items/{item_id}/use?userId={user_id}&quantity={quantity}")


# --- Cooking ---

def get_active_recipes() -> dict:
    """Get today's active cooking recipes."""
    return _request("GET", "/cooking-recipes/active")


def cook(recipe_id: str, quantity: int, fish_ids: list,
         shiny_fish_ids: list = None) -> dict:
    """Cook fish into sashimi."""
    return _request("POST", "/cooking-recipes/claim", json={
        "cookingRecipeId": recipe_id,
        "quantity": quantity,
        "fishs": fish_ids,
        "shinyFishs": shiny_fish_ids or [],
    })


def sell_sashimi(sashimi_id: str, quantity: int = 1) -> dict:
    """Sell sashimi for pearls."""
    return _request("POST", "/sashimi/sell",
                     json={"sashimiId": sashimi_id, "quantity": quantity})


def spin_cooking_wheel(amount: int = 1) -> dict:
    """Spin the cooking wheel using pearls."""
    return _request("GET", f"/cooking-recipes/spin-wheel?amount={amount}")


# --- Quests & Daily ---

def claim_daily_reward() -> dict:
    """Claim daily login reward."""
    return _request("GET", "/daily-rewards/claim")


def get_user_quests() -> dict:
    """Get all user quests with status."""
    return _request("GET", "/user-quests")


def claim_quest(quest_id: str) -> dict:
    """Claim a completed quest reward."""
    return _request("POST", f"/user-quests/{quest_id}/claim")


def get_social_quests() -> dict:
    """Get social quests."""
    return _request("GET", "/social-quests")


def verify_social_quest(quest_id: str) -> dict:
    """Complete/verify a social quest."""
    return _request("POST", f"/social-quests/{quest_id}/verify")


def spin_daily_wheel() -> dict:
    """Spin the daily quest wheel."""
    return _request("POST", "/user-quests/daily-quest/wheel/spin")


# --- Equipment ---

def equip_rod(rod_id: str) -> dict:
    """Equip a fishing rod."""
    return _request("POST", f"/rods/{rod_id}/equip")


def repair_rod(rod_id: str) -> dict:
    """Repair a damaged rod."""
    return _request("POST", "/rods/repair-rod", json={"userRodId": rod_id})


def collect_pet_fish() -> dict:
    """Collect all fish from pets."""
    return _request("GET", "/pets/collect/all")


# --- Diving ---

def get_diving_config() -> dict:
    """Get diving game configuration (board sizes, coral rewards, ticket costs)."""
    return _request("GET", "/diving/game-config")


def get_diving_state() -> dict:
    """Get current diving state (are we mid-dive?)."""
    return _request("GET", "/diving/state")


def get_diving_jackpots() -> dict:
    """Get current diving jackpot values."""
    return _request("GET", "/diving/jackpot-values")


def buy_diving_ticket_with_gold(diving_type: str = "Regular",
                                 quantity: int = 1) -> dict:
    """Buy a diving ticket with gold.

    Args:
        diving_type: "Regular" (gold cost).
        quantity: Number of tickets to buy.
    """
    return _request("POST", "/trading/diving-ticket-purchase-transactions",
                     json={"type": diving_type, "quantity": quantity,
                           "transactionHash": None})


def use_diving_ticket(diving_type: str = "Regular",
                       mode: str = "X1") -> dict:
    """Use a diving ticket to prepare a dive.

    Args:
        diving_type: "Regular", "Premium", or "Token".
        mode: "X1" (normal) or "X10" (10x multiplier, uses 10 tickets).
    """
    return _request("POST", "/diving/use-ticket",
                     json={"divingType": diving_type, "mode": mode})


def start_diving() -> dict:
    """Start the diving session (after ticket is used). Triggers WebSocket gameplay."""
    return _request("POST", "/diving/start")


# --- Accessories (Upgrades) ---

def get_accessories() -> dict:
    """Get all accessories with current levels, effects, and available upgrade points."""
    return _request("GET", "/accessories")


def upgrade_accessory(accessory_id: str) -> dict:
    """Upgrade an accessory by one level (costs upgrade points).

    Args:
        accessory_id: The accessory ID to upgrade.
    """
    return _request("POST", f"/accessories/{accessory_id}/upgrade")


def reset_upgrade_points() -> dict:
    """Reset all upgrade points (respec)."""
    return _request("POST", "/accessories/reset-available-upgrade-point")


# --- Chests ---

def get_inventory_chests() -> dict:
    """Get all chests in inventory."""
    return _request("GET", "/inventory/chests")


def open_chest(chest_id: str) -> dict:
    """Open a single non-NFT chest."""
    return _request("GET", f"/chests/{chest_id}/open")


def open_chests_batch(chest_ids: list) -> dict:
    """Open multiple non-NFT chests at once."""
    return _request("POST", "/chests/open-batch", json={"chests": chest_ids})


# --- Leaderboard ---

def get_leaderboard(rank_type: str = "General") -> dict:
    """Get leaderboard rankings."""
    return _request("GET", f"/rank/type?rankType={rank_type}")
