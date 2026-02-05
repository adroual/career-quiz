#!/usr/bin/env python3
"""
Remove "1. " prefix from club names in career_entries table.
"""

import os
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


def remove_prefix():
    """Remove '1. ' prefix from club names."""
    print("Fetching career entries with '1. ' prefix...")

    # Get entries where club starts with "1. "
    resp = supabase_request("GET", "career_entries?club=like.1.%20*&select=id,club&limit=1000")

    if resp.status_code != 200:
        print(f"Error fetching entries: {resp.status_code} {resp.text}")
        return

    entries = resp.json()
    print(f"Found {len(entries)} entries with '1. ' prefix")

    if not entries:
        print("No entries to fix!")
        return

    # Process and update each entry
    updated = 0
    errors = 0

    for entry in entries:
        old_club = entry["club"]

        # Remove "1. " prefix
        if old_club.startswith("1. "):
            new_club = old_club[3:]  # Remove first 3 characters "1. "
        else:
            continue

        # Update the entry
        resp = supabase_request(
            "PATCH",
            f"career_entries?id=eq.{entry['id']}",
            {"club": new_club}
        )

        if resp.status_code in (200, 204):
            updated += 1
            if updated <= 15:  # Show first 15 examples
                print(f"  Fixed: '{old_club}' -> '{new_club}'")
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

    remove_prefix()
