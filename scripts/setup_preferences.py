#!/usr/bin/env python3
"""Interactive first-setup questionnaire for Fishing Frenzy Agent.

Walks new players through 5 questions that configure CONFIG.md.
Each question includes a brief explanation of the game mechanic.
"""

import os
import re
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "CONFIG.md")


def ask(question: str, options: list[tuple[str, str]], default: int = 1) -> int:
    """Ask a multiple-choice question and return the chosen option index (1-based).

    Args:
        question: The question text.
        options: List of (label, description) tuples.
        default: Default choice (1-based).
    """
    print(f"\n  {question}\n")
    for i, (label, desc) in enumerate(options, 1):
        marker = " (default)" if i == default else ""
        print(f"    {i}) {label}{marker}")
        print(f"       {desc}")
    print()

    while True:
        try:
            raw = input(f"  Choice [1-{len(options)}, default={default}]: ").strip()
            if raw == "":
                return default
            choice = int(raw)
            if 1 <= choice <= len(options):
                return choice
            print(f"  Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print(f"  Please enter a number between 1 and {len(options)}.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Setup cancelled.")
            sys.exit(0)


def update_config(key: str, value: str):
    """Update a key in CONFIG.md using regex substitution."""
    if not os.path.exists(CONFIG_PATH):
        print(f"  WARNING: CONFIG.md not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r") as f:
        content = f.read()

    # Match the key at the start of a line (inside code blocks)
    pattern = rf"^({re.escape(key)}:\s*).*$"
    replacement = rf"\g<1>{value}"
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)

    if count == 0:
        print(f"  WARNING: Could not find '{key}' in CONFIG.md")
        return

    with open(CONFIG_PATH, "w") as f:
        f.write(new_content)


def main():
    print()
    print("  ══════════════════════════════════════════")
    print("  🎣 Fishing Frenzy — Setup Your Preferences")
    print("  ══════════════════════════════════════════")

    # Q1: Strategy / Goal
    q1 = ask(
        "What's your main goal?",
        [
            ("Level up fast (Grind)",
             "Short-range fishing, max casts per energy, aggressive sushi buying."),
            ("Bit of both (Balanced)",
             "Medium-range fishing, cooking + quests, moderate spending."),
            ("Earn gold efficiently (Efficiency)",
             "Long-range fishing with bait, cook everything, careful gold management."),
        ],
        default=2,
    )
    strategy_map = {1: "grind", 2: "balanced", 3: "efficiency"}
    strategy = strategy_map[q1]
    update_config("STRATEGY", strategy)

    # Set strategy-specific defaults
    defaults = {
        "grind": {"sushi": 800, "cook": "false", "risk": "moderate", "reserve": 500},
        "balanced": {"sushi": 1500, "cook": "true", "risk": "moderate", "reserve": 1000},
        "efficiency": {"sushi": 2000, "cook": "true", "risk": "conservative", "reserve": 1000},
    }
    strat_defaults = defaults[strategy]

    # Q2: Sushi buying aggressiveness
    q2 = ask(
        "How aggressively should the agent buy sushi?\n"
        "  Sushi costs 500 gold and restores 5 energy (more energy = more fishing).",
        [
            ("Conservative (2000 gold)",
             "Only buy when you have plenty of gold to spare."),
            ("Moderate (1500 gold)",
             "Buy when comfortably above your gold reserve."),
            ("Aggressive (800 gold)",
             "Buy as soon as possible to maximize fishing time."),
        ],
        default={800: 3, 1500: 2, 2000: 1}.get(strat_defaults["sushi"], 2),
    )
    sushi_map = {1: 2000, 2: 1500, 3: 800}
    update_config("SUSHI_BUY_THRESHOLD", str(sushi_map[q2]))

    # Q3: Cook before selling
    q3 = ask(
        "Cook fish before selling?\n"
        "  Cooking turns fish into sashimi (worth pearls). Pearls spin the cooking\n"
        "  wheel for xFISH tokens. Skipping cooking maximizes gold per session.",
        [
            ("Yes — cook matching recipes first",
             "More pearls and xFISH, slightly less gold."),
            ("No — sell everything raw",
             "Maximum gold income, skip the cooking step."),
        ],
        default=1 if strat_defaults["cook"] == "true" else 2,
    )
    update_config("COOK_BEFORE_SELL", "true" if q3 == 1 else "false")

    # Q4: Diving risk
    q4 = ask(
        "How risky should diving be?\n"
        "  Diving reveals hidden cells on a board. More picks = more rewards, but\n"
        "  hitting a mine ends the dive and you lose uncollected rewards.",
        [
            ("Conservative (5-8 picks)",
             "Safe — cash out early, consistent small rewards."),
            ("Moderate (9-12 picks)",
             "Balanced risk — good rewards with reasonable safety."),
            ("Aggressive (13-15 picks)",
             "High risk, high reward — push deep into the board."),
        ],
        default={"conservative": 1, "moderate": 2, "aggressive": 3}.get(strat_defaults["risk"], 2),
    )
    risk_map = {1: "conservative", 2: "moderate", 3: "aggressive"}
    update_config("DIVE_RISK", risk_map[q4])

    # Q5: Gold reserve
    q5 = ask(
        "Minimum gold reserve to keep?\n"
        "  The agent won't spend gold below this amount. Protects against\n"
        "  accidentally going broke from sushi/diving purchases.",
        [
            ("500 gold",
             "Minimal safety net — spend freely."),
            ("1000 gold",
             "Comfortable buffer for one sushi + incidentals."),
            ("2000 gold",
             "Large reserve — very conservative spending."),
        ],
        default={500: 1, 1000: 2, 2000: 3}.get(strat_defaults["reserve"], 2),
    )
    reserve_map = {1: 500, 2: 1000, 3: 2000}
    update_config("GOLD_RESERVE", str(reserve_map[q5]))

    # Summary
    print()
    print("  ══════════════════════════════════════════")
    print(f"  ✅ Preferences saved to CONFIG.md")
    print()
    print(f"    Strategy:       {strategy}")
    print(f"    Sushi threshold: {sushi_map[q2]} gold")
    print(f"    Cook first:     {'yes' if q3 == 1 else 'no'}")
    print(f"    Dive risk:      {risk_map[q4]}")
    print(f"    Gold reserve:   {reserve_map[q5]}")
    print()
    print("  You can edit CONFIG.md anytime to fine-tune these values.")
    print("  ══════════════════════════════════════════")
    print()


if __name__ == "__main__":
    main()
