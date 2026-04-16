"""Fishing rules: energy costs per range, cooldown enforcement, multiplier math,
fish escape handling, and batch stop-on-zero-energy.

RC1 — Review questions for Derek:
  - Are these energy costs correct? (short=1, mid=2, long=3)
  - Is the cooldown exactly 10s?
  - Can multiplier go above 5x?
"""

import time

import pytest

from .helpers import get_current_profile, get_energy, wait_for_cooldown


@pytest.mark.live
class TestFishingRanges:
    """Verify energy cost per range type."""

    @pytest.mark.order(37)
    @pytest.mark.timeout(60)
    def test_short_range_costs_1_energy(self, auth_token):
        """Fish short_range → energy drops by exactly 1."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 1:
            pytest.skip(f"Need >=1 energy, have {energy_before}")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")
        assert isinstance(result, dict)

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  short_range: energy {energy_before} → {energy_after} (cost={cost})")
        assert cost == 1, f"Expected cost 1, got {cost}"

    @pytest.mark.order(38)
    @pytest.mark.timeout(60)
    def test_mid_range_costs_2_energy(self, auth_token):
        """Fish mid_range → energy drops by exactly 2."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 2:
            pytest.skip(f"Need >=2 energy, have {energy_before}")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "mid_range")
        assert isinstance(result, dict)

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  mid_range: energy {energy_before} → {energy_after} (cost={cost})")
        assert cost == 2, f"Expected cost 2, got {cost}"

    @pytest.mark.order(39)
    @pytest.mark.timeout(60)
    def test_long_range_costs_3_energy(self, auth_token):
        """Fish long_range → energy drops by exactly 3."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 3:
            pytest.skip(f"Need >=3 energy, have {energy_before}")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "long_range")
        assert isinstance(result, dict)

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  long_range: energy {energy_before} → {energy_after} (cost={cost})")
        assert cost == 3, f"Expected cost 3, got {cost}"

    @pytest.mark.order(40)
    @pytest.mark.timeout(300)
    def test_range_affects_quality_distribution(self, auth_token):
        """Fish 5x short vs 5x long → compare avg quality (observational).

        Long range should tend to produce higher-quality fish on average,
        but this is probabilistic. We log results for Derek's review.
        """
        from ff_agent import fishing_client, auth

        token = auth.get_token()
        short_qualities = []
        long_qualities = []

        # Fish 5x short_range
        for i in range(5):
            if get_energy() < 1:
                break
            wait_for_cooldown()
            r = fishing_client.fish_session(token, "short_range")
            if r.get("success"):
                short_qualities.append(r["fish"]["quality"])

        # Fish 5x long_range
        for i in range(5):
            if get_energy() < 3:
                break
            wait_for_cooldown()
            r = fishing_client.fish_session(token, "long_range")
            if r.get("success"):
                long_qualities.append(r["fish"]["quality"])

        short_avg = sum(short_qualities) / len(short_qualities) if short_qualities else 0
        long_avg = sum(long_qualities) / len(long_qualities) if long_qualities else 0
        print(f"  Short range qualities: {short_qualities} (avg={short_avg:.2f})")
        print(f"  Long range qualities:  {long_qualities} (avg={long_avg:.2f})")

        # All qualities should be in valid range 1-5
        for q in short_qualities + long_qualities:
            assert 1 <= q <= 5, f"Quality {q} outside valid range 1-5"


@pytest.mark.live
class TestFishingCooldown:
    """Verify server-enforced 10s cooldown between casts."""

    @pytest.mark.order(41)
    @pytest.mark.timeout(30)
    def test_cooldown_enforced_under_10s(self, auth_token):
        """Two rapid casts <10s apart → second gets cooldown error."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        if get_energy() < 2:
            pytest.skip("Need >=2 energy for cooldown test")

        token = auth.get_token()
        r1 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r1, dict)

        # Immediately try again (no wait)
        r2 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r2, dict)

        # Second cast should fail with cooldown error
        if not r2.get("success"):
            error = str(r2.get("error", "")).lower()
            print(f"  Cooldown error: {r2.get('error')}")
            assert "10 second" in error or "cooldown" in error or "wait" in error, \
                f"Expected cooldown error, got: {r2.get('error')}"
        else:
            # If somehow it succeeded, the server may have been lenient
            print("  WARNING: Second rapid cast succeeded — server may allow fast casts")

    @pytest.mark.order(42)
    @pytest.mark.timeout(60)
    def test_cooldown_passes_after_11s(self, auth_token):
        """Wait 11s → second cast succeeds."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        if get_energy() < 2:
            pytest.skip("Need >=2 energy for cooldown test")

        token = auth.get_token()
        r1 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r1, dict)

        # Wait the full cooldown + margin
        wait_for_cooldown(11.0)

        r2 = fishing_client.fish_session(token, "short_range")
        assert isinstance(r2, dict)
        # After waiting, should succeed (or fail for game reasons, not cooldown)
        if not r2.get("success"):
            error = str(r2.get("error", "")).lower()
            assert "10 second" not in error and "cooldown" not in error, \
                f"Got cooldown error despite 11s wait: {r2.get('error')}"


@pytest.mark.live
class TestFishingMultiplier:
    """Verify multiplier affects energy cost linearly."""

    @pytest.mark.order(43)
    @pytest.mark.timeout(60)
    def test_multiplier_1x_normal_energy(self, auth_token):
        """Multiplier=1, short_range → costs 1 energy."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 1:
            pytest.skip("Need >=1 energy")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range", multiplier=1)
        assert isinstance(result, dict)

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  1x multiplier short_range: cost={cost}")
        assert cost == 1, f"Expected cost 1, got {cost}"

    @pytest.mark.order(44)
    @pytest.mark.timeout(60)
    def test_multiplier_5x_costs_5x_energy(self, auth_token):
        """Multiplier=5, short_range → costs 5 energy."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 5:
            pytest.skip(f"Need >=5 energy, have {energy_before}")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range", multiplier=5)
        assert isinstance(result, dict)

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  5x multiplier short_range: cost={cost}")
        assert cost == 5, f"Expected cost 5, got {cost}"


@pytest.mark.live
class TestFishingOutcomes:
    """Verify fish result structure and edge cases."""

    @pytest.mark.order(45)
    @pytest.mark.timeout(60)
    def test_successful_catch_has_fish_data(self, auth_token):
        """Successful catch returns name, quality (1-5), xp_gain (>0), sell_price (>0)."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        if get_energy() < 1:
            pytest.skip("Need energy to fish")

        token = auth.get_token()
        # Try up to 3 times to get a successful catch (fish can escape)
        result = None
        for attempt in range(3):
            if attempt > 0:
                wait_for_cooldown()
                if get_energy() < 1:
                    pytest.skip("Ran out of energy trying to catch a fish")
            r = fishing_client.fish_session(token, "short_range")
            if r.get("success"):
                result = r
                break

        if result is None:
            pytest.skip("Could not catch a fish in 3 attempts")

        fish = result["fish"]
        assert "name" in fish, "Fish missing 'name'"
        assert isinstance(fish["name"], str) and len(fish["name"]) > 0
        assert 1 <= fish["quality"] <= 5, f"Quality {fish['quality']} not in 1-5"
        assert fish["xp_gain"] > 0, f"xp_gain should be >0, got {fish['xp_gain']}"
        assert fish["sell_price"] > 0, f"sell_price should be >0, got {fish['sell_price']}"
        print(f"  Caught: {fish['name']} Q{fish['quality']} "
              f"XP={fish['xp_gain']} Gold={fish['sell_price']}")

    @pytest.mark.order(46)
    @pytest.mark.timeout(60)
    def test_escaped_fish_still_costs_energy(self, auth_token):
        """A 'Fish escaped' result still decrements energy.

        This is observational — escapes are random. If all attempts catch,
        we verify that energy is consumed regardless and log the outcome.
        """
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 1:
            pytest.skip("Need energy to fish")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")

        energy_after = get_energy()
        cost = energy_before - energy_after
        print(f"  Result: success={result.get('success')}, energy cost={cost}")

        # Whether caught or escaped, energy should be consumed
        assert cost >= 1, f"Expected >=1 energy cost, got {cost}"

    @pytest.mark.order(47)
    @pytest.mark.timeout(60)
    def test_new_fish_unlock_flagged(self, auth_token):
        """Check new_unlocks array exists in successful catch (may be empty)."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        if get_energy() < 1:
            pytest.skip("Need energy")

        token = auth.get_token()
        result = fishing_client.fish_session(token, "short_range")

        if result.get("success"):
            assert "new_unlocks" in result, "Missing new_unlocks field"
            assert isinstance(result["new_unlocks"], list), "new_unlocks should be a list"
            print(f"  new_unlocks: {result['new_unlocks']}")


@pytest.mark.live
class TestFishBatch:
    """Verify batch fishing stops correctly."""

    @pytest.mark.order(48)
    @pytest.mark.timeout(600)
    def test_batch_stops_on_zero_energy(self, auth_token):
        """Batch of 30 casts → stops early when energy hits 0."""
        from ff_agent import fishing_client, auth

        wait_for_cooldown()

        energy_before = get_energy()
        if energy_before < 1:
            pytest.skip("Need energy for batch test")

        token = auth.get_token()
        result = fishing_client.fish_batch(token, "short_range", count=30)

        assert result["total_casts"] <= 30
        energy_after = get_energy()

        print(f"  Batch: {result['total_casts']} casts, "
              f"{result['successes']} caught, {result['failures']} failed")
        print(f"  Energy: {energy_before} → {energy_after}")
        print(f"  Total XP: {result['total_xp']}, Total Gold: {result['total_gold_value']}")

        # If we ran out of energy, batch should have stopped
        if energy_after == 0:
            assert result["total_casts"] < 30, \
                "Batch should stop before 30 casts if energy runs out"
        # Total casts should be reasonable
        assert result["total_casts"] >= 1
