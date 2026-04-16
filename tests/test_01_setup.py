"""Setup tests: installation, account creation, auth verification."""

import pytest


class TestSetup:
    """Verify installation, account creation, and basic auth (7 tests)."""

    @pytest.mark.order(1)
    def test_imports_succeed(self):
        """All ff_agent modules import without error."""
        import ff_agent
        import ff_agent.auth
        import ff_agent.api_client
        import ff_agent.fishing_client
        import ff_agent.diving_client
        import ff_agent.state
        import ff_agent.wallet
        import ff_agent.server
        import ff_agent.chain
        import ff_agent.strategy

    @pytest.mark.order(2)
    def test_mcp_server_has_47_tools(self):
        """FastMCP server exposes 47+ registered tools."""
        from ff_agent.server import server

        tool_count = 0
        # FastMCP stores tools in _tool_manager._tools (mcp>=1.0)
        if hasattr(server, "_tool_manager"):
            tm = server._tool_manager
            if hasattr(tm, "_tools"):
                tool_count = len(tm._tools)
            elif hasattr(tm, "tools"):
                tool_count = len(tm.tools)
        elif hasattr(server, "_tools"):
            tool_count = len(server._tools)

        assert tool_count >= 47, f"Expected 47+ tools, got {tool_count}"

    @pytest.mark.order(3)
    def test_dependencies_installed(self):
        """Core dependencies are importable."""
        import httpx
        import websockets
        import eth_account
        import mcp
        import web3

    @pytest.mark.live
    @pytest.mark.order(4)
    @pytest.mark.timeout(30)
    def test_setup_account_creates_wallet(self, fresh_account, test_session):
        """setup_account() creates a valid Ethereum wallet and authenticates."""
        assert fresh_account["wallet_address"].startswith("0x")
        assert len(fresh_account["wallet_address"]) == 42
        assert fresh_account["authenticated"] is True
        assert fresh_account["user_id"] is not None
        assert len(fresh_account["user_id"]) > 0

    @pytest.mark.live
    @pytest.mark.order(5)
    def test_state_db_initialized(self, fresh_account):
        """SQLite DB has all required tables (auth, wallet, sessions, cache)."""
        from ff_agent import state

        conn = state.get_connection()
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = [r[0] for r in rows]
        conn.close()

        for table in ("auth", "wallet", "sessions", "cache", "action_log"):
            assert table in tables, f"Missing table: {table}"

    @pytest.mark.live
    @pytest.mark.order(6)
    def test_auth_tokens_persisted(self, fresh_account):
        """Auth tokens are persisted in the state DB after setup."""
        from ff_agent import state

        assert state.get_auth("access_token") is not None, "No access_token"
        assert state.get_auth("refresh_token") is not None, "No refresh_token"
        assert state.get_auth("user_id") is not None, "No user_id"

    @pytest.mark.live
    @pytest.mark.order(7)
    @pytest.mark.timeout(15)
    def test_get_profile_returns_valid_data(self, auth_token, test_session):
        """get_me() returns a profile with level, energy, gold, maxEnergy."""
        from ff_agent import api_client as api

        profile = api.get_me()
        user = profile if "username" in profile else profile.get("data", profile)

        for field in ("energy", "gold", "level"):
            assert field in user, f"Profile missing field: {field}"

        test_session.player_level = user.get("level", 0)
        test_session.profile = user
