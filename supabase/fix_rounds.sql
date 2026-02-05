-- ============================================================
-- FIX 1: Update career_club_count for all players
-- ============================================================

UPDATE public.players p
SET career_club_count = (
  SELECT COUNT(*)::smallint
  FROM public.career_entries ce
  WHERE ce.player_id = p.id
);

-- Verify the update
SELECT
  COUNT(*) as total_players,
  COUNT(*) FILTER (WHERE career_club_count >= 2) as players_with_2plus_clubs,
  COUNT(*) FILTER (WHERE career_club_count = 0) as players_with_no_clubs
FROM public.players;

-- ============================================================
-- FIX 2: Improved generate_daily_rounds function
-- More robust error handling and logging
-- ============================================================

CREATE OR REPLACE FUNCTION public.generate_daily_rounds(
  p_party_id uuid,
  p_date date DEFAULT current_date
)
RETURNS void AS $$
DECLARE
  v_rounds_per_day smallint;
  v_diff_min smallint;
  v_diff_max smallint;
  v_player_ids uuid[];
  v_count int;
BEGIN
  -- Get party config
  SELECT rounds_per_day, difficulty_min, difficulty_max
  INTO v_rounds_per_day, v_diff_min, v_diff_max
  FROM public.parties
  WHERE id = p_party_id AND is_active = true;

  IF NOT FOUND THEN
    RETURN;  -- Party not found or inactive
  END IF;

  -- Check if rounds already exist for this date
  SELECT COUNT(*) INTO v_count
  FROM public.daily_rounds
  WHERE party_id = p_party_id AND round_date = p_date;

  IF v_count > 0 THEN
    RETURN;  -- Rounds already exist, nothing to do
  END IF;

  -- Select random players not used in last 30 days
  SELECT array_agg(id) INTO v_player_ids
  FROM (
    SELECT p.id
    FROM public.players p
    WHERE p.is_active = true
      AND p.difficulty BETWEEN v_diff_min AND v_diff_max
      AND p.career_club_count >= 2
      AND p.id NOT IN (
        SELECT dr.player_id
        FROM public.daily_rounds dr
        WHERE dr.party_id = p_party_id
          AND dr.round_date > p_date - interval '30 days'
      )
    ORDER BY random()
    LIMIT v_rounds_per_day
  ) sub;

  -- If no players found, try without the 30-day restriction
  IF v_player_ids IS NULL OR array_length(v_player_ids, 1) IS NULL THEN
    SELECT array_agg(id) INTO v_player_ids
    FROM (
      SELECT p.id
      FROM public.players p
      WHERE p.is_active = true
        AND p.career_club_count >= 2
      ORDER BY random()
      LIMIT v_rounds_per_day
    ) sub;
  END IF;

  -- Still no players? Exit gracefully
  IF v_player_ids IS NULL OR array_length(v_player_ids, 1) IS NULL THEN
    RETURN;
  END IF;

  -- Insert rounds
  INSERT INTO public.daily_rounds (party_id, round_date, round_number, player_id)
  SELECT p_party_id, p_date, row_number() OVER (), unnest(v_player_ids);

END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FIX 3: Grant execute permission on the function
-- ============================================================

GRANT EXECUTE ON FUNCTION public.generate_daily_rounds(uuid, date) TO anon;
GRANT EXECUTE ON FUNCTION public.generate_daily_rounds(uuid, date) TO authenticated;

-- ============================================================
-- Test: Generate rounds for all active parties
-- ============================================================

SELECT public.generate_all_daily_rounds();

-- Verify rounds were created
SELECT
  p.name as party_name,
  dr.round_date,
  COUNT(*) as rounds_count
FROM public.daily_rounds dr
JOIN public.parties p ON p.id = dr.party_id
WHERE dr.round_date = current_date
GROUP BY p.name, dr.round_date;
