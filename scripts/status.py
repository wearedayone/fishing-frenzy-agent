#!/usr/bin/env python3
"""Quick status check — called by SKILL.md dynamic context injection."""

import json
import os
import sys

# Add parent directory so we can import ff_agent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ff_agent import state
    from ff_agent import wallet as w

    auth = state.get_auth("user_id")
    if not auth:
        print("STATUS: No account yet. Run setup_account() to create one.")
        sys.exit(0)

    # Get basic info from state
    user_id = state.get_auth("user_id")
    wallet = w.get_address()
    lifetime = state.get_lifetime_stats()
    recent = state.get_session_history(3)

    print(f"Account: {user_id}")
    if wallet:
        print(f"Wallet: {wallet[:8]}...{wallet[-4:]}")
    if lifetime:
        print(f"Lifetime: {lifetime.get('total_fish', 0)} fish, "
              f"{lifetime.get('total_gold', 0):.0f} gold earned, "
              f"{lifetime.get('total_sessions', 0)} sessions")
    if recent:
        last = recent[0]
        print(f"Last session: {last.get('started_at', 'unknown')}")

except Exception as e:
    print(f"STATUS: Agent ready (state unavailable: {e})")
