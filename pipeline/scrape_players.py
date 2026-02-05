#!/usr/bin/env python3
"""
Career Quiz — Data Pipeline (uses requests directly, no supabase lib)
Fetches football player career data from Wikidata + Wikipedia.

Usage:
  python scrape_players.py          # Full run
  python scrape_players.py test     # Test single player
  python scrape_players.py dry      # Dry run (JSON only)
"""

import re
import json
import time
import logging
import os
from typing import Optional
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

LEAGUES = {
    "Q13394": "Ligue 1", "Q82595": "Bundesliga", "Q15804": "Serie A",
    "Q324867": "La Liga", "Q9448": "Premier League",
}

COUNTRY_FLAGS = {
    "FR": "🇫🇷", "DE": "🇩🇪", "IT": "🇮🇹", "ES": "🇪🇸", "EN": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "PT": "🇵🇹", "NL": "🇳🇱", "BE": "🇧🇪", "BR": "🇧🇷", "AR": "🇦🇷",
    "US": "🇺🇸", "TR": "🇹🇷", "RU": "🇷🇺", "UA": "🇺🇦", "PL": "🇵🇱",
    "SE": "🇸🇪", "CH": "🇨🇭", "GR": "🇬🇷", "HR": "🇭🇷", "RS": "🇷🇸",
    "SA": "🇸🇦", "CN": "🇨🇳", "CA": "🇨🇦", "SC": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
}

KNOWN_CLUBS_COUNTRY = {
    "AS Cannes": "FR", "Girondins de Bordeaux": "FR", "Paris Saint-Germain": "FR",
    "Marseille": "FR", "Monaco": "FR", "Lyon": "FR", "Lille": "FR", "Nice": "FR",
    "Le Mans": "FR", "Guingamp": "FR", "Auxerre": "FR", "Strasbourg": "FR",
    "Manchester United": "EN", "Arsenal": "EN", "Chelsea": "EN", "Liverpool": "EN",
    "Manchester City": "EN", "Tottenham": "EN", "Everton": "EN", "Newcastle United": "EN",
    "Juventus": "IT", "AC Milan": "IT", "Inter Milan": "IT", "Inter": "IT",
    "Roma": "IT", "Lazio": "IT", "Napoli": "IT", "Fiorentina": "IT",
    "Real Madrid": "ES", "Barcelona": "ES", "Atlético Madrid": "ES", "Sevilla": "ES",
    "Valencia": "ES", "Villarreal": "ES", "Espanyol": "ES", "Mallorca": "ES",
    "Bayern Munich": "DE", "Borussia Dortmund": "DE", "Bayer Leverkusen": "DE",
    "Schalke 04": "DE", "Wolfsburg": "DE", "Werder Bremen": "DE",
    "Ajax": "NL", "PSV Eindhoven": "NL", "Feyenoord": "NL",
    "Porto": "PT", "Benfica": "PT", "Sporting CP": "PT",
    "Galatasaray": "TR", "Celtic": "SC", "Rangers": "SC",
    "LA Galaxy": "US", "New York Red Bulls": "US", "New York City FC": "US",
    "Montreal Impact": "CA", "Flamengo": "BR", "Grêmio": "BR", "Atlético Mineiro": "BR",
    "Al Nassr": "SA", "Shanghai Shenhua": "CN", "Malmö FF": "SE",
    "Lech Poznań": "PL", "Znicz Pruszków": "PL", "Anzhi Makhachkala": "RU",
}


@dataclass
class CareerEntry:
    years: str
    club: str
    country_code: str = ""
    country_flag: str = ""
    matches: int = 0
    goals: int = 0
    chronological_order: int = 0
    sort_order: int = 0


@dataclass
class Player:
    name: str
    aliases: list = field(default_factory=list)
    wikipedia_title: str = ""
    wikidata_id: str = ""
    difficulty: int = 3
    career: list = field(default_factory=list)


def supabase_insert(table: str, data: dict) -> dict:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers, json=data)
    if resp.status_code in (200, 201):
        return resp.json()[0] if resp.json() else {}
    log.error(f"Supabase insert failed: {resp.status_code} {resp.text}")
    return {}


