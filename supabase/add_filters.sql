-- ============================================================
-- Add Party Filters: Year Range & Leagues
-- ============================================================

-- 1. Add metadata columns to players table
ALTER TABLE public.players
ADD COLUMN IF NOT EXISTS career_start_year smallint,
ADD COLUMN IF NOT EXISTS career_end_year smallint,
ADD COLUMN IF NOT EXISTS leagues_played text[] DEFAULT '{}';

-- 2. Populate career_start_year and career_end_year from career_entries
UPDATE public.players p
SET
  career_start_year = sub.start_year,
  career_end_year = sub.end_year
FROM (
  SELECT
    player_id,
    MIN(CAST(NULLIF(regexp_replace(split_part(years, '–', 1), '[^0-9]', '', 'g'), '') AS int)) as start_year,
    MAX(CAST(NULLIF(regexp_replace(
      CASE
        WHEN split_part(years, '–', 2) = '' THEN split_part(years, '–', 1)
        ELSE split_part(years, '–', 2)
      END, '[^0-9]', '', 'g'), '') AS int)) as end_year
  FROM public.career_entries
  WHERE years IS NOT NULL AND years != ''
  GROUP BY player_id
) sub
WHERE p.id = sub.player_id;

-- 3. Populate leagues_played (using country_code as league proxy)
UPDATE public.players p
SET leagues_played = sub.leagues
FROM (
  SELECT
    player_id,
    array_agg(DISTINCT country_code) FILTER (WHERE country_code IS NOT NULL AND country_code != '') as leagues
  FROM public.career_entries
  GROUP BY player_id
) sub
WHERE p.id = sub.player_id AND sub.leagues IS NOT NULL;

-- 4. Add filter columns to parties table
ALTER TABLE public.parties
ADD COLUMN IF NOT EXISTS filter_start_year_min smallint,
ADD COLUMN IF NOT EXISTS filter_start_year_max smallint,
ADD COLUMN IF NOT EXISTS filter_leagues text[] DEFAULT '{}';

-- 5. Verify the data was populated
SELECT
  COUNT(*) as total_players,
  COUNT(*) FILTER (WHERE career_start_year IS NOT NULL) as with_start_year,
  COUNT(*) FILTER (WHERE career_end_year IS NOT NULL) as with_end_year,
  COUNT(*) FILTER (WHERE array_length(leagues_played, 1) > 0) as with_leagues,
  MIN(career_start_year) as earliest_career,
  MAX(career_start_year) as latest_career
FROM public.players;

-- 6. Show available leagues/countries
SELECT
  unnest(leagues_played) as league,
  COUNT(*) as player_count
FROM public.players
WHERE leagues_played IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20;

-- 7. Update generate_daily_rounds function to use filters
CREATE OR REPLACE FUNCTION public.generate_daily_rounds(
  p_party_id uuid,
  p_date date DEFAULT current_date
)
RETURNS void AS $$
DECLARE
  v_rounds_per_day smallint;
  v_diff_min smallint;
  v_diff_max smallint;
  v_start_year_min smallint;
  v_start_year_max smallint;
  v_leagues text[];
  v_player record;
  v_round_num int := 1;
BEGIN
  -- Get party config including filters
  SELECT
    rounds_per_day,
    difficulty_min,
    difficulty_max,
    filter_start_year_min,
    filter_start_year_max,
    filter_leagues
  INTO
    v_rounds_per_day,
    v_diff_min,
    v_diff_max,
    v_start_year_min,
    v_start_year_max,
    v_leagues
  FROM public.parties
  WHERE id = p_party_id AND is_active = true;

  -- Exit if party not found
  IF NOT FOUND THEN
    RETURN;
  END IF;

  -- Exit if rounds already exist for this date
  IF EXISTS (
    SELECT 1 FROM public.daily_rounds
    WHERE party_id = p_party_id AND round_date = p_date
    LIMIT 1
  ) THEN
    RETURN;
  END IF;

  -- Insert rounds one by one with filters applied
  FOR v_player IN
    SELECT p.id
    FROM public.players p
    WHERE p.is_active = true
      AND p.difficulty BETWEEN v_diff_min AND v_diff_max
      AND p.career_club_count >= 2
      -- Year filters (only apply if set)
      AND (v_start_year_min IS NULL OR p.career_start_year >= v_start_year_min)
      AND (v_start_year_max IS NULL OR p.career_start_year <= v_start_year_max)
      -- League filter (only apply if set, player must have played in at least one of the leagues)
      AND (v_leagues IS NULL OR array_length(v_leagues, 1) IS NULL OR v_leagues = '{}' OR p.leagues_played && v_leagues)
      -- Exclude recently used players
      AND p.id NOT IN (
        SELECT dr.player_id
        FROM public.daily_rounds dr
        WHERE dr.party_id = p_party_id
          AND dr.round_date > p_date - interval '30 days'
      )
    ORDER BY random()
    LIMIT v_rounds_per_day
  LOOP
    INSERT INTO public.daily_rounds (party_id, round_date, round_number, player_id)
    VALUES (p_party_id, p_date, v_round_num, v_player.id);
    v_round_num := v_round_num + 1;
  END LOOP;

  -- Fallback: if no players found with all filters, try with just year filter
  IF v_round_num = 1 AND (v_leagues IS NOT NULL AND array_length(v_leagues, 1) > 0) THEN
    FOR v_player IN
      SELECT p.id
      FROM public.players p
      WHERE p.is_active = true
        AND p.career_club_count >= 2
        AND (v_start_year_min IS NULL OR p.career_start_year >= v_start_year_min)
        AND (v_start_year_max IS NULL OR p.career_start_year <= v_start_year_max)
      ORDER BY random()
      LIMIT v_rounds_per_day
    LOOP
      INSERT INTO public.daily_rounds (party_id, round_date, round_number, player_id)
      VALUES (p_party_id, p_date, v_round_num, v_player.id);
      v_round_num := v_round_num + 1;
    END LOOP;
  END IF;

  -- Final fallback: any player
  IF v_round_num = 1 THEN
    FOR v_player IN
      SELECT p.id
      FROM public.players p
      WHERE p.is_active = true AND p.career_club_count >= 2
      ORDER BY random()
      LIMIT v_rounds_per_day
    LOOP
      INSERT INTO public.daily_rounds (party_id, round_date, round_number, player_id)
      VALUES (p_party_id, p_date, v_round_num, v_player.id);
      v_round_num := v_round_num + 1;
    END LOOP;
  END IF;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.generate_daily_rounds(uuid, date) TO anon;
GRANT EXECUTE ON FUNCTION public.generate_daily_rounds(uuid, date) TO authenticated;
GRANT EXECUTE ON FUNCTION public.generate_daily_rounds(uuid, date) TO service_role;
