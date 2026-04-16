"""Shared test utilities."""

import json
import time


def parse_tool_result(result_str: str) -> dict:
    """Parse a JSON string returned by an MCP tool."""
    return json.loads(result_str)


def wait_for_cooldown(seconds: float = 11.0):
    """Wait for the server fishing cooldown period (10s + margin)."""
    time.sleep(seconds)


def get_current_profile() -> dict:
    """Fetch and return the current player profile dict."""
    from ff_agent import api_client as api

    profile = api.get_me()
    if "username" in profile:
        return profile
    return profile.get("data", profile)


def get_energy() -> int:
    """Return current energy from profile."""
    return get_current_profile().get("energy", 0)


def get_gold() -> float:
    """Return current gold from profile."""
    return get_current_profile().get("gold", 0)


def get_max_energy() -> int:
    """Return max energy from profile."""
    return get_current_profile().get("maxEnergy", 30)


def fish_until_inventory(count: int = 5, range_type: str = "short_range") -> int:
    """Fish repeatedly until we have at least `count` successful catches.

    Returns the number of successful catches. Stops early if energy runs out.
    """
    from ff_agent import fishing_client, auth

    token = auth.get_token()
    successes = 0

    for i in range(count * 2):  # Allow extra attempts for escapes
        if successes >= count:
            break
        if get_energy() < 1:
            break
        if i > 0:
            wait_for_cooldown()
        result = fishing_client.fish_session(token, range_type)
        if result.get("success"):
            successes += 1

    return successes
