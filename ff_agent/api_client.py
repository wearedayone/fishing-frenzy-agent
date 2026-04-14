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


def use_item(item_id: str) -> dict:
    """Use a consumable item (sushi, bait, scroll)."""
    from . import state
    user_id = state.get_auth("user_id")
    return _request("GET", f"/items/{item_id}/use?userId={user_id}")


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


# --- Leaderboard ---

def get_leaderboard(rank_type: str = "General") -> dict:
    """Get leaderboard rankings."""
    return _request("GET", f"/rank/type?rankType={rank_type}")
