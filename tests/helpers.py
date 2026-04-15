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
