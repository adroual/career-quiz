#!/usr/bin/env python3
"""
Career Quiz Analytics Report Generator

Generates comprehensive usage and growth analytics.
Run periodically to track metrics over time.

Usage:
  python analytics_report.py           # Full report to console
  python analytics_report.py --json    # JSON output for programmatic use
  python analytics_report.py --save    # Save report to file with timestamp
"""

import os
import json
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tjxdbdueayzlxgywigth.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


@dataclass
class DailyStats:
    date: str
    new_parties: int
    new_members: int
    unique_nicknames: int
    games_played: int
    correct_answers: int


@dataclass
class AnalyticsReport:
    generated_at: str

    # Totals
    total_parties: int
    total_members: int
    total_games: int
    total_correct: int

    # Unique counts
    unique_nicknames: int
    unique_players: int
    estimated_real_users: int

    # Party breakdown
    solo_parties: int
    multi_player_parties: int
    users_in_multi_player: int

    # Engagement
    avg_games_per_player: float
    correct_rate: float

    # Daily stats
    daily_stats: list

    # Top users
    top_players: list

    # Duplicate indicators
    duplicate_nicknames: dict


class SupabaseClient:
    def __init__(self):
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }

    def fetch_all(self, table: str, select: str = "*", order: str = None) -> list:
        """Fetch all records from a table."""
        url = f"{SUPABASE_URL}/rest/v1/{table}?select={select}"
        if order:
            url += f"&order={order}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        return []

    def count(self, table: str) -> int:
        """Get count of records in a table."""
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?select=id",
            headers={**self.headers, "Prefer": "count=exact"}
        )
        if resp.status_code == 200:
            return int(resp.headers.get("content-range", "0/0").split("/")[-1])
        return 0


