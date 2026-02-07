
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

