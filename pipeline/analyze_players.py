#!/usr/bin/env python3
"""
Analyze player distribution by nationality and period.
"""

import os
import re
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def fetch_all_players():
    """Fetch all players with nationality info."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    players = []
    offset = 0
    limit = 1000

    while True:
        url = f"{SUPABASE_URL}/rest/v1/players?select=id,name,nationality,nationality_code,nationality_flag&offset={offset}&limit={limit}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching players: {resp.status_code}")
            break

        batch = resp.json()
        if not batch:
            break

        players.extend(batch)
        offset += limit

        if len(batch) < limit:
            break

    return players


def fetch_career_entries():
    """Fetch all career entries to determine player periods."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    entries = []
    offset = 0
    limit = 1000

    while True:
        url = f"{SUPABASE_URL}/rest/v1/career_entries?select=player_id,years&offset={offset}&limit={limit}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching entries: {resp.status_code}")
            break

        batch = resp.json()
        if not batch:
            break

        entries.extend(batch)
        offset += limit

        if len(batch) < limit:
            break

    return entries


def extract_years(years_str):
    """Extract start and end years from a years string like '2010–2015'."""
    if not years_str:
        return None, None

    # Find all 4-digit years
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', years_str)
    if not years:
        return None, None

    years = [int(y) for y in years]
    return min(years), max(years)


def get_period(year):
    """Map a year to a period."""
    if year is None:
        return "Unknown"
    if year < 1980:
        return "Pre-1980"
    elif year < 1990:
        return "1980s"
    elif year < 2000:
        return "1990s"
    elif year < 2010:
        return "2000s"
    elif year < 2020:
        return "2010s"
    else:
        return "2020s"


def analyze():
    print("Fetching players...")
    players = fetch_all_players()
    print(f"Found {len(players)} players")

    print("Fetching career entries...")
    entries = fetch_career_entries()
    print(f"Found {len(entries)} career entries")

    # Build player period map (use earliest career year)
    player_periods = {}
    for entry in entries:
        player_id = entry["player_id"]
        start_year, end_year = extract_years(entry.get("years", ""))

        if start_year:
            if player_id not in player_periods:
                player_periods[player_id] = start_year
            else:
                player_periods[player_id] = min(player_periods[player_id], start_year)

    # Count by nationality
    nationality_counts = defaultdict(int)
    nationality_code_counts = defaultdict(int)

    # Count by period
    period_counts = defaultdict(int)

    # Count by nationality AND period
    nationality_period_counts = defaultdict(lambda: defaultdict(int))

    for player in players:
        # Nationality
        nat_code = player.get("nationality_code") or "Unknown"
        nat_flag = player.get("nationality_flag") or ""
        nationality = player.get("nationality") or "Unknown"

        nationality_counts[nationality] += 1
        nationality_code_counts[nat_code] += 1

        # Period
        player_id = player["id"]
        start_year = player_periods.get(player_id)
        period = get_period(start_year)
        period_counts[period] += 1

        # Combined
        nationality_period_counts[nat_code][period] += 1

    # Print results
    print("\n" + "="*60)
    print("PLAYERS BY NATIONALITY (Top 30)")
    print("="*60)
    sorted_nats = sorted(nationality_code_counts.items(), key=lambda x: -x[1])
    for nat_code, count in sorted_nats[:30]:
        # Find a sample player to get the flag
        flag = ""
        for p in players:
            if p.get("nationality_code") == nat_code:
                flag = p.get("nationality_flag") or ""
                break
        print(f"  {flag} {nat_code:4} : {count:4} players")

    if len(sorted_nats) > 30:
        other_count = sum(count for _, count in sorted_nats[30:])
        print(f"  ... and {len(sorted_nats) - 30} more countries with {other_count} players")

    print("\n" + "="*60)
    print("PLAYERS BY PERIOD")
    print("="*60)
    period_order = ["Pre-1980", "1980s", "1990s", "2000s", "2010s", "2020s", "Unknown"]
    for period in period_order:
        count = period_counts.get(period, 0)
        bar = "█" * (count // 20)
        print(f"  {period:10} : {count:4} players  {bar}")

    print("\n" + "="*60)
    print("TOP 10 NATIONALITIES BY PERIOD")
    print("="*60)
    top_10_nats = [nat for nat, _ in sorted_nats[:10]]

    # Header
    header = f"{'Country':8}"
    for period in period_order[:-1]:  # Skip Unknown
        header += f" {period:>8}"
    header += f" {'Total':>8}"
    print(header)
    print("-" * len(header))

    for nat_code in top_10_nats:
        # Find flag
        flag = ""
        for p in players:
            if p.get("nationality_code") == nat_code:
                flag = p.get("nationality_flag") or ""
                break

        row = f"{flag} {nat_code:5}"
        total = 0
        for period in period_order[:-1]:
            count = nationality_period_counts[nat_code].get(period, 0)
            total += count
            row += f" {count:>8}"
        row += f" {total:>8}"
        print(row)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Total players: {len(players)}")
    print(f"  Total nationalities: {len(nationality_code_counts)}")
    print(f"  Players with nationality code: {len(players) - nationality_code_counts.get('Unknown', 0)}")
    print(f"  Players missing nationality: {nationality_code_counts.get('Unknown', 0)}")


if __name__ == "__main__":
    analyze()
