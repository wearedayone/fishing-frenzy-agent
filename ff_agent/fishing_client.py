"""REST-based fishing client for Fishing Frenzy.

The fishing minigame uses a two-step REST flow:
1. POST /fishing-sessions — creates a session, returns the random fish
2. POST /fishing-sessions/{id}/results — submits gameplay frames, returns catch result
"""

import random
import time

import httpx

# Default theme ID (standard fishing zone)
DEFAULT_THEME_ID = "6752b7a7ef93f2489cfef709"

# Cooldown between consecutive fishing sessions (seconds)
# Server enforces 10-second minimum between casts
CAST_COOLDOWN = 10.0

API_BASE = "https://api.fishingfrenzy.co/v1"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "https://fishingfrenzy.co",
    }


def _generate_frames(count: int = 20) -> list:
    """Generate realistic [fishY, netY] frame pairs.

    In the real game, these track the vertical positions of the fish sprite
    and the catch-net sprite during the reel-in minigame.
    """
    frames = []
    fish_y = random.randint(80, 160)
    net_y = random.randint(160, 260)

    for _ in range(count):
        fish_y += random.randint(-12, 12)
        net_y += random.randint(-8, 8)
        fish_y = max(40, min(320, fish_y))
        net_y = max(80, min(380, net_y))
        frames.append([fish_y, net_y])

    return frames


def fish_session(token: str, range_type: str = "short_range",
                 theme_id: str = None, multiplier: int = 1) -> dict:
    """Execute one complete fishing session.

    Args:
        token: JWT access token.
        range_type: "short_range" (1 energy), "mid_range" (2), "long_range" (3).
        theme_id: Fishing zone theme ObjectId. Uses default if None.
        multiplier: Fishing multiplier (1 = normal).

    Returns:
        Dict with success, fish caught details, XP, gold, energy remaining.
    """
    theme = theme_id or DEFAULT_THEME_ID
    hdrs = _headers(token)

    # Step 1: Create fishing session
    init_body = {
        "themeId": theme,
        "range": range_type,
        "fishingMultiplier": multiplier,
        "isMonsterFight": False,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(f"{API_BASE}/fishing-sessions",
                               json=init_body, headers=hdrs)

            if resp.status_code not in (200, 201):
                error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"message": resp.text}
                return {
                    "success": False,
                    "error": error.get("message", str(error)),
                }

            session_data = resp.json()
            session_id = session_data.get("fishingSessionId")
            fish_info = session_data.get("randomFish", {})
            current_energy = session_data.get("currentEnergy")

            # Simulate gameplay timing
            # hookTimestamp = when the fish bites (after casting animation)
            cast_time = int(time.time() * 1000)
            bite_delay = random.randint(1500, 3000)  # 1.5-3s for fish to bite
            hook_ts = cast_time + bite_delay

            # Simulate the reel-in minigame duration
            game_duration = random.uniform(3.0, 6.0)
            time.sleep(game_duration)

            # submitTimestamp = when the catch attempt ends (always after hook)
            submit_ts = hook_ts + int(game_duration * 1000) + random.randint(500, 1500)

            # Generate frame data
            frames = _generate_frames(20)

            # Step 2: Submit results
            result_body = {
                "hookTimestamp": hook_ts,
                "submitTimestamp": submit_ts,
                "frames": frames,
            }

            resp2 = client.post(
                f"{API_BASE}/fishing-sessions/{session_id}/results",
                json=result_body, headers=hdrs,
            )

            if resp2.status_code != 200:
                error = resp2.json() if resp2.headers.get("content-type", "").startswith("application/json") else {"message": resp2.text}
                return {
                    "success": False,
                    "error": error.get("message", str(error)),
                    "session_id": session_id,
                }

            result = resp2.json()
            success = result.get("success", False)
            caught = result.get("catchedFish", {})

            if success:
                fish_detail = caught.get("fishInfo", fish_info)
                new_fishes = caught.get("newFishes", [])
                return {
                    "success": True,
                    "session_id": session_id,
                    "range": range_type,
                    "multiplier": multiplier,
                    "fish": {
                        "name": fish_detail.get("fishName", fish_info.get("fishName", "Unknown")),
                        "quality": fish_detail.get("quality", 0),
                        "xp_gain": fish_detail.get("expGain", 0),
                        "sell_price": fish_detail.get("sellPrice", 0),
                        "weight": fish_info.get("weight", 0),
                        "image": fish_detail.get("imageName", ""),
                    },
                    "player": {
                        "level": caught.get("level"),
                        "exp": caught.get("exp"),
                        "energy_remaining": current_energy,
                    },
                    "new_unlocks": [f.get("fishName") for f in new_fishes],
                    "refunds": caught.get("refunds", {}),
                }
            else:
                # Catch failed (fish escaped) — still costs energy
                return {
                    "success": False,
                    "session_id": session_id,
                    "range": range_type,
                    "error": "Fish escaped",
                    "energy_remaining": current_energy,
                }

    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fish_batch(token: str, range_type: str = "short_range",
               count: int = 5, theme_id: str = None,
               multiplier: int = 1) -> dict:
    """Fish multiple times in sequence with cooldowns.

    Stops early if a session fails (e.g. out of energy).

    Returns:
        Summary: total caught, total XP/gold, successes, failures, results list.
    """
    results = []
    successes = 0
    failures = 0
    total_xp = 0
    total_gold = 0

    last_cast_time = 0
    for i in range(count):
        if i > 0:
            # Ensure at least CAST_COOLDOWN seconds between session starts
            elapsed = time.time() - last_cast_time
            wait = max(0, CAST_COOLDOWN - elapsed + random.uniform(0.5, 1.5))
            if wait > 0:
                time.sleep(wait)
        last_cast_time = time.time()

        result = fish_session(token, range_type, theme_id, multiplier)
        results.append(result)

        if result["success"]:
            successes += 1
            fish = result.get("fish", {})
            total_xp += fish.get("xp_gain", 0)
            total_gold += fish.get("sell_price", 0)
        else:
            error = result.get("error", "")
            # "Fish escaped" is normal gameplay — count it but don't stop
            if "escaped" in str(error).lower():
                failures += 1
            elif any(s in str(error).lower() for s in ["energy", "not enough", "401", "unauthorized"]):
                failures += 1
                break  # Stop on resource/auth errors
            elif "10 seconds" in str(error).lower():
                # Cooldown error — wait and retry this cast
                time.sleep(5)
                continue
            else:
                failures += 1

    return {
        "total_casts": len(results),
        "successes": successes,
        "failures": failures,
        "total_xp": total_xp,
        "total_gold_value": total_gold,
        "results": results,
    }


def get_active_themes(token: str) -> list:
    """Fetch active fishing themes (zones) from the game.

    Returns list of themes with their IDs. The default theme has isDefault=True.
    """
    hdrs = _headers(token)
    with httpx.Client(timeout=15) as client:
        resp = client.get(f"{API_BASE}/events/active", headers=hdrs)
        if resp.status_code != 200:
            return []
        events = resp.json()
        themes = []
        for event in events if isinstance(events, list) else [events]:
            for theme in event.get("themes", []):
                themes.append({
                    "id": theme.get("_id"),
                    "name": theme.get("name"),
                    "is_default": theme.get("isDefault", False),
                })
        return themes
