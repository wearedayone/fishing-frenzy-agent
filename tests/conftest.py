"""Test configuration: DB isolation, fresh account fixtures, shared state."""

import shutil
import tempfile
from pathlib import Path

import pytest

_test_state_dir = None


def pytest_configure(config):
    """Redirect ff_agent state to a temp directory before any tests run."""
    global _test_state_dir
    _test_state_dir = Path(tempfile.mkdtemp(prefix="ff-test-"))

    # Monkeypatch the state module BEFORE any other ff_agent imports use it.
    # All other modules (auth, api_client, etc.) do `from . import state`
    # which gives them a reference to the SAME module object, so they'll
    # see our overwritten paths when they call state functions at runtime.
    import ff_agent.state as state_mod
    state_mod.STATE_DIR = _test_state_dir
    state_mod.DB_PATH = _test_state_dir / "state.db"


def pytest_unconfigure(config):
    """Clean up the test state directory."""
    if _test_state_dir and _test_state_dir.exists():
        shutil.rmtree(_test_state_dir, ignore_errors=True)


class TestSession:
    """Mutable state container that accumulates across ordered tests.

    A single instance is shared across all tests in the session via the
    `test_session` fixture. Tests update fields as game state evolves
    (e.g. after fishing, selling, buying).
    """
    wallet_address: str = None
    user_id: str = None
    access_token: str = None
    profile: dict = None
    session_id: int = None
    has_fish_in_inventory: bool = False
    player_level: int = 0
    gold_before_sell: float = 0
    gold_after_sell: float = 0

    def __init__(self):
        self.quest_ids = []


@pytest.fixture(scope="session")
def test_session():
    """Shared mutable state across all tests in a session."""
    return TestSession()


@pytest.fixture(scope="session")
def fresh_account(test_session):
    """Create a fresh game account (wallet + SIWE auth + game login).

    Called once per session. All tests share this account since game
    state builds progressively (fish -> sell -> buy).
    """
    from ff_agent import auth

    result = auth.setup_account()
    test_session.wallet_address = result["wallet_address"]
    test_session.user_id = result["user_id"]
    test_session.access_token = auth.get_token()
    return result


@pytest.fixture(scope="session")
def auth_token(fresh_account, test_session):
    """Get a valid auth token (depends on fresh_account being created)."""
    from ff_agent import auth

    token = auth.get_token()
    test_session.access_token = token
    return token
