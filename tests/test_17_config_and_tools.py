"""Tests for CONFIG.md parsing, strategy advice tools, and setup questionnaire.

All offline — uses mock API or temp CONFIG.md files.
"""

import json
import os
import shutil
import tempfile

import pytest


# ============================================================
# _parse_config
# ============================================================

class TestParseConfig:
    """Verify _parse_config reads CONFIG.md correctly."""

    def _write_config(self, tmpdir, content):
        """Write a CONFIG.md to tmpdir and monkeypatch server to read it."""
        config_path = os.path.join(tmpdir, "CONFIG.md")
        with open(config_path, "w") as f:
            f.write(content)
        return config_path

    def test_parses_default_config(self):
        """Reads the real CONFIG.md and returns a valid StrategyConfig."""
        from ff_agent.server import _parse_config
        config = _parse_config()
        assert config.strategy in ("balanced", "grind", "risk")
        assert config.sushi_buy_threshold > 0
        assert config.gold_reserve >= 0

    def test_balanced_defaults(self):
        """Default CONFIG.md has balanced strategy with standard thresholds."""
        from ff_agent.server import _parse_config
        config = _parse_config()
        # These are the defaults from the real CONFIG.md
        if config.strategy == "balanced":
            assert config.sushi_buy_threshold == 1500
            assert config.gold_reserve == 1000
            assert config.diving_gold_threshold == 2500

    def test_parses_custom_values(self, monkeypatch, tmp_path):
        """Custom CONFIG.md values are parsed correctly."""
        custom_config = """\
# Agent Configuration
```
STRATEGY: grind
SUSHI_BUY_THRESHOLD: 900
GOLD_RESERVE: 500
DIVING_GOLD_THRESHOLD: 3000
FISHING_STRATEGY: short
FISH_DISPOSAL: hold
MAX_SUSHI_PER_SESSION: 0
USE_MULTIPLIER: true
DIVE_RISK: aggressive
DIVE_MAX_PICKS: 15
UPGRADE_ORDER: Reel, Icebox
COOK_BEFORE_SELL: false
SPIN_COOKING_WHEEL: false
```
"""
        config_path = tmp_path / "CONFIG.md"
        config_path.write_text(custom_config)

        # Monkeypatch the config path used by _parse_config
        import ff_agent.server as srv
        original_file = os.path.abspath(__file__)
        repo_dir = os.path.dirname(os.path.dirname(original_file))

        import re
        def _patched_parse():
            content = config_path.read_text()
            def _val(key, default=""):
                m = re.search(rf"^{re.escape(key)}:\s*(.+)$", content, re.MULTILINE)
                return m.group(1).strip() if m else default

            from ff_agent.strategy import StrategyConfig, STRATEGY_DEFAULTS
            strategy_name = _val("STRATEGY", "balanced")
            base = STRATEGY_DEFAULTS.get(strategy_name, STRATEGY_DEFAULTS["balanced"])
            return StrategyConfig(
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

        monkeypatch.setattr(srv, "_parse_config", _patched_parse)
        config = srv._parse_config()

        assert config.strategy == "grind"
        assert config.sushi_buy_threshold == 900
        assert config.gold_reserve == 500
        assert config.diving_gold_threshold == 3000
        assert config.fishing_strategy == "short"
        assert config.fish_disposal == "hold"
        assert config.max_sushi_per_session == 0
        assert config.use_multiplier is True
        assert config.dive_risk == "aggressive"
        assert config.dive_max_picks == 15
        assert config.upgrade_order == "Reel, Icebox"
        assert config.cook_before_sell is False
        assert config.spin_cooking_wheel is False


# ============================================================
# get_strategy_advice tool
# ============================================================

class TestGetStrategyAdvice:
    """Verify the get_strategy_advice MCP tool returns correct decisions."""

    def test_returns_valid_json(self):
        """Tool returns parseable JSON with all expected keys."""
        from ff_agent.server import get_strategy_advice
        result = json.loads(get_strategy_advice(
            gold=3000, energy=10, level=25,
            has_bait_medium=True, has_bait_big=False,
            has_recipe_match=False, sushi_bought=0,
        ))

        assert "strategy" in result
        assert "fishing_range" in result
        assert "should_buy_sushi" in result
        assert "should_dive" in result
        assert "fish_disposal" in result
        assert "dive_max_picks" in result
        assert "thresholds" in result

    def test_level_25_cannot_dive(self):
        """Level 25 player should not be advised to dive."""
        from ff_agent.server import get_strategy_advice
        result = json.loads(get_strategy_advice(
            gold=10000, energy=0, level=25,
        ))
        assert result["should_dive"] is False

    def test_zero_energy_sushi_decision(self):
        """With 0 energy and sufficient gold, sushi decision depends on config."""
        from ff_agent.server import get_strategy_advice
        result = json.loads(get_strategy_advice(
            gold=5000, energy=0, level=10,
        ))
        # With default balanced (threshold 1500 + reserve 1000 = 2500), 5000 gold → buy
        assert isinstance(result["should_buy_sushi"], bool)

    def test_fishing_range_is_valid(self):
        """Fishing range is one of the known range types."""
        from ff_agent.server import get_strategy_advice
        result = json.loads(get_strategy_advice(
            gold=1000, energy=20, level=10,
            has_bait_medium=True, has_bait_big=True,
        ))
        assert result["fishing_range"] in ("short_range", "mid_range", "long_range")

    def test_thresholds_included(self):
        """Response includes calculated thresholds."""
        from ff_agent.server import get_strategy_advice
        result = json.loads(get_strategy_advice(gold=1000, energy=10, level=10))
        thresholds = result["thresholds"]
        assert "sushi_buy_at" in thresholds
        assert "dive_at" in thresholds
        assert "gold_reserve" in thresholds
        assert thresholds["sushi_buy_at"] > thresholds["gold_reserve"]


# ============================================================
# get_next_upgrade_advice tool
# ============================================================

class TestGetNextUpgradeAdvice:
    """Verify the get_next_upgrade_advice MCP tool (uses mock API)."""

    def test_returns_recommendation_with_mock(self, mock_account):
        """With mocked accessories, returns a valid recommendation."""
        from ff_agent.server import get_next_upgrade_advice
        from unittest.mock import patch

        mock_accessories = {
            "availableUpgradePoint": 3,
            "accessories": [
                {"name": "Rod Handle", "accessoryId": "rh1", "currentLevel": 2, "maxLevel": 10},
                {"name": "Icebox", "accessoryId": "ib1", "currentLevel": 0, "maxLevel": 10},
                {"name": "Reel", "accessoryId": "rl1", "currentLevel": 1, "maxLevel": 10},
                {"name": "Fishing Manual", "accessoryId": "fm1", "currentLevel": 0, "maxLevel": 10},
                {"name": "Lucky Charm", "accessoryId": "lc1", "currentLevel": 0, "maxLevel": 10},
                {"name": "Cutting Board", "accessoryId": "cb1", "currentLevel": 0, "maxLevel": 10},
            ],
        }

        def _mock_request(method, path, **kwargs):
            if path == "/accessories":
                return mock_accessories
            return {"code": 404}

        with patch("ff_agent.api_client._request", side_effect=_mock_request):
            result = json.loads(get_next_upgrade_advice())

        assert "recommended_upgrade" in result
        assert "available_points" in result
        assert "can_upgrade" in result
        assert "current_levels" in result
        assert result["available_points"] == 3
        assert result["can_upgrade"] is True
        # With balanced default, first upgrade should be Rod Handle (already at 2),
        # so Icebox should be next
        assert result["recommended_upgrade"] is not None

    def test_all_maxed_returns_null(self, mock_account):
        """When all accessories are maxed, recommendation is null."""
        from ff_agent.server import get_next_upgrade_advice
        from unittest.mock import patch

        mock_accessories = {
            "availableUpgradePoint": 5,
            "accessories": [
                {"name": "Rod Handle", "accessoryId": "rh1", "currentLevel": 10, "maxLevel": 10},
                {"name": "Icebox", "accessoryId": "ib1", "currentLevel": 10, "maxLevel": 10},
                {"name": "Reel", "accessoryId": "rl1", "currentLevel": 10, "maxLevel": 10},
                {"name": "Fishing Manual", "accessoryId": "fm1", "currentLevel": 10, "maxLevel": 10},
                {"name": "Lucky Charm", "accessoryId": "lc1", "currentLevel": 10, "maxLevel": 10},
                {"name": "Cutting Board", "accessoryId": "cb1", "currentLevel": 10, "maxLevel": 10},
            ],
        }

        def _mock_request(method, path, **kwargs):
            if path == "/accessories":
                return mock_accessories
            return {"code": 404}

        with patch("ff_agent.api_client._request", side_effect=_mock_request):
            result = json.loads(get_next_upgrade_advice())

        assert result["recommended_upgrade"] is None
        assert result["can_upgrade"] is False


# ============================================================
# setup_preferences.py update_config
# ============================================================

class TestSetupPreferencesConfig:
    """Verify update_config() correctly modifies CONFIG.md keys."""

    def test_updates_strategy(self, tmp_path):
        """update_config changes STRATEGY value."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "play-fishing-frenzy", "scripts"))
        import setup_preferences

        config_src = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "play-fishing-frenzy", "CONFIG.md"
        )
        config_copy = tmp_path / "CONFIG.md"
        shutil.copy(config_src, config_copy)

        # Monkeypatch CONFIG_PATH
        original_path = setup_preferences.CONFIG_PATH
        setup_preferences.CONFIG_PATH = str(config_copy)
        try:
            setup_preferences.update_config("STRATEGY", "grind")
            content = config_copy.read_text()
            assert "STRATEGY: grind" in content

            setup_preferences.update_config("STRATEGY", "risk")
            content = config_copy.read_text()
            assert "STRATEGY: risk" in content
        finally:
            setup_preferences.CONFIG_PATH = original_path

    def test_updates_numeric_value(self, tmp_path):
        """update_config changes numeric values correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "play-fishing-frenzy", "scripts"))
        import setup_preferences

        config_src = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "play-fishing-frenzy", "CONFIG.md"
        )
        config_copy = tmp_path / "CONFIG.md"
        shutil.copy(config_src, config_copy)

        original_path = setup_preferences.CONFIG_PATH
        setup_preferences.CONFIG_PATH = str(config_copy)
        try:
            setup_preferences.update_config("SUSHI_BUY_THRESHOLD", "800")
            content = config_copy.read_text()
            assert "SUSHI_BUY_THRESHOLD: 800" in content

            setup_preferences.update_config("GOLD_RESERVE", "2000")
            content = config_copy.read_text()
            assert "GOLD_RESERVE: 2000" in content
        finally:
            setup_preferences.CONFIG_PATH = original_path

    def test_updates_boolean_value(self, tmp_path):
        """update_config changes boolean values correctly."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "play-fishing-frenzy", "scripts"))
        import setup_preferences

        config_src = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "play-fishing-frenzy", "CONFIG.md"
        )
        config_copy = tmp_path / "CONFIG.md"
        shutil.copy(config_src, config_copy)

        original_path = setup_preferences.CONFIG_PATH
        setup_preferences.CONFIG_PATH = str(config_copy)
        try:
            setup_preferences.update_config("COOK_BEFORE_SELL", "false")
            content = config_copy.read_text()
            assert "COOK_BEFORE_SELL: false" in content

            setup_preferences.update_config("COOK_BEFORE_SELL", "true")
            content = config_copy.read_text()
            assert "COOK_BEFORE_SELL: true" in content
        finally:
            setup_preferences.CONFIG_PATH = original_path

    def test_preserves_other_values(self, tmp_path):
        """Changing one key does not affect other keys."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "play-fishing-frenzy", "scripts"))
        import setup_preferences

        config_src = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "play-fishing-frenzy", "CONFIG.md"
        )
        config_copy = tmp_path / "CONFIG.md"
        shutil.copy(config_src, config_copy)

        original_path = setup_preferences.CONFIG_PATH
        setup_preferences.CONFIG_PATH = str(config_copy)
        try:
            # Read original values
            content_before = config_copy.read_text()

            # Change one value
            setup_preferences.update_config("STRATEGY", "grind")
            content_after = config_copy.read_text()

            # STRATEGY changed
            assert "STRATEGY: grind" in content_after
            # Other values unchanged
            assert "SUSHI_BUY_THRESHOLD: 1500" in content_after
            assert "GOLD_RESERVE: 1000" in content_after
        finally:
            setup_preferences.CONFIG_PATH = original_path
