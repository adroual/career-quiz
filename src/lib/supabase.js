/**
 * Career Quiz — Supabase Client Integration
 * 
 * Replace the mock functions in the main app with these real Supabase calls.
 * 
 * Setup:
 *   npm install @supabase/supabase-js
 * 
 * Environment:
 *   VITE_SUPABASE_URL=https://xxx.supabase.co
 *   VITE_SUPABASE_ANON_KEY=eyJ...
 */

import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

// ============================================================
// Party Management
// ============================================================

/** Create a new party and its host member */
export async function createParty(name, roundsPerDay, nickname, avatarEmoji, filters = {}) {
  // Generate invite code
  const { data: codeData } = await supabase.rpc("generate_invite_code");
  const inviteCode = codeData || generateLocalCode();

  // Build party data with optional filters
  const partyData = {
    name,
    invite_code: inviteCode,
    rounds_per_day: roundsPerDay,
  };

  // Add filters if provided
  if (filters.startYearMin) partyData.filter_start_year_min = filters.startYearMin;
  if (filters.startYearMax) partyData.filter_start_year_max = filters.startYearMax;
  if (filters.leagues && filters.leagues.length > 0) partyData.filter_leagues = filters.leagues;

  // Insert party
  const { data: party, error: partyErr } = await supabase
    .from("parties")
    .insert(partyData)
    .select()
    .single();

  if (partyErr) throw partyErr;

  // Insert host member
  const { data: member, error: memberErr } = await supabase
    .from("party_members")
    .insert({
      party_id: party.id,
      nickname,
      avatar_emoji: avatarEmoji,
      is_host: true,
    })
    .select()
    .single();

  if (memberErr) throw memberErr;

  // Update party.created_by
  await supabase
    .from("parties")
    .update({ created_by: member.id })
    .eq("id", party.id);

  // Generate today's rounds
  await supabase.rpc("generate_daily_rounds", { p_party_id: party.id });

  return { party, member };
}

/** Look up a party by invite code */
export async function getPartyByCode(code) {
  const { data, error } = await supabase
    .from("parties")
    .select("*, party_members!party_id(*)")
    .eq("invite_code", code.toUpperCase())
    .eq("is_active", true)
    .single();

  if (error) throw error;
  return data;
}

/** Join an existing party */
export async function joinParty(partyId, nickname, avatarEmoji) {
  const { data: member, error } = await supabase
    .from("party_members")
    .insert({
      party_id: partyId,
      nickname,
      avatar_emoji: avatarEmoji,
      is_host: false,
    })
    .select()
    .single();

  if (error) throw error;
  return member;
}

/** Get all members of a party */
export async function getPartyMembers(partyId) {
  const { data, error } = await supabase
    .from("party_members")
    .select("*")
    .eq("party_id", partyId)
    .order("joined_at");

  if (error) throw error;
  return data;
}

// ============================================================
// Daily Rounds
// ============================================================

/** Get today's rounds for a party (generates them if needed) */
export async function getTodayRounds(partyId) {
  const today = new Date().toISOString().split("T")[0];

  // Try to generate rounds (ignore errors - 409 means rounds already exist)
  const { error: rpcError } = await supabase.rpc("generate_daily_rounds", {
    p_party_id: partyId,
    p_date: today,
  });

  // Log but don't throw - 409 conflict just means rounds exist already
  if (rpcError) {
    console.log("generate_daily_rounds:", rpcError.message || "rounds may already exist");
  }

  // Fetch rounds with player data and career entries
  const { data: rounds, error } = await supabase
    .from("daily_rounds")
    .select(`
      id,
      round_number,
      round_date,
      player:players (
        id,
        name,
        aliases,
        difficulty,
        career_entries (
          sort_order,
          chronological_order,
          years,
          club,
          country_code,
          country_flag,
          matches,
          goals
        )
      )
    `)
    .eq("party_id", partyId)
    .eq("round_date", today)
    .order("round_number");

  if (error) throw error;

  // Sort career entries by chronological_order (actual career timeline)
  return rounds.map((r) => ({
    ...r,
    player: {
      ...r.player,
      career: r.player.career_entries.sort((a, b) => a.chronological_order - b.chronological_order),
    },
  }));
}

/** Check which rounds a member has already completed today */
export async function getMemberProgress(partyId, memberId) {
  const today = new Date().toISOString().split("T")[0];

  const { data, error } = await supabase
    .from("scores")
    .select(`
      daily_round_id,
      points,
      time_ms,
      clubs_revealed,
      is_correct,
      daily_rounds!inner (
        party_id,
        round_date,
        round_number
      )
    `)
    .eq("member_id", memberId)
    .eq("daily_rounds.party_id", partyId)
    .eq("daily_rounds.round_date", today);

  if (error) throw error;
  return data;
}

