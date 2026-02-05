-- ============================================================
-- Career Quiz — Supabase Schema Migration
-- ============================================================

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ============================================================
-- PLAYERS (populated by data pipeline)
-- ============================================================

create table public.players (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  aliases text[] not null default '{}',
  wikipedia_title text,
  wikidata_id text,
  difficulty smallint not null default 3 check (difficulty between 1 and 5),
  career_club_count smallint not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create index idx_players_difficulty on public.players(difficulty);
create index idx_players_active on public.players(is_active) where is_active = true;

-- ============================================================
-- CAREER ENTRIES (one row per club stint)
-- ============================================================

create table public.career_entries (
  id uuid primary key default gen_random_uuid(),
  player_id uuid not null references public.players(id) on delete cascade,
  sort_order smallint not null,           -- reveal order (1 = shown first)
  chronological_order smallint not null,  -- actual career order
  years text not null,                    -- "2001–2006"
  club text not null,
  country_code text,                      -- "FR", "ES", etc.
  country_flag text,                      -- "🇫🇷"
  matches smallint default 0,
  goals smallint default 0,
  
  unique(player_id, sort_order)
);

create index idx_career_player on public.career_entries(player_id);

-- ============================================================
-- PARTIES (game groups)
-- ============================================================

create table public.parties (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  invite_code text not null unique,
  rounds_per_day smallint not null default 5 check (rounds_per_day between 1 and 20),
  difficulty_min smallint not null default 1,
  difficulty_max smallint not null default 5,
  created_by uuid,  -- FK set after party_members exists
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create unique index idx_party_invite on public.parties(invite_code);

-- ============================================================
-- PARTY MEMBERS
-- ============================================================

create table public.party_members (
  id uuid primary key default gen_random_uuid(),
  party_id uuid not null references public.parties(id) on delete cascade,
  nickname text not null,
  avatar_emoji text not null default '⚽',
  is_host boolean not null default false,
  joined_at timestamptz not null default now(),
  
  unique(party_id, nickname)
);

create index idx_members_party on public.party_members(party_id);

-- Now add the FK for parties.created_by
alter table public.parties 
  add constraint fk_parties_created_by 
  foreign key (created_by) references public.party_members(id);

-- ============================================================
-- DAILY ROUNDS (generated each day per party)
-- ============================================================

create table public.daily_rounds (
  id uuid primary key default gen_random_uuid(),
  party_id uuid not null references public.parties(id) on delete cascade,
  round_date date not null,
  round_number smallint not null,
  player_id uuid not null references public.players(id),
  
  unique(party_id, round_date, round_number)
);

create index idx_rounds_party_date on public.daily_rounds(party_id, round_date);

-- ============================================================
-- SCORES
-- ============================================================

create table public.scores (
  id uuid primary key default gen_random_uuid(),
  daily_round_id uuid not null references public.daily_rounds(id) on delete cascade,
  member_id uuid not null references public.party_members(id) on delete cascade,
  points smallint not null default 0,
  time_ms integer not null,
  clubs_revealed smallint not null,
  is_correct boolean not null default false,
  answered_at timestamptz not null default now(),
  
  unique(daily_round_id, member_id)  -- one attempt per round per player
);

create index idx_scores_member on public.scores(member_id);
create index idx_scores_round on public.scores(daily_round_id);

-- ============================================================
-- VIEWS
-- ============================================================

-- Leaderboard view: total score per member per party
create or replace view public.v_leaderboard as
select
  pm.party_id,
  pm.id as member_id,
  pm.nickname,
  pm.avatar_emoji,
  coalesce(sum(s.points), 0) as total_points,
  count(s.id) filter (where s.is_correct) as correct_answers,
  count(s.id) as total_answers,
  coalesce(avg(s.time_ms) filter (where s.is_correct), 0) as avg_time_ms,
  max(s.answered_at) as last_played
from public.party_members pm
left join public.scores s on s.member_id = pm.id
group by pm.party_id, pm.id, pm.nickname, pm.avatar_emoji;

-- Daily leaderboard
create or replace view public.v_daily_leaderboard as
select
  dr.party_id,
  dr.round_date,
  pm.id as member_id,
  pm.nickname,
  pm.avatar_emoji,
  coalesce(sum(s.points), 0) as day_points,
  count(s.id) filter (where s.is_correct) as day_correct,
  count(s.id) as day_answers
from public.daily_rounds dr
cross join public.party_members pm
left join public.scores s on s.daily_round_id = dr.id and s.member_id = pm.id
where pm.party_id = dr.party_id
group by dr.party_id, dr.round_date, pm.id, pm.nickname, pm.avatar_emoji;

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Generate a random 6-char invite code
create or replace function public.generate_invite_code()
returns text as $$
declare
  chars text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';  -- no ambiguous chars
  code text := '';
  i int;
begin
  for i in 1..6 loop
    code := code || substr(chars, floor(random() * length(chars) + 1)::int, 1);
  end loop;
  return code;
end;
$$ language plpgsql;

-- Generate daily rounds for a party
create or replace function public.generate_daily_rounds(
  p_party_id uuid,
  p_date date default current_date
)
returns void as $$
declare
  v_rounds_per_day smallint;
  v_diff_min smallint;
  v_diff_max smallint;
  v_player_ids uuid[];
begin
  -- Get party config
  select rounds_per_day, difficulty_min, difficulty_max
  into v_rounds_per_day, v_diff_min, v_diff_max
  from public.parties
  where id = p_party_id and is_active = true;
  
  if not found then return; end if;
  
  -- Check if rounds already exist for this date
  if exists (
    select 1 from public.daily_rounds 
    where party_id = p_party_id and round_date = p_date
  ) then return; end if;
  
  -- Select random players not used in last 30 days
  select array_agg(id) into v_player_ids
  from (
    select p.id
    from public.players p
    where p.is_active = true
      and p.difficulty between v_diff_min and v_diff_max
      and p.career_club_count >= 2
      and p.id not in (
        select dr.player_id 
        from public.daily_rounds dr
        where dr.party_id = p_party_id
          and dr.round_date > p_date - interval '30 days'
      )
    order by random()
    limit v_rounds_per_day
  ) sub;
  
  -- Insert rounds
  insert into public.daily_rounds (party_id, round_date, round_number, player_id)
  select p_party_id, p_date, row_number() over (), unnest(v_player_ids);
end;
$$ language plpgsql;

-- Generate rounds for ALL active parties (called by cron)
create or replace function public.generate_all_daily_rounds()
returns void as $$
declare
  v_party_id uuid;
begin
  for v_party_id in select id from public.parties where is_active = true loop
    perform public.generate_daily_rounds(v_party_id);
  end loop;
end;
$$ language plpgsql;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Players and career entries: readable by everyone
alter table public.players enable row level security;
create policy "Players are viewable by everyone" on public.players for select using (true);

alter table public.career_entries enable row level security;
create policy "Career entries are viewable by everyone" on public.career_entries for select using (true);

-- Parties: viewable by everyone (to join via invite code)
alter table public.parties enable row level security;
create policy "Parties are viewable by everyone" on public.parties for select using (true);
create policy "Anyone can create a party" on public.parties for insert with check (true);

-- Party members: viewable by party members
alter table public.party_members enable row level security;
create policy "Members are viewable by everyone" on public.party_members for select using (true);
create policy "Anyone can join a party" on public.party_members for insert with check (true);

-- Daily rounds: viewable by party members
alter table public.daily_rounds enable row level security;
create policy "Rounds are viewable by everyone" on public.daily_rounds for select using (true);

-- Scores: viewable by party members, insertable by the player
alter table public.scores enable row level security;
create policy "Scores are viewable by everyone" on public.scores for select using (true);
create policy "Anyone can insert scores" on public.scores for insert with check (true);

-- ============================================================
-- CRON: Schedule daily round generation (requires pg_cron)
-- Run in Supabase Dashboard > SQL Editor after enabling pg_cron
-- ============================================================

-- select cron.schedule(
--   'generate-daily-rounds',
--   '0 0 * * *',  -- midnight UTC
--   $$select public.generate_all_daily_rounds()$$
-- );
