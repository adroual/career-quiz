#!/usr/bin/env python3
"""
Clean malformed club names in career_entries table.
Removes trailing data like "| caps3 = 13 | goals3 = 0" from club names.
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def supabase_request(method, endpoint, data=None):
    """Make a request to Supabase REST API."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"

    if method == "GET":
        resp = requests.get(url, headers=headers)
    elif method == "PATCH":
        headers["Prefer"] = "return=minimal"
        resp = requests.patch(url, headers=headers, json=data)

    return resp


def clean_club_name(club: str) -> str:
    """Extract clean club name by removing trailing pipe data."""
    # Remove everything after the first pipe character
    if "|" in club:
        club = club.split("|")[0]

    # Also clean up any trailing whitespace
    club = club.strip()

    return club


def fix_malformed_clubs():
    """Fetch entries with malformed club names and clean them."""
    print("Fetching career entries with malformed club names...")

    # Get entries where club contains "|" (indicating malformed data)
    resp = supabase_request("GET", "career_entries?club=like.*|*&select=id,club&limit=1000")

    if resp.status_code != 200:
        print(f"Error fetching entries: {resp.status_code} {resp.text}")
        return

    entries = resp.json()
    print(f"Found {len(entries)} entries with malformed club names")

    if not entries:
        print("No entries to fix!")
        return

    # Process and update each entry
    updated = 0
    errors = 0

    for entry in entries:
        old_club = entry["club"]
        new_club = clean_club_name(old_club)

        if old_club == new_club:
            continue

        # Update the entry
        resp = supabase_request(
            "PATCH",
            f"career_entries?id=eq.{entry['id']}",
            {"club": new_club}
        )

        if resp.status_code in (200, 204):
            updated += 1
            if updated <= 10:  # Show first 10 examples
                print(f"  Fixed: '{old_club[:50]}...' -> '{new_club}'")
        else:
            errors += 1
            print(f"  Error updating {entry['id']}: {resp.status_code}")

    print(f"\n=== Results ===")
    print(f"Updated: {updated} entries")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    if not SUPABASE_KEY:
        print("Error: SUPABASE_SERVICE_KEY not set in .env")
        exit(1)

    fix_malformed_clubs()
