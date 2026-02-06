#!/usr/bin/env python3
"""
Update existing players with nationality information from Wikidata.

Usage:
  python update_nationalities.py           # Update all players
  python update_nationalities.py test      # Test with first 5 players
  python update_nationalities.py dry       # Dry run (don't update DB)
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# Country code to flag emoji mapping
COUNTRY_FLAGS = {
    "AF": "🇦🇫", "AL": "🇦🇱", "DZ": "🇩🇿", "AD": "🇦🇩", "AO": "🇦🇴",
    "AR": "🇦🇷", "AM": "🇦🇲", "AU": "🇦🇺", "AT": "🇦🇹", "AZ": "🇦🇿",
    "BS": "🇧🇸", "BH": "🇧🇭", "BD": "🇧🇩", "BB": "🇧🇧", "BY": "🇧🇾",
    "BE": "🇧🇪", "BZ": "🇧🇿", "BJ": "🇧🇯", "BO": "🇧🇴", "BA": "🇧🇦",
    "BW": "🇧🇼", "BR": "🇧🇷", "BN": "🇧🇳", "BG": "🇧🇬", "BF": "🇧🇫",
    "BI": "🇧🇮", "KH": "🇰🇭", "CM": "🇨🇲", "CA": "🇨🇦", "CV": "🇨🇻",
    "CF": "🇨🇫", "TD": "🇹🇩", "CL": "🇨🇱", "CN": "🇨🇳", "CO": "🇨🇴",
    "KM": "🇰🇲", "CG": "🇨🇬", "CD": "🇨🇩", "CR": "🇨🇷", "CI": "🇨🇮",
    "HR": "🇭🇷", "CU": "🇨🇺", "CY": "🇨🇾", "CZ": "🇨🇿", "DK": "🇩🇰",
    "DJ": "🇩🇯", "DM": "🇩🇲", "DO": "🇩🇴", "EC": "🇪🇨", "EG": "🇪🇬",
    "SV": "🇸🇻", "GQ": "🇬🇶", "ER": "🇪🇷", "EE": "🇪🇪", "SZ": "🇸🇿",
    "ET": "🇪🇹", "FJ": "🇫🇯", "FI": "🇫🇮", "FR": "🇫🇷", "GA": "🇬🇦",
    "GM": "🇬🇲", "GE": "🇬🇪", "DE": "🇩🇪", "GH": "🇬🇭", "GR": "🇬🇷",
    "GD": "🇬🇩", "GT": "🇬🇹", "GN": "🇬🇳", "GW": "🇬🇼", "GY": "🇬🇾",
    "HT": "🇭🇹", "HN": "🇭🇳", "HU": "🇭🇺", "IS": "🇮🇸", "IN": "🇮🇳",
    "ID": "🇮🇩", "IR": "🇮🇷", "IQ": "🇮🇶", "IE": "🇮🇪", "IL": "🇮🇱",
    "IT": "🇮🇹", "JM": "🇯🇲", "JP": "🇯🇵", "JO": "🇯🇴", "KZ": "🇰🇿",
    "KE": "🇰🇪", "KI": "🇰🇮", "KP": "🇰🇵", "KR": "🇰🇷", "KW": "🇰🇼",
    "KG": "🇰🇬", "LA": "🇱🇦", "LV": "🇱🇻", "LB": "🇱🇧", "LS": "🇱🇸",
    "LR": "🇱🇷", "LY": "🇱🇾", "LI": "🇱🇮", "LT": "🇱🇹", "LU": "🇱🇺",
    "MG": "🇲🇬", "MW": "🇲🇼", "MY": "🇲🇾", "MV": "🇲🇻", "ML": "🇲🇱",
    "MT": "🇲🇹", "MH": "🇲🇭", "MR": "🇲🇷", "MU": "🇲🇺", "MX": "🇲🇽",
    "FM": "🇫🇲", "MD": "🇲🇩", "MC": "🇲🇨", "MN": "🇲🇳", "ME": "🇲🇪",
    "MA": "🇲🇦", "MZ": "🇲🇿", "MM": "🇲🇲", "NA": "🇳🇦", "NR": "🇳🇷",
    "NP": "🇳🇵", "NL": "🇳🇱", "NZ": "🇳🇿", "NI": "🇳🇮", "NE": "🇳🇪",
    "NG": "🇳🇬", "MK": "🇲🇰", "NO": "🇳🇴", "OM": "🇴🇲", "PK": "🇵🇰",
    "PW": "🇵🇼", "PA": "🇵🇦", "PG": "🇵🇬", "PY": "🇵🇾", "PE": "🇵🇪",
    "PH": "🇵🇭", "PL": "🇵🇱", "PT": "🇵🇹", "QA": "🇶🇦", "RO": "🇷🇴",
    "RU": "🇷🇺", "RW": "🇷🇼", "KN": "🇰🇳", "LC": "🇱🇨", "VC": "🇻🇨",
    "WS": "🇼🇸", "SM": "🇸🇲", "ST": "🇸🇹", "SA": "🇸🇦", "SN": "🇸🇳",
    "RS": "🇷🇸", "SC": "🇸🇨", "SL": "🇸🇱", "SG": "🇸🇬", "SK": "🇸🇰",
    "SI": "🇸🇮", "SB": "🇸🇧", "SO": "🇸🇴", "ZA": "🇿🇦", "SS": "🇸🇸",
    "ES": "🇪🇸", "LK": "🇱🇰", "SD": "🇸🇩", "SR": "🇸🇷", "SE": "🇸🇪",
    "CH": "🇨🇭", "SY": "🇸🇾", "TW": "🇹🇼", "TJ": "🇹🇯", "TZ": "🇹🇿",
    "TH": "🇹🇭", "TL": "🇹🇱", "TG": "🇹🇬", "TO": "🇹🇴", "TT": "🇹🇹",
    "TN": "🇹🇳", "TR": "🇹🇷", "TM": "🇹🇲", "TV": "🇹🇻", "UG": "🇺🇬",
    "UA": "🇺🇦", "AE": "🇦🇪", "GB": "🇬🇧", "US": "🇺🇸", "UY": "🇺🇾",
    "UZ": "🇺🇿", "VU": "🇻🇺", "VA": "🇻🇦", "VE": "🇻🇪", "VN": "🇻🇳",
    "YE": "🇾🇪", "ZM": "🇿🇲", "ZW": "🇿🇼",
    # Special cases for UK nations (football uses separate teams)
    "EN": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",  # England
    "SC": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",  # Scotland
    "WA": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",  # Wales
    "NI": "🇬🇧",  # Northern Ireland (uses GB flag usually)
    "XK": "🇽🇰",  # Kosovo
}

# Wikidata country QID to ISO code mapping (for common football nations)
WIKIDATA_COUNTRY_MAP = {
    "Q142": ("France", "FR"),
    "Q183": ("Germany", "DE"),
    "Q38": ("Italy", "IT"),
    "Q29": ("Spain", "ES"),
    "Q145": ("United Kingdom", "GB"),
    "Q21": ("England", "EN"),
    "Q22": ("Scotland", "SC"),
    "Q25": ("Wales", "WA"),
    "Q26": ("Northern Ireland", "NI"),
    "Q45": ("Portugal", "PT"),
    "Q55": ("Netherlands", "NL"),
    "Q31": ("Belgium", "BE"),
    "Q155": ("Brazil", "BR"),
    "Q414": ("Argentina", "AR"),
    "Q717": ("Venezuela", "VE"),
    "Q298": ("Chile", "CL"),
    "Q733": ("Paraguay", "PY"),
    "Q77": ("Uruguay", "UY"),
    "Q736": ("Ecuador", "EC"),
    "Q419": ("Peru", "PE"),
    "Q739": ("Colombia", "CO"),
    "Q96": ("Mexico", "MX"),
    "Q30": ("United States", "US"),
    "Q16": ("Canada", "CA"),
    "Q43": ("Turkey", "TR"),
    "Q159": ("Russia", "RU"),
    "Q212": ("Ukraine", "UA"),
    "Q36": ("Poland", "PL"),
    "Q34": ("Sweden", "SE"),
    "Q35": ("Denmark", "DK"),
    "Q20": ("Norway", "NO"),
    "Q33": ("Finland", "FI"),
    "Q39": ("Switzerland", "CH"),
    "Q40": ("Austria", "AT"),
    "Q41": ("Greece", "GR"),
    "Q224": ("Croatia", "HR"),
    "Q403": ("Serbia", "RS"),
    "Q225": ("Bosnia and Herzegovina", "BA"),
    "Q221": ("North Macedonia", "MK"),
    "Q229": ("Cyprus", "CY"),
    "Q222": ("Albania", "AL"),
    "Q1246": ("Kosovo", "XK"),
    "Q236": ("Montenegro", "ME"),
    "Q227": ("Azerbaijan", "AZ"),
    "Q399": ("Armenia", "AM"),
    "Q230": ("Georgia", "GE"),
    "Q37": ("Lithuania", "LT"),
    "Q211": ("Latvia", "LV"),
    "Q191": ("Estonia", "EE"),
    "Q184": ("Belarus", "BY"),
    "Q28": ("Hungary", "HU"),
    "Q218": ("Romania", "RO"),
    "Q219": ("Bulgaria", "BG"),
    "Q213": ("Czech Republic", "CZ"),
    "Q214": ("Slovakia", "SK"),
    "Q215": ("Slovenia", "SI"),
    "Q851": ("Saudi Arabia", "SA"),
    "Q878": ("United Arab Emirates", "AE"),
    "Q846": ("Qatar", "QA"),
    "Q817": ("Kuwait", "KW"),
    "Q148": ("China", "CN"),
    "Q17": ("Japan", "JP"),
    "Q884": ("South Korea", "KR"),
    "Q408": ("Australia", "AU"),
    "Q664": ("New Zealand", "NZ"),
    "Q79": ("Egypt", "EG"),
    "Q1028": ("Morocco", "MA"),
    "Q262": ("Algeria", "DZ"),
    "Q948": ("Tunisia", "TN"),
    "Q1029": ("Senegal", "SN"),
    "Q1008": ("Ivory Coast", "CI"),
    "Q1009": ("Cameroon", "CM"),
    "Q1030": ("Nigeria", "NG"),
    "Q1005": ("Gambia", "GM"),
    "Q1006": ("Guinea", "GN"),
    "Q1007": ("Mali", "ML"),
    "Q912": ("Ghana", "GH"),
    "Q258": ("South Africa", "ZA"),
    "Q954": ("Zimbabwe", "ZW"),
    "Q1033": ("Niger", "NE"),
    "Q929": ("Central African Republic", "CF"),
    "Q974": ("DR Congo", "CD"),
    "Q114": ("Kenya", "KE"),
    "Q115": ("Ethiopia", "ET"),
    "Q794": ("Iran", "IR"),
    "Q796": ("Iraq", "IQ"),
    "Q801": ("Israel", "IL"),
    "Q810": ("Jordan", "JO"),
    "Q805": ("Yemen", "YE"),
    "Q668": ("India", "IN"),
    "Q252": ("Indonesia", "ID"),
    "Q869": ("Thailand", "TH"),
    "Q833": ("Malaysia", "MY"),
    "Q928": ("Philippines", "PH"),
    "Q881": ("Vietnam", "VN"),
    "Q334": ("Singapore", "SG"),
    "Q574": ("East Timor", "TL"),
    "Q424": ("Cambodia", "KH"),
    "Q836": ("Myanmar", "MM"),
    "Q27": ("Ireland", "IE"),
    "Q189": ("Iceland", "IS"),
    "Q32": ("Luxembourg", "LU"),
    "Q233": ("Malta", "MT"),
}


def get_players_from_supabase(limit=None, missing_nationality_only=False):
    """Fetch players from Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    url = f"{SUPABASE_URL}/rest/v1/players?select=id,name,wikidata_id,nationality"
    if missing_nationality_only:
        url += "&nationality=is.null"
    if limit:
        url += f"&limit={limit}"

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    log.error(f"Failed to fetch players: {resp.status_code} {resp.text}")
    return []


