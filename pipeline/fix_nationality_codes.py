#!/usr/bin/env python3
"""
Fix players with missing nationality_code and nationality_flag.
Maps full country names to their ISO codes.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Country code to flag emoji mapping
COUNTRY_FLAGS = {
    "DK": "🇩🇰", "NL": "🇳🇱", "LB": "🇱🇧", "PK": "🇵🇰", "SN": "🇸🇳",
    "SC": "🇸🇨", "TT": "🇹🇹", "ZM": "🇿🇲", "AG": "🇦🇬", "CR": "🇨🇷",
    "GH": "🇬🇭", "HN": "🇭🇳", "JM": "🇯🇲",
}

# Map nationality names to their correct ISO codes
NATIONALITY_FIXES = {
    "Kingdom of Denmark": "DK",
    "Kingdom of the Netherlands": "NL",
    "Lebanon": "LB",
    "Pakistan": "PK",
    "Senegal": "SN",
    "Seychelles": "SC",
    "Trinidad and Tobago": "TT",
    "Zambia": "ZM",
    "Antigua and Barbuda": "AG",
    "Costa Rica": "CR",
    "Ghana": "GH",
    "Honduras": "HN",
    "Jamaica": "JM",
}


def get_players_with_missing_codes():
    """Fetch players with nationality but missing nationality_code."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # Get players where nationality is not null but nationality_code is empty or null
    url = f"{SUPABASE_URL}/rest/v1/players?select=id,name,nationality,nationality_code,nationality_flag"
    url += "&or=(nationality_code.is.null,nationality_code.eq.)"
    url += "&nationality=not.is.null"

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    log.error(f"Failed to fetch players: {resp.status_code} {resp.text}")
    return []


def update_player_nationality(player_id, nationality_code, nationality_flag):
    """Update a player's nationality_code and nationality_flag."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "nationality_code": nationality_code,
        "nationality_flag": nationality_flag,
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/players?id=eq.{player_id}",
        headers=headers,
        json=data
    )
    return resp.status_code in (200, 204)


def run_fix():
    """Fix all players with missing nationality codes."""
    log.info("=== Fixing Missing Nationality Codes ===")

    players = get_players_with_missing_codes()
    log.info(f"Found {len(players)} players with missing nationality codes")

    if not players:
        log.info("No players to fix!")
        return

    # Count by nationality
    nationality_counts = {}
    for p in players:
        nat = p.get("nationality", "Unknown")
        nationality_counts[nat] = nationality_counts.get(nat, 0) + 1

    log.info("Nationality breakdown:")
    for nat, count in sorted(nationality_counts.items(), key=lambda x: -x[1]):
        fix_code = NATIONALITY_FIXES.get(nat, "?")
        log.info(f"  {nat}: {count} players -> {fix_code}")

    # Apply fixes
    updated = 0
    skipped = 0

    for player in players:
        nationality = player.get("nationality", "")

        if nationality in NATIONALITY_FIXES:
            code = NATIONALITY_FIXES[nationality]
            flag = COUNTRY_FLAGS.get(code, "🏳️")

            if update_player_nationality(player["id"], code, flag):
                updated += 1
                log.info(f"  Fixed: {player['name']} -> {flag} {nationality} ({code})")
            else:
                log.warning(f"  Failed to update: {player['name']}")
        else:
            skipped += 1
            if nationality:
                log.warning(f"  No mapping for: {player['name']} ({nationality})")

    log.info(f"=== Done ===")
    log.info(f"Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    import sys

    if not SUPABASE_KEY:
        log.error("SUPABASE_SERVICE_KEY not set in environment")
        sys.exit(1)

    run_fix()