def generate_report() -> AnalyticsReport:
    """Generate comprehensive analytics report."""
    client = SupabaseClient()

    # Fetch all data
    parties = client.fetch_all("parties", order="created_at.asc")
    members = client.fetch_all("party_members", order="joined_at.asc")
    scores = client.fetch_all("scores", order="answered_at.asc")

    # Basic counts
    total_parties = len(parties)
    total_members = len(members)
    total_games = len(scores)
    total_correct = sum(1 for s in scores if s.get("is_correct"))

    # Unique counts
    all_nicknames = [m["nickname"].lower().strip() for m in members if m.get("nickname")]
    nickname_counts = Counter(all_nicknames)
    unique_nicknames = len(nickname_counts)
    unique_players = len(set(s["member_id"] for s in scores))

    # Filter test names for real user estimate
    test_names = {"test", "t", "r", "", "asdf", "aaa", "xxx"}
    filtered_nicknames = [n for n in set(all_nicknames) if n not in test_names]
    estimated_real_users = len(filtered_nicknames)

    # Party breakdown
    party_member_count = defaultdict(int)
    for member in members:
        party_member_count[member["party_id"]] += 1

    solo_parties = sum(1 for p in parties if party_member_count.get(p["id"], 0) == 1)
    multi_player_parties = sum(1 for p in parties if party_member_count.get(p["id"], 0) > 1)
    users_in_multi_player = sum(
        count for pid, count in party_member_count.items()
        if count > 1
    )

    # Engagement metrics
    avg_games = total_games / unique_players if unique_players > 0 else 0
    correct_rate = total_correct / total_games * 100 if total_games > 0 else 0

    # Daily stats (last 14 days)
    now = datetime.now(timezone.utc)
    daily_stats = []

    # Group by date
    parties_by_date = defaultdict(list)
    for p in parties:
        date = p["created_at"][:10]
        parties_by_date[date].append(p)

    members_by_date = defaultdict(list)
    for m in members:
        date = m["joined_at"][:10]
        members_by_date[date].append(m)

    scores_by_date = defaultdict(list)
    for s in scores:
        date = s["answered_at"][:10]
        scores_by_date[date].append(s)

    for i in range(13, -1, -1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        day_members = members_by_date.get(date, [])
        day_scores = scores_by_date.get(date, [])

        daily_stats.append(DailyStats(
            date=date,
            new_parties=len(parties_by_date.get(date, [])),
            new_members=len(day_members),
            unique_nicknames=len(set(m["nickname"].lower().strip() for m in day_members if m.get("nickname"))),
            games_played=len(day_scores),
            correct_answers=sum(1 for s in day_scores if s.get("is_correct"))
        ))

    # Top players
    games_per_player = Counter(s["member_id"] for s in scores)
    top_players = []
    for member_id, count in games_per_player.most_common(10):
        member = next((m for m in members if m["id"] == member_id), None)
        nickname = member["nickname"] if member else "Unknown"
        correct = sum(1 for s in scores if s["member_id"] == member_id and s.get("is_correct"))
        top_players.append({
            "nickname": nickname,
            "games": count,
            "correct": correct,
            "accuracy": round(correct / count * 100, 1) if count > 0 else 0
        })

    # Duplicate indicators
    duplicate_nicknames = {n: c for n, c in nickname_counts.items() if c > 1}

    return AnalyticsReport(
        generated_at=now.isoformat(),
        total_parties=total_parties,
        total_members=total_members,
        total_games=total_games,
        total_correct=total_correct,
        unique_nicknames=unique_nicknames,
        unique_players=unique_players,
        estimated_real_users=estimated_real_users,
        solo_parties=solo_parties,
        multi_player_parties=multi_player_parties,
        users_in_multi_player=users_in_multi_player,
        avg_games_per_player=round(avg_games, 2),
        correct_rate=round(correct_rate, 1),
        daily_stats=[asdict(d) for d in daily_stats],
        top_players=top_players,
        duplicate_nicknames=duplicate_nicknames
    )


def print_report(report: AnalyticsReport):
    """Print formatted report to console."""
    print("=" * 70)
    print("🎯 CAREER QUIZ - ANALYTICS REPORT")
    print(f"   Generated: {report.generated_at[:19]}")
    print("=" * 70)

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                         KEY METRICS                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Estimated Real Users:     {report.estimated_real_users:>5}                                   ║
║  Total Games Played:       {report.total_games:>5}                                   ║
║  Correct Answer Rate:      {report.correct_rate:>5.1f}%                                  ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    print("=" * 70)
    print("📊 DETAILED METRICS")
    print("=" * 70)
    print(f"""
Raw Counts:
  • Parties created:          {report.total_parties:>5}
  • Member entries:           {report.total_members:>5}
  • Games played:             {report.total_games:>5}
  • Correct answers:          {report.total_correct:>5}

User Analysis:
  • Unique nicknames:         {report.unique_nicknames:>5}
  • Active players:           {report.unique_players:>5}
  • Estimated real users:     {report.estimated_real_users:>5}

Party Breakdown:
  • Solo parties:             {report.solo_parties:>5}
  • Multi-player parties:     {report.multi_player_parties:>5}
  • Users in multi-player:    {report.users_in_multi_player:>5}

Engagement:
  • Avg games per player:     {report.avg_games_per_player:>5.1f}
  • Correct rate:             {report.correct_rate:>5.1f}%
""")

    print("=" * 70)
    print("📅 DAILY STATS (Last 14 Days)")
    print("=" * 70)
    print(f"{'Date':<12} {'Parties':>8} {'Members':>8} {'Unique':>8} {'Games':>8} {'Correct':>8}")
    print("-" * 60)

    for day in report.daily_stats:
        if day["new_parties"] > 0 or day["games_played"] > 0:
            print(f"{day['date']:<12} {day['new_parties']:>8} {day['new_members']:>8} "
                  f"{day['unique_nicknames']:>8} {day['games_played']:>8} {day['correct_answers']:>8}")

    print("\n" + "=" * 70)
    print("🏆 TOP PLAYERS")
    print("=" * 70)
    print(f"{'Rank':<6} {'Nickname':<20} {'Games':>8} {'Correct':>8} {'Accuracy':>10}")
    print("-" * 60)

    for i, player in enumerate(report.top_players, 1):
        print(f"{i:<6} {player['nickname']:<20} {player['games']:>8} "
              f"{player['correct']:>8} {player['accuracy']:>9.1f}%")

    if report.duplicate_nicknames:
        print("\n" + "=" * 70)
        print("⚠️  DUPLICATE INDICATORS")
        print("=" * 70)
        for nickname, count in sorted(report.duplicate_nicknames.items(), key=lambda x: -x[1])[:10]:
            print(f"  • '{nickname}': {count} occurrences")


def save_report(report: AnalyticsReport, filename: Optional[str] = None):
    """Save report to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)

    print(f"Report saved to: {filename}")
    return filename


# SQL views for Supabase
SUPABASE_SQL_VIEWS = """
-- ============================================================
-- CAREER QUIZ ANALYTICS VIEWS
-- Run these in Supabase SQL Editor to create real-time analytics
-- ============================================================

-- View: Daily stats summary
CREATE OR REPLACE VIEW analytics_daily_stats AS
SELECT
    DATE(pm.joined_at) as date,
    COUNT(DISTINCT p.id) as new_parties,
    COUNT(DISTINCT pm.id) as new_members,
    COUNT(DISTINCT LOWER(TRIM(pm.nickname))) as unique_nicknames,
    COALESCE(games.games_played, 0) as games_played,
    COALESCE(games.correct_answers, 0) as correct_answers
FROM party_members pm
LEFT JOIN parties p ON DATE(p.created_at) = DATE(pm.joined_at)
LEFT JOIN (
    SELECT
        DATE(answered_at) as date,
        COUNT(*) as games_played,
        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers
    FROM scores
    GROUP BY DATE(answered_at)
) games ON games.date = DATE(pm.joined_at)
GROUP BY DATE(pm.joined_at), games.games_played, games.correct_answers
ORDER BY date DESC;

-- View: Overall metrics
CREATE OR REPLACE VIEW analytics_overview AS
SELECT
    (SELECT COUNT(*) FROM parties) as total_parties,
    (SELECT COUNT(*) FROM party_members) as total_members,
    (SELECT COUNT(DISTINCT LOWER(TRIM(nickname))) FROM party_members) as unique_nicknames,
    (SELECT COUNT(*) FROM scores) as total_games,
    (SELECT COUNT(*) FROM scores WHERE is_correct = true) as correct_answers,
    (SELECT COUNT(DISTINCT member_id) FROM scores) as active_players,
    (SELECT COUNT(*) FROM parties p
     WHERE (SELECT COUNT(*) FROM party_members pm WHERE pm.party_id = p.id) = 1) as solo_parties,
    (SELECT COUNT(*) FROM parties p
     WHERE (SELECT COUNT(*) FROM party_members pm WHERE pm.party_id = p.id) > 1) as multi_player_parties;

-- View: Top players leaderboard
CREATE OR REPLACE VIEW analytics_top_players AS
SELECT
    pm.nickname,
    COUNT(s.id) as games_played,
    SUM(CASE WHEN s.is_correct THEN 1 ELSE 0 END) as correct_answers,
    ROUND(100.0 * SUM(CASE WHEN s.is_correct THEN 1 ELSE 0 END) / COUNT(s.id), 1) as accuracy,
    SUM(s.points) as total_points
FROM scores s
JOIN party_members pm ON s.member_id = pm.id
GROUP BY pm.id, pm.nickname
ORDER BY games_played DESC
LIMIT 50;

-- View: Duplicate nickname detection
CREATE OR REPLACE VIEW analytics_duplicate_nicknames AS
SELECT
    LOWER(TRIM(nickname)) as nickname,
    COUNT(*) as occurrences
FROM party_members
WHERE nickname IS NOT NULL AND nickname != ''
GROUP BY LOWER(TRIM(nickname))
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- View: Party sizes distribution
CREATE OR REPLACE VIEW analytics_party_sizes AS
SELECT
    member_count,
    COUNT(*) as party_count
FROM (
    SELECT
        p.id,
        COUNT(pm.id) as member_count
    FROM parties p
    LEFT JOIN party_members pm ON pm.party_id = p.id
    GROUP BY p.id
) party_sizes
GROUP BY member_count
ORDER BY member_count;

-- Function: Get analytics summary (can be called via RPC)
CREATE OR REPLACE FUNCTION get_analytics_summary()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'generated_at', NOW(),
        'total_parties', (SELECT COUNT(*) FROM parties),
        'total_members', (SELECT COUNT(*) FROM party_members),
        'unique_nicknames', (SELECT COUNT(DISTINCT LOWER(TRIM(nickname))) FROM party_members),
        'total_games', (SELECT COUNT(*) FROM scores),
        'correct_answers', (SELECT COUNT(*) FROM scores WHERE is_correct = true),
        'active_players', (SELECT COUNT(DISTINCT member_id) FROM scores),
        'correct_rate', (
            SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE is_correct) / NULLIF(COUNT(*), 0), 1)
            FROM scores
        )
    ) INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Grant access to authenticated users (optional)
-- GRANT SELECT ON analytics_daily_stats TO authenticated;
-- GRANT SELECT ON analytics_overview TO authenticated;
-- GRANT SELECT ON analytics_top_players TO authenticated;
"""


def print_sql_views():
    """Print SQL views for Supabase."""
    print(SUPABASE_SQL_VIEWS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Career Quiz Analytics Report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--sql", action="store_true", help="Print SQL views for Supabase")
    args = parser.parse_args()

    if args.sql:
        print_sql_views()
    else:
        report = generate_report()

        if args.json:
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
        else:
            print_report(report)

        if args.save:
            save_report(report)
