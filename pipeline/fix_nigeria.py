#!/usr/bin/env python3
"""
Fix Nigerian players incorrectly coded as NE (Niger) instead of NG (Nigeria).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# Fetch players with NE code
url = f"{SUPABASE_URL}/rest/v1/players?select=id,name,nationality,nationality_code&nationality_code=eq.NE"
resp = requests.get(url, headers=headers)
players = resp.json()

print(f"Found {len(players)} players with NE (Niger) code:")
for p in players:
    print(f"  - {p['name']}: {p.get('nationality', 'N/A')}")

# These are Nigerian players, fix them to NG
print(f"\nUpdating {len(players)} players from NE to NG (Nigeria)...")

update_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

updated = 0
for player in players:
    data = {
        "nationality": "Nigeria",
        "nationality_code": "NG",
        "nationality_flag": "🇳🇬",
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/players?id=eq.{player['id']}",
        headers=update_headers,
        json=data
    )
    if resp.status_code in (200, 204):
        updated += 1
        print(f"  Fixed: {player['name']} -> 🇳🇬 Nigeria (NG)")
    else:
        print(f"  Error updating {player['name']}: {resp.status_code}")

print(f"\nDone! Updated {updated} players from NE (Niger) to NG (Nigeria)")
