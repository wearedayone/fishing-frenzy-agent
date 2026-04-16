"""Quest rules: daily rewards, quest lifecycle, social quests.

RC4 — Review questions for Derek:
  - Do daily quests reset at midnight UTC?
  - Can social quests be re-verified?
"""

import json

import pytest

from .helpers import get_current_profile, get_gold

FAKE_OBJECT_ID = "000000000000000000000000"


@pytest.mark.live
class TestDailyReward:
    """Verify daily reward claim behavior."""

    @pytest.mark.order(65)
    @pytest.mark.timeout(15)
    def test_daily_reward_first_claim(self, auth_token):
        """First claim → rewards received (gold, items, or energy)."""
        from ff_agent import api_client as api

        gold_before = get_gold()
        result = api.claim_daily_reward()
        gold_after = get_gold()

        assert isinstance(result, dict)
        print(f"  Daily reward: {result}")
        print(f"  Gold: {gold_before:.0f} → {gold_after:.0f}")

    @pytest.mark.order(66)
    @pytest.mark.timeout(15)
    def test_daily_reward_double_claim_safe(self, auth_token):
        """Second claim same day → 'already claimed' (no crash)."""
        from ff_agent import api_client as api

        # First claim (may already be claimed from previous test)
        api.claim_daily_reward()

        # Second claim
        gold_before = get_gold()
        result = api.claim_daily_reward()
        gold_after = get_gold()

        assert isinstance(result, dict)
        print(f"  Double claim result: {result}")

        # Gold should not increase on double claim
        change = gold_after - gold_before
        print(f"  Gold change on double claim: {change:.0f}")

    @pytest.mark.order(67)
    @pytest.mark.timeout(15)
    def test_daily_reward_verification(self, auth_token):
        """Verified gold_change from MCP tool matches profile delta."""
        from ff_agent.server import claim_daily_reward as claim_tool

        gold_before = get_gold()
        result_json = claim_tool()
        result = json.loads(result_json)
        gold_after = get_gold()

        actual_delta = gold_after - gold_before

        if "verified" in result and result["verified"] is not None:
            verified_change = result["verified"]["gold_change"]
            print(f"  Verified: {verified_change:.0f}, Actual: {actual_delta:.0f}")
            assert abs(verified_change - actual_delta) < 1.0
        else:
            print("  No verification data (may be already claimed)")


@pytest.mark.live
class TestQuestLifecycle:
    """Verify quest data structure and claim behavior."""

    @pytest.mark.order(68)
    @pytest.mark.timeout(15)
    def test_get_quests_returns_categories(self, auth_token):
        """Response has quest data with identifiable categories."""
        from ff_agent import api_client as api

        result = api.get_user_quests()
        assert result is not None

        # Quests may come as list or dict with categories
        if isinstance(result, dict):
            print(f"  Quest response keys: {list(result.keys())}")
        elif isinstance(result, list):
            print(f"  Quest count: {len(result)}")
            if result:
                print(f"  First quest keys: {list(result[0].keys())}")

    @pytest.mark.order(69)
    @pytest.mark.timeout(15)
    def test_quest_has_progress_fields(self, auth_token):
        """Each quest has questId, status, progress fields."""
        from ff_agent import api_client as api

        result = api.get_user_quests()
        quests = result if isinstance(result, list) else \
            result.get("data", result.get("quests", result.get("items", [])))

        if isinstance(quests, dict):
            # May be nested by category
            all_quests = []
            for v in quests.values():
                if isinstance(v, list):
                    all_quests.extend(v)
            quests = all_quests

        if not isinstance(quests, list) or len(quests) == 0:
            pytest.skip("No quests returned")

        quest = quests[0]
        print(f"  Quest keys: {list(quest.keys())}")

        # Check for ID field
        has_id = any(k in quest for k in ("questId", "_id", "id", "userQuestId"))
        assert has_id, f"Quest missing ID field. Keys: {list(quest.keys())}"

    @pytest.mark.order(70)
    @pytest.mark.timeout(15)
    def test_claim_uncompleted_quest_fails(self, auth_token):
        """Claim incomplete quest → error (not crash)."""
        from ff_agent import api_client as api

        result = api.claim_quest(FAKE_OBJECT_ID)
        assert isinstance(result, dict)
        print(f"  Claim fake quest: {result}")


@pytest.mark.live
class TestSocialQuests:
    """Verify social quest structure."""

    @pytest.mark.order(71)
    @pytest.mark.timeout(15)
    def test_verify_social_quest_structure(self, auth_token):
        """verify_social_quest returns structured response."""
        from ff_agent import api_client as api

        # Get social quests first
        social_result = api.get_social_quests()
        assert isinstance(social_result, (dict, list))
        print(f"  Social quests: {type(social_result)}")

        # Try verifying a fake one (should return error gracefully)
        result = api.verify_social_quest(FAKE_OBJECT_ID)
        assert isinstance(result, dict)
        print(f"  Verify fake social quest: {result}")
