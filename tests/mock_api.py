"""Mock API helpers for offline testing.

Provides context managers that patch api_client._request and
fishing_client.fish_session with fixture-based responses.
"""

import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture by name (without .json extension)."""
    path = FIXTURES_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


@contextmanager
def mock_api_client(route_map: dict[tuple[str, str], str | dict] = None):
    """Patch api_client._request to return fixture data.

    Args:
        route_map: Dict mapping (method, path) tuples to fixture names (str)
                   or raw response dicts. If a tuple isn't found, returns
                   a generic error response.

    Yields a call_log list of (method, path, kwargs) tuples for assertion.

    Example:
        with mock_api_client({("GET", "/v1/users/me"): "profile"}) as log:
            profile = api.get_me()
            assert profile["username"] == "TestBot_0xABCD"
            assert len(log) == 1
    """
    if route_map is None:
        route_map = {}

    call_log = []

    def _fake_request(method: str, path: str, **kwargs):
        call_log.append((method, path, kwargs))
        key = (method.upper(), path)
        value = route_map.get(key)
        if value is None:
            return {"code": 404, "message": f"No mock for {method} {path}"}
        if isinstance(value, str):
            return load_fixture(value)
        return value

    with patch("ff_agent.api_client._request", side_effect=_fake_request):
        yield call_log


@contextmanager
def mock_fishing_client(results: list[dict] = None):
    """Patch fishing_client.fish_session to return a sequence of results.

    Args:
        results: List of result dicts to return in order. When exhausted,
                 returns an energy-depleted error.

    Yields a call_log list of (token, range_type, kwargs) tuples.

    Example:
        success = load_fixture("fish_session_success")
        with mock_fishing_client([success, success]) as log:
            r1 = fishing_client.fish_session("tok", "short_range")
            r2 = fishing_client.fish_session("tok", "short_range")
            assert r1["success"] is True
    """
    if results is None:
        results = []

    call_log = []
    result_iter = iter(results)

    def _fake_fish_session(token: str, range_type: str = "short_range",
                           theme_id: str = None, multiplier: int = 1):
        call_log.append((token, range_type, {"theme_id": theme_id, "multiplier": multiplier}))
        try:
            return next(result_iter)
        except StopIteration:
            return {
                "success": False,
                "error": "Not enough energy",
            }

    with patch("ff_agent.fishing_client.fish_session", side_effect=_fake_fish_session):
        yield call_log
