-- Add nationality columns to players table
-- Run this in Supabase SQL Editor

-- Add nationality columns
ALTER TABLE players ADD COLUMN IF NOT EXISTS nationality TEXT;
ALTER TABLE players ADD COLUMN IF NOT EXISTS nationality_code TEXT;
ALTER TABLE players ADD COLUMN IF NOT EXISTS nationality_flag TEXT;

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_players_nationality_code ON players(nationality_code);

-- Example of how data will look:
-- nationality: "France"
-- nationality_code: "FR"
-- nationality_flag: "🇫🇷"