def get_nationality_stats():
    """Get current nationality coverage stats."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    # Count total players
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/players?select=id",
        headers={**headers, "Prefer": "count=exact"},
    )
    total = int(resp.headers.get("content-range", "0/0").split("/")[-1])

    # Count players with nationality
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/players?select=id&nationality=not.is.null",
        headers={**headers, "Prefer": "count=exact"},
    )
    with_nationality = int(resp.headers.get("content-range", "0/0").split("/")[-1])

    return total, with_nationality


def update_player_nationality(player_id, nationality, nationality_code, nationality_flag):
    """Update a player's nationality in Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "nationality": nationality,
        "nationality_code": nationality_code,
        "nationality_flag": nationality_flag,
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/players?id=eq.{player_id}",
        headers=headers,
        json=data
    )
    return resp.status_code in (200, 204)


def fetch_nationality_from_wikidata(wikidata_id):
    """Fetch player's nationality from Wikidata using their QID."""
    if not wikidata_id:
        return None, None, None

    # P27 = country of citizenship
    query = f"""
    SELECT ?country ?countryLabel WHERE {{
      wd:{wikidata_id} wdt:P27 ?country .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "CareerQuizBot/1.0 (https://github.com/adroual/career-quiz; adroual@gmail.com)"
    }

    try:
        resp = requests.get(WIKIDATA_SPARQL_URL, params={"query": query}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", {}).get("bindings", [])
        if results:
            country_uri = results[0]["country"]["value"]
            country_qid = country_uri.split("/")[-1]
            country_label = results[0].get("countryLabel", {}).get("value", "")

            # Look up the country code
            if country_qid in WIKIDATA_COUNTRY_MAP:
                name, code = WIKIDATA_COUNTRY_MAP[country_qid]
                flag = COUNTRY_FLAGS.get(code, "🏳️")
                return name, code, flag

            # Fallback: use the label
            return country_label, "", "🏳️"

    except Exception as e:
        log.warning(f"Wikidata query failed for {wikidata_id}: {e}")

    return None, None, None


def fetch_nationality_by_name(player_name):
    """Fetch player's nationality from Wikidata by searching their name."""
    query = f"""
    SELECT ?player ?country ?countryLabel WHERE {{
      ?player wdt:P106 wd:Q937857 .
      ?player rdfs:label "{player_name}"@en .
      ?player wdt:P27 ?country .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 1
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "CareerQuizBot/1.0 (https://github.com/adroual/career-quiz; adroual@gmail.com)"
    }

    try:
        resp = requests.get(WIKIDATA_SPARQL_URL, params={"query": query}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", {}).get("bindings", [])
        if results:
            country_uri = results[0]["country"]["value"]
            country_qid = country_uri.split("/")[-1]

            if country_qid in WIKIDATA_COUNTRY_MAP:
                name, code = WIKIDATA_COUNTRY_MAP[country_qid]
                flag = COUNTRY_FLAGS.get(code, "🏳️")
                return name, code, flag

    except Exception as e:
        log.warning(f"Wikidata name search failed for {player_name}: {e}")

    return None, None, None


def run_update(dry_run=False, limit=None):
    """Update all players with nationality information."""
    log.info("=== Updating Player Nationalities ===")

    # Show current stats
    total, with_nationality = get_nationality_stats()
    coverage = (with_nationality / total * 100) if total > 0 else 0
    log.info(f"Current coverage: {with_nationality}/{total} ({coverage:.1f}%)")
    target = int(total * 0.8)
    log.info(f"Target (80%): {target} players")

    # Fetch only players missing nationality
    players = get_players_from_supabase(limit, missing_nationality_only=True)
    log.info(f"Found {len(players)} players without nationality")

    if len(players) == 0:
        log.info("All players already have nationality data!")
        return

    updated = 0
    skipped = 0
    failed = 0

    for i, player in enumerate(players):
        if i % 50 == 0:
            log.info(f"Progress: {i}/{len(players)} (updated: {updated}, failed: {failed})")

        # Try to fetch nationality (no need to check if player has it - query filters)
        wikidata_id = player.get("wikidata_id")
        nationality, code, flag = fetch_nationality_from_wikidata(wikidata_id)

        # Fallback: search by name
        if not nationality:
            nationality, code, flag = fetch_nationality_by_name(player["name"])

        if nationality:
            if dry_run:
                log.info(f"  Would update: {player['name']} -> {flag} {nationality} ({code})")
            else:
                if update_player_nationality(player["id"], nationality, code, flag):
                    updated += 1
                    log.info(f"  Updated: {player['name']} -> {flag} {nationality}")
                else:
                    failed += 1
                    log.warning(f"  Failed to update: {player['name']}")
        else:
            log.warning(f"  No nationality found for: {player['name']}")
            failed += 1

        # Rate limiting
        time.sleep(0.3)

    # Show final stats
    total, with_nationality = get_nationality_stats()
    coverage = (with_nationality / total * 100) if total > 0 else 0
    log.info(f"=== Done ===")
    log.info(f"Updated: {updated}, Failed: {failed}")
    log.info(f"Final coverage: {with_nationality}/{total} ({coverage:.1f}%)")
    target = int(total * 0.8)
    if coverage >= 80:
        log.info("Target reached! Coverage is at 80% or above.")
    else:
        log.info(f"Still need {target - with_nationality} more players to reach 80%")


if __name__ == "__main__":
    import sys

    if not SUPABASE_KEY:
        log.error("SUPABASE_SERVICE_KEY not set in environment")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_update(dry_run=False, limit=5)
    elif len(sys.argv) > 1 and sys.argv[1] == "dry":
        run_update(dry_run=True, limit=20)
    else:
        run_update(dry_run=False)
