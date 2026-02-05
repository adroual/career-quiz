-- ============================================================
-- Solo Mode: Daily Challenge & Infinite Practice
-- ============================================================

-- 1. Create solo_daily_rounds table (shared daily challenge for all players)
CREATE TABLE IF NOT EXISTS public.solo_daily_rounds (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  round_date date NOT NULL,
  round_number smallint NOT NULL,
  player_id uuid NOT NULL REFERENCES public.players(id),

  UNIQUE(round_date, round_number)
);

CREATE INDEX IF NOT EXISTS idx_solo_rounds_date ON public.solo_daily_rounds(round_date);

-- 2. Enable RLS
ALTER TABLE public.solo_daily_rounds ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Solo rounds are viewable by everyone" ON public.solo_daily_rounds FOR SELECT USING (true);

-- 3. Function to generate solo daily rounds (5 players per day, deterministic)
CREATE OR REPLACE FUNCTION public.generate_solo_daily_rounds(
  p_date date DEFAULT current_date
)
RETURNS void AS $$
DECLARE
  v_player record;
  v_round_num int := 1;
  v_seed double precision;
BEGIN
  -- Exit if rounds already exist for this date
  IF EXISTS (SELECT 1 FROM public.solo_daily_rounds WHERE round_date = p_date LIMIT 1) THEN
    RETURN;
  END IF;

  -- Use date as seed for deterministic random selection
  -- This ensures same players for everyone on the same day
  v_seed := extract(epoch from p_date::timestamp)::double precision / 86400;
  PERFORM setseed(v_seed - floor(v_seed));

  -- Select 5 random players (mix of difficulties for variety)
  FOR v_player IN
    SELECT p.id
    FROM public.players p
    WHERE p.is_active = true
      AND p.career_club_count >= 2
      AND p.id NOT IN (
        SELECT sdr.player_id
        FROM public.solo_daily_rounds sdr
        WHERE sdr.round_date > p_date - interval '14 days'
      )
    ORDER BY random()
    LIMIT 5
  LOOP
    INSERT INTO public.solo_daily_rounds (round_date, round_number, player_id)
    VALUES (p_date, v_round_num, v_player.id);
    v_round_num := v_round_num + 1;
  END LOOP;

  -- Fallback if not enough players (use any player)
  IF v_round_num <= 5 THEN
    FOR v_player IN
      SELECT p.id
      FROM public.players p
      WHERE p.is_active = true AND p.career_club_count >= 2
      ORDER BY random()
      LIMIT (6 - v_round_num)
    LOOP
      INSERT INTO public.solo_daily_rounds (round_date, round_number, player_id)
      VALUES (p_date, v_round_num, v_player.id);
      v_round_num := v_round_num + 1;
    END LOOP;
  END IF;

  -- Reset random seed
  PERFORM setseed(random());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Function to get random players for infinite mode
CREATE OR REPLACE FUNCTION public.get_random_players(
  p_count int DEFAULT 1,
  p_exclude_ids uuid[] DEFAULT '{}'
)
RETURNS TABLE (
  id uuid,
  name text,
  aliases text[],
  difficulty smallint
) AS $$
BEGIN
  RETURN QUERY
  SELECT p.id, p.name, p.aliases, p.difficulty
  FROM public.players p
  WHERE p.is_active = true
    AND p.career_club_count >= 2
    AND (p_exclude_ids IS NULL OR NOT (p.id = ANY(p_exclude_ids)))
  ORDER BY random()
  LIMIT p_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Grant permissions
GRANT EXECUTE ON FUNCTION public.generate_solo_daily_rounds(date) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_random_players(int, uuid[]) TO anon, authenticated, service_role;

-- 6. Generate today's solo rounds
SELECT generate_solo_daily_rounds();

-- 7. Verify
SELECT sdr.*, p.name as player_name
FROM solo_daily_rounds sdr
JOIN players p ON p.id = sdr.player_id
WHERE round_date = current_date
ORDER BY round_number;
