#!/usr/bin/env python3
"""Parse CONFIG.md and output current settings for SKILL.md context injection."""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "CONFIG.md")


def parse_config(path: str) -> dict:
    """Parse key: value pairs from code blocks in CONFIG.md."""
    config = {}
    if not os.path.exists(path):
        return config

    with open(path) as f:
        in_code_block = False
        for line in f:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                match = re.match(r"^(\w+):\s*(.+)$", stripped)
                if match:
                    config[match.group(1)] = match.group(2).strip()
    return config


if __name__ == "__main__":
    config = parse_config(CONFIG_PATH)
    if not config:
        print("CONFIG: Using defaults (no CONFIG.md found or empty)")
    else:
        print(f"Strategy: {config.get('STRATEGY', 'balanced')}")
        print(f"Sushi threshold: {config.get('SUSHI_BUY_THRESHOLD', '1500')}g")
        print(f"Range: {config.get('PREFERRED_RANGE', 'auto')}")
        print(f"Dive risk: {config.get('DIVE_RISK', 'moderate')}")
        upgrades = config.get("UPGRADE_ORDER", "rod_handle, icebox, reel")
        print(f"Upgrades: {upgrades.split(',')[0].strip()} first")
