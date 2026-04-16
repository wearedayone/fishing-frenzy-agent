"""Test configuration: DB isolation, fresh account fixtures, shared state."""

import shutil
import tempfile
from pathlib import Path

import pytest

_test_state_dir = None


def pytest_addoption(parser):
    """Add custom CLI options for the test suite."""
    parser.addoption(
        "--skip-live",
        action="store_true",
        default=False,
        help="Skip tests that require a live API connection",
    )


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

    # Register custom markers
    config.addinivalue_line("markers", "live: test requires a live API connection")


def pytest_collection_modifyitems(config, items):
    """Skip tests marked 'live' when --skip-live is passed."""
    if not config.getoption("--skip-live"):
        return
    skip_live = pytest.mark.skip(reason="--skip-live flag: skipping live API tests")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


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

    Gracefully skips if auth fails (e.g. API down, 405, network issues).
    """
    from ff_agent import auth

    try:
        result = auth.setup_account()
    except Exception as e:
        pytest.skip(f"Live auth failed (use --skip-live to skip): {e}")
        return None

    test_session.wallet_address = result["wallet_address"]
    test_session.user_id = result["user_id"]
    test_session.access_token = auth.get_token()
    return result


@pytest.fixture(scope="session")
def auth_token(fresh_account, test_session):
    """Get a valid auth token (depends on fresh_account being created)."""
    if fresh_account is None:
        pytest.skip("No live account available")
    from ff_agent import auth

    token = auth.get_token()
    test_session.access_token = token
    return token


@pytest.fixture(scope="session")
def mock_account(test_session):
    """Seed the state DB with fake wallet/auth data — no API calls.

    Use this fixture for offline tests that need valid state DB entries
    but don't need a real game account.
    """
    from ff_agent import state

    # Seed wallet
    state.save_wallet("0x" + "a1" * 20, "0x" + "ff" * 32)

    # Seed auth tokens (fake but structurally valid)
    state.save_auth(
        access_token="mock-access-token-for-testing",
        refresh_token="mock-refresh-token-for-testing",
        user_id="mock-user-id-12345",
        privy_token="mock-privy-token",
    )

    test_session.wallet_address = "0x" + "a1" * 20
    test_session.user_id = "mock-user-id-12345"
    test_session.access_token = "mock-access-token-for-testing"

    return {
        "wallet_address": "0x" + "a1" * 20,
        "user_id": "mock-user-id-12345",
        "authenticated": True,
    }