/** Submit a score for a round */
export async function submitScore(dailyRoundId, memberId, points, timeMs, clubsRevealed, isCorrect) {
  const { data, error } = await supabase
    .from("scores")
    .insert({
      daily_round_id: dailyRoundId,
      member_id: memberId,
      points,
      time_ms: timeMs,
      clubs_revealed: clubsRevealed,
      is_correct: isCorrect,
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

// ============================================================
// Leaderboard
// ============================================================

/** Get all-time leaderboard for a party */
export async function getLeaderboard(partyId) {
  const { data, error } = await supabase
    .from("v_leaderboard")
    .select("*")
    .eq("party_id", partyId)
    .order("total_points", { ascending: false });

  if (error) throw error;
  return data;
}

/** Get daily leaderboard */
export async function getDailyLeaderboard(partyId, date) {
  const targetDate = date || new Date().toISOString().split("T")[0];

  const { data, error } = await supabase
    .from("v_daily_leaderboard")
    .select("*")
    .eq("party_id", partyId)
    .eq("round_date", targetDate)
    .order("day_points", { ascending: false });

  if (error) throw error;
  return data;
}

// ============================================================
// Real-time subscriptions
// ============================================================

/** Subscribe to new scores in a party (for live leaderboard updates) */
export function subscribeToScores(partyId, callback) {
  const channel = supabase
    .channel(`party-scores-${partyId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "scores",
      },
      (payload) => {
        callback(payload.new);
      }
    )
    .subscribe();

  return () => supabase.removeChannel(channel);
}

/** Subscribe to new members joining */
export function subscribeToMembers(partyId, callback) {
  const channel = supabase
    .channel(`party-members-${partyId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "party_members",
        filter: `party_id=eq.${partyId}`,
      },
      (payload) => {
        callback(payload.new);
      }
    )
    .subscribe();

  return () => supabase.removeChannel(channel);
}

// ============================================================
// WhatsApp Sharing Helpers
// ============================================================

export function getInviteUrl(inviteCode) {
  const baseUrl = window.location.origin;
  return `${baseUrl}?join=${inviteCode}`;
}

export function shareViaWhatsApp(text) {
  const encoded = encodeURIComponent(text);
  
  // Try Web Share API first (works on mobile)
  if (navigator.share) {
    navigator.share({ text }).catch(() => {
      // Fallback to wa.me
      window.open(`https://wa.me/?text=${encoded}`, "_blank");
    });
  } else {
    window.open(`https://wa.me/?text=${encoded}`, "_blank");
  }
}

export function shareInvite(partyName, inviteCode) {
  const url = getInviteUrl(inviteCode);
  const text = `⚽ Join my Career Quiz party "${partyName}"!\n\nGuess football players from their club careers.\nNew rounds every day!\n\n${url}`;
  shareViaWhatsApp(text);
}

export function shareDailyReminder(inviteCode) {
  const url = getInviteUrl(inviteCode);
  const text = `🎯 Today's Career Quiz rounds are ready!\n\nPlay now: ${url}`;
  shareViaWhatsApp(text);
}

export function shareScore(totalPoints, correct, total, inviteCode) {
  const url = getInviteUrl(inviteCode);
  const text = `⚽ Career Quiz\n🏆 ${totalPoints} pts — ${correct}/${total} correct\n\nCan you beat me?\n${url}`;
  shareViaWhatsApp(text);
}

// ============================================================
// Utility
// ============================================================

function generateLocalCode() {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 6; i++) code += chars[Math.floor(Math.random() * chars.length)];
  return code;
}

/** Store member session locally */
export function saveMemberSession(partyId, memberId) {
  try {
    const sessions = JSON.parse(localStorage.getItem("cq_sessions") || "{}");
    sessions[partyId] = memberId;
    localStorage.setItem("cq_sessions", JSON.stringify(sessions));
  } catch {}
}

export function getMemberSession(partyId) {
  try {
    const sessions = JSON.parse(localStorage.getItem("cq_sessions") || "{}");
    return sessions[partyId] || null;
  } catch {
    return null;
  }
}

/** Get all saved sessions from localStorage */
export function getAllSessions() {
  try {
    return JSON.parse(localStorage.getItem("cq_sessions") || "{}");
  } catch {
    return {};
  }
}

/** Get party by ID */
export async function getPartyById(partyId) {
  const { data, error } = await supabase
    .from("parties")
    .select("*, party_members!party_id(*)")
    .eq("id", partyId)
    .eq("is_active", true)
    .single();

  if (error) throw error;
  return data;
}

/** Remove a session from localStorage */
export function removeSession(partyId) {
  try {
    const sessions = JSON.parse(localStorage.getItem("cq_sessions") || "{}");
    delete sessions[partyId];
    localStorage.setItem("cq_sessions", JSON.stringify(sessions));
  } catch {}
}

// ============================================================
// Solo Mode
// ============================================================

/** Get today's solo daily challenge rounds */
export async function getSoloDailyRounds() {
  const today = new Date().toISOString().split("T")[0];

  // Generate if needed (ignore errors)
  await supabase.rpc("generate_solo_daily_rounds", { p_date: today });

  // Fetch rounds with player data
  const { data: rounds, error } = await supabase
    .from("solo_daily_rounds")
    .select(`
      id,
      round_number,
      round_date,
      player:players (
        id,
        name,
        aliases,
        difficulty,
        career_entries (
          sort_order,
          chronological_order,
          years,
          club,
          country_code,
          country_flag,
          matches,
          goals
        )
      )
    `)
    .eq("round_date", today)
    .order("round_number");

  if (error) throw error;

  return rounds.map((r) => ({
    ...r,
    player: {
      ...r.player,
      career: r.player.career_entries.sort((a, b) => a.chronological_order - b.chronological_order),
    },
  }));
}

/** Get random players for infinite mode */
export async function getRandomPlayers(count = 1, excludeIds = [], filters = {}) {
  // Build query with filters
  let query = supabase
    .from("players")
    .select("*")
    .gte("career_club_count", 3)
    .gte("career_start_year", 1980); // Always enforce 1980 minimum

  // Apply additional filters
  if (filters.startYearMin && filters.startYearMin > 1980) {
    query = query.gte("career_start_year", filters.startYearMin);
  }
  if (filters.startYearMax) {
    query = query.lte("career_start_year", filters.startYearMax);
  }
  if (filters.leagues && filters.leagues.length > 0) {
    query = query.overlaps("leagues_played", filters.leagues);
  }
  if (filters.nationalities && filters.nationalities.length > 0) {
    query = query.in("nationality_code", filters.nationalities);
  }
  // Get random players using limit and order
  const { data, error } = await query
    .order("id", { ascending: false })
    .limit(200); // Get a larger pool for better randomness

  if (error) throw error;
  if (!data || data.length === 0) return [];

  // Filter out already played players (more reliable than SQL filter)
  const excludeSet = new Set(excludeIds);
  const available = data.filter(p => !excludeSet.has(p.id));

  if (available.length === 0) return [];

  // Shuffle and take requested count
  const shuffled = available.sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, count);

  // Fetch career entries for each player
  const playerIds = selected.map((p) => p.id);
  const { data: careers, error: careerErr } = await supabase
    .from("career_entries")
    .select("*")
    .in("player_id", playerIds)
    .order("chronological_order");

  if (careerErr) throw careerErr;

  // Map careers to players
  return selected.map((p) => ({
    ...p,
    career: careers
      .filter((c) => c.player_id === p.id)
      .sort((a, b) => a.chronological_order - b.chronological_order),
  }));
}

/** Check if user has completed today's solo challenge */
export function hasSoloDailyCompleted() {
  try {
    const today = new Date().toISOString().split("T")[0];
    const completed = localStorage.getItem("cq_solo_daily_completed");
    return completed === today;
  } catch {
    return false;
  }
}

/** Mark today's solo challenge as completed */
export function setSoloDailyCompleted() {
  try {
    const today = new Date().toISOString().split("T")[0];
    localStorage.setItem("cq_solo_daily_completed", today);
  } catch {}
}

/** Get solo daily best score */
export function getSoloDailyScore() {
  try {
    const today = new Date().toISOString().split("T")[0];
    const data = JSON.parse(localStorage.getItem("cq_solo_daily_score") || "{}");
    return data[today] || null;
  } catch {
    return null;
  }
}

/** Save solo daily score */
export function saveSoloDailyScore(score, correct, total) {
  try {
    const today = new Date().toISOString().split("T")[0];
    const data = JSON.parse(localStorage.getItem("cq_solo_daily_score") || "{}");
    data[today] = { score, correct, total };
    localStorage.setItem("cq_solo_daily_score", JSON.stringify(data));
  } catch {}
}

/** Get infinite mode stats */
export function getInfiniteStats() {
  try {
    return JSON.parse(localStorage.getItem("cq_infinite_stats") || '{"played":0,"correct":0,"totalPoints":0}');
  } catch {
    return { played: 0, correct: 0, totalPoints: 0 };
  }
}

/** Update infinite mode stats */
export function updateInfiniteStats(points, isCorrect) {
  try {
    const stats = getInfiniteStats();
    stats.played += 1;
    if (isCorrect) stats.correct += 1;
    stats.totalPoints += points;
    localStorage.setItem("cq_infinite_stats", JSON.stringify(stats));
    return stats;
  } catch {
    return { played: 0, correct: 0, totalPoints: 0 };
  }
}