def fetch_players_from_wikidata(league_qid: str, limit: int = 500) -> list[dict]:
    query = f"""
    SELECT DISTINCT ?player ?playerLabel ?article WHERE {{
      ?player wdt:P106 wd:Q937857 .
      ?player wdt:P118 wd:{league_qid} .
      ?article schema:about ?player ;
               schema:isPartOf <https://en.wikipedia.org/> .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT {limit}
    """
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "CareerQuizBot/1.0 (https://github.com/adroual/career-quiz; adroual@gmail.com)"
    }
    try:
        resp = requests.get(WIKIDATA_SPARQL_URL, params={"query": query},
                          headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.error(f"Wikidata query failed: {e}")
        return []

    players = []
    for result in data.get("results", {}).get("bindings", []):
        qid = result["player"]["value"].split("/")[-1]
        name = result.get("playerLabel", {}).get("value", "")
        article_url = result.get("article", {}).get("value", "")
        wiki_title = article_url.split("/wiki/")[-1] if "/wiki/" in article_url else ""
        if name and wiki_title:
            players.append({"qid": qid, "name": name, "wikipedia_title": wiki_title})

    log.info(f"Wikidata: Found {len(players)} players for {LEAGUES.get(league_qid, league_qid)}")
    return players


def fetch_all_league_players(limit_per_league: int = 500) -> dict:
    all_players = {}
    for qid, name in LEAGUES.items():
        log.info(f"Fetching {name} players...")
        for p in fetch_players_from_wikidata(qid, limit_per_league):
            if p["qid"] not in all_players:
                all_players[p["qid"]] = p
        time.sleep(2)
    log.info(f"Total unique players: {len(all_players)}")
    return all_players


def fetch_wikipedia_wikitext(title: str) -> Optional[str]:
    params = {"action": "query", "titles": title, "prop": "revisions",
              "rvprop": "content", "format": "json", "formatversion": "2"}
    headers = {
        "User-Agent": "CareerQuizBot/1.0 (https://github.com/adroual/career-quiz; adroual@gmail.com)"
    }
    try:
        resp = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", [])
        if pages and "revisions" in pages[0]:
            return pages[0]["revisions"][0].get("content", "")
    except Exception as e:
        log.warning(f"Wikipedia API failed for {title}: {e}")
    return None


def parse_career_from_wikitext(wikitext: str) -> list[CareerEntry]:
    entries = []
    for i in range(1, 30):
        years = _extract_field(wikitext, f"years{i}")
        clubs = _extract_field(wikitext, f"clubs{i}")
        caps = _extract_field(wikitext, f"caps{i}")
        goals = _extract_field(wikitext, f"goals{i}")

        if not clubs:
            break
        club_name = _clean_club_name(clubs)
        if not club_name:
            continue

        country_code = _guess_country(club_name)
        entries.append(CareerEntry(
            years=_clean_years(years) if years else "",
            club=club_name,
            country_code=country_code,
            country_flag=COUNTRY_FLAGS.get(country_code, ""),
            matches=_parse_int(caps),
            goals=_parse_int(goals),
            chronological_order=i,
        ))
    return entries


def _extract_field(wikitext: str, field_name: str) -> Optional[str]:
    match = re.search(rf'\|\s*{re.escape(field_name)}\s*=\s*(.*?)(?=\n\s*\||\n\s*\}})', wikitext, re.DOTALL)
    return match.group(1).strip() if match else None


def _clean_club_name(raw: str) -> str:
    raw = re.sub(r'→\s*', '', raw)
    raw = re.sub(r'\[\[([^\]|]*)\|([^\]]*)\]\]', r'\2', raw)
    raw = re.sub(r'\[\[([^\]]*)\]\]', r'\1', raw)
    raw = re.sub(r"<[^>]+>|\{\{[^}]*\}\}|'''?|\(loan\)", "", raw, flags=re.IGNORECASE)
    return raw.strip()


def _clean_years(raw: str) -> str:
    raw = re.sub(r'\[\[([^\]]*)\]\]|\{\{[^}]*\}\}', r'\1', raw)
    return re.sub(r'[–—]', '–', raw).strip()


def _parse_int(raw: Optional[str]) -> int:
    if not raw:
        return 0
    # Extract just the first number (avoid concatenating multiple numbers)
    match = re.search(r'\d+', raw)
    if not match:
        return 0
    value = int(match.group())
    # Sanity check: cap at reasonable max (no player has 2000+ apps/goals per club)
    return min(value, 2000)


def _guess_country(club_name: str) -> str:
    if club_name in KNOWN_CLUBS_COUNTRY:
        return KNOWN_CLUBS_COUNTRY[club_name]
    for known, code in KNOWN_CLUBS_COUNTRY.items():
        if known.lower() in club_name.lower() or club_name.lower() in known.lower():
            return code
    return ""


def generate_aliases(name: str) -> list[str]:
    import unicodedata
    aliases = [name.lower()]
    parts = name.split()
    if len(parts) > 1:
        aliases.append(parts[-1].lower())
    if len(parts) > 2:
        aliases.append(f"{parts[0]} {parts[-1]}".lower())
    for alias in list(aliases):
        ascii_ver = unicodedata.normalize('NFD', alias).encode('ascii', 'ignore').decode('ascii')
        if ascii_ver != alias:
            aliases.append(ascii_ver)
    return list(set(aliases))


def compute_difficulty(career: list[CareerEntry]) -> int:
    total_apps = sum(e.matches for e in career)
    top_clubs = {"Real Madrid", "Barcelona", "Manchester United", "Liverpool", "Chelsea",
                 "Arsenal", "Bayern Munich", "Juventus", "AC Milan", "Inter Milan", "Paris Saint-Germain"}
    top_count = sum(1 for e in career if any(tc.lower() in e.club.lower() for tc in top_clubs))
    if total_apps > 400 and top_count >= 2:
        return 1
    elif total_apps > 250 and top_count >= 1:
        return 2
    elif total_apps > 150:
        return 3
    elif total_apps > 80:
        return 4
    return 5


def compute_reveal_order(career: list[CareerEntry]) -> list[CareerEntry]:
    top_rank = {"Real Madrid": 10, "Barcelona": 10, "Manchester United": 9, "Liverpool": 9,
                "Bayern Munich": 9, "Juventus": 9, "Chelsea": 8, "AC Milan": 8, "Inter Milan": 8,
                "Arsenal": 8, "Paris Saint-Germain": 8, "Manchester City": 8}

    def fame(e):
        f = max((rank for club, rank in top_rank.items() if club.lower() in e.club.lower()), default=0)
        return f + e.matches / 100

    sorted_career = sorted(career, key=fame)
    for i, entry in enumerate(sorted_career):
        entry.sort_order = i + 1
    return sorted_career


def upload_to_supabase(players: list[Player]):
    if not SUPABASE_KEY:
        log.warning("No Supabase key. Saving to JSON.")
        save_to_json(players)
        return

    uploaded = 0
    for player in players:
        result = supabase_insert("players", {
            "name": player.name, "aliases": player.aliases, "wikipedia_title": player.wikipedia_title,
            "wikidata_id": player.wikidata_id, "difficulty": player.difficulty,
            "career_club_count": len(player.career),
        })
        if not result or not result.get("id"):
            continue

        for entry in player.career:
            supabase_insert("career_entries", {
                "player_id": result["id"], "sort_order": entry.sort_order,
                "chronological_order": entry.chronological_order, "years": entry.years,
                "club": entry.club, "country_code": entry.country_code,
                "country_flag": entry.country_flag, "matches": entry.matches, "goals": entry.goals,
            })

        uploaded += 1
        if uploaded % 20 == 0:
            log.info(f"Uploaded: {uploaded}/{len(players)}")

    log.info(f"Done! Uploaded {uploaded} players")


def save_to_json(players: list[Player], filename: str = "players_data.json"):
    data = [{"name": p.name, "aliases": p.aliases, "difficulty": p.difficulty,
             "career": [{"years": e.years, "club": e.club, "country_flag": e.country_flag,
                        "matches": e.matches, "goals": e.goals, "sort_order": e.sort_order}
                       for e in p.career]} for p in players]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {len(data)} players to {filename}")


def run_pipeline(limit_per_league: int = 200, upload: bool = True):
    log.info("=== Starting Pipeline ===")
    raw_players = fetch_all_league_players(limit_per_league)

    enriched = []
    for i, (qid, info) in enumerate(raw_players.items()):
        if i % 100 == 0:
            log.info(f"Progress: {i}/{len(raw_players)}")

        wikitext = fetch_wikipedia_wikitext(info["wikipedia_title"])
        if not wikitext:
            continue

        career = parse_career_from_wikitext(wikitext)
        if len(career) < 2 or len(career) > 15:
            continue

        career = compute_reveal_order(career)
        enriched.append(Player(
            name=info["name"], aliases=generate_aliases(info["name"]),
            wikipedia_title=info["wikipedia_title"], wikidata_id=qid,
            difficulty=compute_difficulty(career), career=career,
        ))
        time.sleep(0.5)

    log.info(f"Enriched {len(enriched)} players")
    upload_to_supabase(enriched) if upload else save_to_json(enriched)


def test_single_player(title: str = "Zinédine_Zidane"):
    wikitext = fetch_wikipedia_wikitext(title)
    if not wikitext:
        return log.error("Failed to fetch")

    career = compute_reveal_order(parse_career_from_wikitext(wikitext))
    print(f"\n{title.replace('_', ' ')} - {len(career)} clubs")
    for e in career:
        print(f"  {e.sort_order}. {e.country_flag} {e.club:<25} {e.years:<12} {e.matches}({e.goals})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_single_player(sys.argv[2] if len(sys.argv) > 2 else "Zinédine_Zidane")
    elif len(sys.argv) > 1 and sys.argv[1] == "dry":
        run_pipeline(limit_per_league=30, upload=False)
    else:
        run_pipeline(upload=True)
