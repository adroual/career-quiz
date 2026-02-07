import { useState, useEffect, useRef } from "react";
import {
  createParty as supabaseCreateParty,
  getPartyByCode,
  joinParty as supabaseJoinParty,
  getTodayRounds,
  getMemberProgress,
  submitScore,
  getLeaderboard,
  subscribeToScores,
  subscribeToMembers,
  shareInvite as shareInviteWA,
  shareDailyReminder,
  shareScore as shareScoreWA,
  saveMemberSession,
  getMemberSession,
  getAllSessions,
  getPartyById,
  removeSession,
  // Solo mode
  getSoloDailyRounds,
  getRandomPlayers,
  hasSoloDailyCompleted,
  setSoloDailyCompleted,
  getSoloDailyScore,
  saveSoloDailyScore,
  getInfiniteStats,
  updateInfiniteStats,
} from "./lib/supabase";
import { getClubFlag } from "./lib/clubCountries";

const REVEAL_INTERVAL = 2000; // Faster reveal (was 3200)
const AVATARS = ["⚽", "🥅", "🏟️", "🧤", "👟", "🎯", "🏆", "⭐", "🦁", "🐉", "🦅", "🐺"];

// Available leagues/countries for filtering
const LEAGUES = [
  { code: "EN", name: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { code: "ES", name: "Spain", flag: "🇪🇸" },
  { code: "DE", name: "Germany", flag: "🇩🇪" },
  { code: "IT", name: "Italy", flag: "🇮🇹" },
  { code: "FR", name: "France", flag: "🇫🇷" },
  { code: "NL", name: "Netherlands", flag: "🇳🇱" },
  { code: "PT", name: "Portugal", flag: "🇵🇹" },
  { code: "BR", name: "Brazil", flag: "🇧🇷" },
  { code: "AR", name: "Argentina", flag: "🇦🇷" },
  { code: "TR", name: "Turkey", flag: "🇹🇷" },
];

// Player nationalities for filtering
const NATIONALITIES = [
  { code: "FR", name: "France", flag: "🇫🇷" },
  { code: "BR", name: "Brazil", flag: "🇧🇷" },
  { code: "AR", name: "Argentina", flag: "🇦🇷" },
  { code: "EN", name: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { code: "ES", name: "Spain", flag: "🇪🇸" },
  { code: "DE", name: "Germany", flag: "🇩🇪" },
  { code: "IT", name: "Italy", flag: "🇮🇹" },
  { code: "PT", name: "Portugal", flag: "🇵🇹" },
  { code: "NL", name: "Netherlands", flag: "🇳🇱" },
  { code: "BE", name: "Belgium", flag: "🇧🇪" },
  { code: "HR", name: "Croatia", flag: "🇭🇷" },
  { code: "PL", name: "Poland", flag: "🇵🇱" },
  { code: "SN", name: "Senegal", flag: "🇸🇳" },
  { code: "CI", name: "Ivory Coast", flag: "🇨🇮" },
  { code: "CM", name: "Cameroon", flag: "🇨🇲" },
  { code: "NG", name: "Nigeria", flag: "🇳🇬" },
  { code: "UY", name: "Uruguay", flag: "🇺🇾" },
  { code: "CO", name: "Colombia", flag: "🇨🇴" },
  { code: "SE", name: "Sweden", flag: "🇸🇪" },
  { code: "RS", name: "Serbia", flag: "🇷🇸" },
];

// Year range options
const YEAR_OPTIONS = [
  { label: "All eras", min: null, max: null },
  { label: "2010+", min: 2010, max: null },
  { label: "2000s", min: 2000, max: 2009 },
  { label: "1990s", min: 1990, max: 1999 },
  { label: "Classics (pre-1990)", min: null, max: 1989 },
];

function normalize(str) {
  return str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9\s]/g, "").trim();
}

function formatTime(ms) {
  const s = Math.floor(ms / 1000);
  const d = Math.floor((ms % 1000) / 100);
  return `${s}.${d}s`;
}

// Levenshtein distance for fuzzy matching
function levenshtein(a, b) {
  const matrix = [];
  for (let i = 0; i <= b.length; i++) matrix[i] = [i];
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      matrix[i][j] = b[i - 1] === a[j - 1]
        ? matrix[i - 1][j - 1]
        : Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
    }
  }
  return matrix[b.length][a.length];
}

// Fuzzy match: returns true if guess is close enough to any alias
function fuzzyMatch(guess, aliases) {
  const normalizedGuess = normalize(guess);
  if (!normalizedGuess || normalizedGuess.length < 3) return false;

  for (const alias of aliases) {
    const normalizedAlias = normalize(alias);

    // Exact match
    if (normalizedAlias === normalizedGuess) return true;

    // Contains match (for partial names like "Ronaldo" matching "Cristiano Ronaldo")
    if (normalizedAlias.includes(normalizedGuess) || normalizedGuess.includes(normalizedAlias)) return true;

    // Fuzzy match with Levenshtein distance
    // Allow more errors for longer names
    const maxDistance = Math.floor(Math.max(normalizedGuess.length, normalizedAlias.length) * 0.25);
    const distance = levenshtein(normalizedGuess, normalizedAlias);
    if (distance <= Math.max(2, maxDistance)) return true;

    // Check individual words (for "Messi" matching "Lionel Messi")
    const guessWords = normalizedGuess.split(/\s+/);
    const aliasWords = normalizedAlias.split(/\s+/);
    for (const gw of guessWords) {
      if (gw.length < 3) continue;
      for (const aw of aliasWords) {
        if (aw.length < 3) continue;
        if (aw === gw) return true;
        if (levenshtein(gw, aw) <= 1) return true;
      }
    }
  }
  return false;
}

export default function CareerQuizApp() {
  const [screen, setScreen] = useState("home");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [party, setParty] = useState(null);
  const [member, setMember] = useState(null);
  const [members, setMembers] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);

  const [rounds, setRounds] = useState([]);
  const [currentRound, setCurrentRound] = useState(0);
  const [revealedClubs, setRevealedClubs] = useState(1);
  const [guess, setGuess] = useState("");
  const [timer, setTimer] = useState(0);
  const [isCorrect, setIsCorrect] = useState(null);
  const [scores, setScores] = useState([]);
  const [streak, setStreak] = useState(0);
  const [savedParties, setSavedParties] = useState([]);
  const [wrongGuess, setWrongGuess] = useState(false);

  // Solo mode state
  const [soloMode, setSoloMode] = useState(null); // "daily", "infinite", or "fortune"
  const [infinitePlayer, setInfinitePlayer] = useState(null);
  const [infiniteStats, setInfiniteStats] = useState({ played: 0, correct: 0, totalPoints: 0 });
  const [playedPlayerIds, setPlayedPlayerIds] = useState([]);
  const [infiniteFilters, setInfiniteFilters] = useState({});

  // Wheel of Fortune mode state
  const [revealedLetters, setRevealedLetters] = useState([]);
  const letterRevealRef = useRef(null);

  const inputRef = useRef(null);
  const timerRef = useRef(null);
  const revealRef = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("join");
    if (code) setScreen("join");

    // Load saved parties from localStorage
    loadSavedParties();
  }, []);

  const loadSavedParties = async () => {
    const sessions = getAllSessions();
    const partyIds = Object.keys(sessions);
    if (partyIds.length === 0) return;

    const parties = [];
    for (const partyId of partyIds) {
      try {
        const partyData = await getPartyById(partyId);
        const memberId = sessions[partyId];
        const memberData = partyData.party_members.find(m => m.id === memberId);
        if (partyData && memberData) {
          parties.push({ party: partyData, member: memberData });
        } else {
          // Remove invalid session
          removeSession(partyId);
        }
      } catch {
        // Party no longer exists, remove session
        removeSession(partyId);
      }
    }
    setSavedParties(parties);
  };

  const rejoinParty = async (partyData, memberData) => {
    setLoading(true);
    setError(null);
    try {
      setParty(partyData);
      setMember(memberData);
      setMembers(partyData.party_members);
      const lb = await getLeaderboard(partyData.id);
      setLeaderboard(lb);
      setScreen("lobby");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const deletePartyFromList = (partyId, e) => {
    e.stopPropagation(); // Prevent triggering the parent button click
    if (window.confirm("Remove this party from your list?")) {
      removeSession(partyId);
      setSavedParties(prev => prev.filter(p => p.party.id !== partyId));
    }
  };

  const currentPlayer = rounds[currentRound]?.player;
  const currentDailyRoundId = rounds[currentRound]?.id;
  const totalRounds = rounds.length;

  useEffect(() => {
    if (screen !== "playing" || isCorrect !== null) return;
    timerRef.current = setInterval(() => setTimer(t => t + 100), 100);
    return () => clearInterval(timerRef.current);
  }, [screen, isCorrect, currentRound]);

  useEffect(() => {
    const player = (soloMode === "infinite" || soloMode === "fortune") ? infinitePlayer : currentPlayer;
    if (screen !== "playing" || isCorrect !== null || !player) return;
    setRevealedClubs(1);
    revealRef.current = setInterval(() => {
      setRevealedClubs(r => {
        if (r >= player.career.length) { clearInterval(revealRef.current); return r; }
        return r + 1;
      });
    }, REVEAL_INTERVAL);
    return () => clearInterval(revealRef.current);
  }, [screen, currentRound, isCorrect, currentPlayer, infinitePlayer, soloMode]);

  useEffect(() => {
    if (screen === "playing" && isCorrect === null) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [screen, isCorrect, currentRound]);

  // Fortune mode: Progressive letter reveal (capped at 70%)
  useEffect(() => {
    if (screen !== "playing" || soloMode !== "fortune" || isCorrect !== null || !infinitePlayer) return;

    const playerName = infinitePlayer.name;
    const nameLength = playerName.length;
    const letterCount = playerName.split("").filter(c => c !== " ").length;
    const maxRevealed = Math.floor(letterCount * 0.7); // Cap at 70%

    // Start with ~25% of letters visible
    const initialCount = Math.max(1, Math.floor(letterCount * 0.25));
    const indices = [];
    while (indices.length < initialCount) {
      const idx = Math.floor(Math.random() * nameLength);
      if (!indices.includes(idx) && playerName[idx] !== " ") {
        indices.push(idx);
      }
    }
    setRevealedLetters(indices);

    // Reveal a new letter every 3 seconds, stop at 70%
    letterRevealRef.current = setInterval(() => {
      setRevealedLetters(prev => {
        // Stop revealing at 70%
        if (prev.length >= maxRevealed) {
          clearInterval(letterRevealRef.current);
          return prev;
        }
        const unrevealed = [];
        for (let i = 0; i < nameLength; i++) {
          if (!prev.includes(i) && playerName[i] !== " ") {
            unrevealed.push(i);
          }
        }
        if (unrevealed.length === 0) {
          clearInterval(letterRevealRef.current);
          return prev;
        }
        const nextIdx = unrevealed[Math.floor(Math.random() * unrevealed.length)];
        return [...prev, nextIdx];
      });
    }, 3000);

    return () => clearInterval(letterRevealRef.current);
  }, [screen, soloMode, isCorrect, infinitePlayer]);

  useEffect(() => {
    if (!party?.id) return;
    const unsubScores = subscribeToScores(party.id, () => {
      getLeaderboard(party.id).then(setLeaderboard).catch(console.error);
    });
    const unsubMembers = subscribeToMembers(party.id, (newMember) => {
      setMembers(prev => [...prev, newMember]);
    });
    return () => { unsubScores(); unsubMembers(); };
  }, [party?.id]);

  const createParty = async (name, roundsPerDay, nickname, avatar, filters = {}) => {
    setLoading(true);
    setError(null);
    try {
      const { party: newParty, member: newMember } = await supabaseCreateParty(name, roundsPerDay, nickname, avatar, filters);
      setParty(newParty);
      setMember(newMember);
      setMembers([newMember]);
      saveMemberSession(newParty.id, newMember.id);
      setScreen("lobby");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const joinParty = async (code, nickname, avatar) => {
    setLoading(true);
    setError(null);
    try {
      const partyData = await getPartyByCode(code);
      const existingMemberId = getMemberSession(partyData.id);
      if (existingMemberId) {
        const existingMember = partyData.party_members.find(m => m.id === existingMemberId);
        if (existingMember) {
          setParty(partyData);
          setMember(existingMember);
          setMembers(partyData.party_members);
          setScreen("lobby");
          return;
        }
      }
      const newMember = await supabaseJoinParty(partyData.id, nickname, avatar);
      setParty(partyData);
      setMember(newMember);
      setMembers([...partyData.party_members, newMember]);
      saveMemberSession(partyData.id, newMember.id);
      setScreen("lobby");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startPlaying = async () => {
    setLoading(true);
    setError(null);
    try {
      const todayRounds = await getTodayRounds(party.id);
      const progress = await getMemberProgress(party.id, member.id);
      const completedIds = new Set(progress.map(p => p.daily_round_id));
      const unplayedRounds = todayRounds.filter(r => !completedIds.has(r.id));

      if (unplayedRounds.length === 0) {
        setError("You've completed all today's rounds! Come back tomorrow.");
        setLoading(false);
        return;
      }

      setRounds(unplayedRounds);
      setCurrentRound(0);
      setRevealedClubs(1);
      setGuess("");
      setTimer(0);
      setIsCorrect(null);
      setScores([]);
      setStreak(0);
      setScreen("playing");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Tap to reveal next club faster
  const revealNextClub = () => {
    const player = (soloMode === "infinite" || soloMode === "fortune") ? infinitePlayer : currentPlayer;
    if (isCorrect !== null || !player) return;
    setRevealedClubs(r => {
      if (r >= player.career.length) return r;
      return r + 1;
    });
  };

  const checkGuess = async () => {
    if (!guess.trim() || !currentPlayer) return;
    const allAliases = [currentPlayer.name, ...(currentPlayer.aliases || [])];
    const match = fuzzyMatch(guess, allAliases);
    if (match) {
      clearInterval(timerRef.current);
      clearInterval(revealRef.current);
      setIsCorrect(true);

      const timeBonus = Math.max(0, 300 - Math.floor(timer / 100));
      const revealBonus = Math.max(0, (currentPlayer.career.length - revealedClubs) * 100);
      const roundScore = 100 + timeBonus + revealBonus;

      try {
        await submitScore(currentDailyRoundId, member.id, roundScore, timer, revealedClubs, true);
      } catch (err) {
        console.error("Failed to submit score:", err);
      }

      setScores(s => [...s, { player: currentPlayer.name, score: roundScore, time: timer, clubs: revealedClubs }]);
      setStreak(s => s + 1);
    } else {
      // Show wrong guess feedback
      setWrongGuess(true);
      setTimeout(() => {
        setWrongGuess(false);
        setGuess("");
      }, 600);
    }
  };

  const giveUp = async () => {
    clearInterval(timerRef.current);
    clearInterval(revealRef.current);
    setIsCorrect(false);

    try {
      await submitScore(currentDailyRoundId, member.id, 0, timer, revealedClubs, false);
    } catch (err) {
      console.error("Failed to submit score:", err);
    }

    setScores(s => [...s, { player: currentPlayer.name, score: 0, time: timer, clubs: revealedClubs }]);
    setStreak(0);
  };

  const nextRound = async () => {
    if (currentRound + 1 >= totalRounds) {
      try {
        const lb = await getLeaderboard(party.id);
        setLeaderboard(lb);
      } catch (err) {
        console.error("Failed to fetch leaderboard:", err);
      }
      setScreen("result");
    } else {
      setCurrentRound(i => i + 1);
      setRevealedClubs(1);
      setGuess("");
      setTimer(0);
      setIsCorrect(null);
    }
  };

  const shareInvite = () => shareInviteWA(party?.name, party?.invite_code);
  const shareReminder = () => shareDailyReminder(party?.invite_code);
  const shareScore = () => {
    const total = scores.reduce((a, s) => a + s.score, 0);
    const correct = scores.filter(s => s.score > 0).length;
    shareScoreWA(total, correct, totalRounds, party?.invite_code);
  };

  const viewLeaderboard = async () => {
    setLoading(true);
    try {
      const lb = await getLeaderboard(party.id);
      setLeaderboard(lb);
      setScreen("leaderboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Solo Mode Functions
  // ============================================================

  const startSoloDaily = async () => {
    if (hasSoloDailyCompleted()) {
      const todayScore = getSoloDailyScore();
      if (todayScore) {
        setError(`You've already completed today's challenge! Score: ${todayScore.score} pts (${todayScore.correct}/${todayScore.total})`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    try {
      const dailyRounds = await getSoloDailyRounds();
      if (dailyRounds.length === 0) {
        setError("No daily challenge available. Try again later.");
        return;
      }
      setSoloMode("daily");
      setRounds(dailyRounds);
      setCurrentRound(0);
      setRevealedClubs(1);
      setGuess("");
      setTimer(0);
      setIsCorrect(null);
      setScores([]);
      setStreak(0);
      setScreen("playing");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const [setupGameType, setSetupGameType] = useState("infinite");

  const openInfiniteSetup = (mode = "infinite") => {
    setSetupGameType(mode);
    setScreen("infiniteSetup");
  };

  const startSoloInfinite = async (filters = {}, mode = "infinite") => {
    setLoading(true);
    setError(null);
    try {
      setInfiniteFilters(filters);
      setInfiniteStats(getInfiniteStats());
      setPlayedPlayerIds([]);
      setRevealedLetters([]);
      await loadNextInfinitePlayer([], filters);
      setSoloMode(mode); // "infinite" or "fortune"
      setScreen("playing");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadNextInfinitePlayer = async (excludeIds, filters = null) => {
    const filtersToUse = filters || infiniteFilters;
    const players = await getRandomPlayers(1, excludeIds, filtersToUse);
    if (players.length === 0) {
      setError("No more players available with these filters!");
      return false;
    }
    setInfinitePlayer(players[0]);
    setRevealedClubs(1);
    setRevealedLetters([]);
    setGuess("");
    setTimer(0);
    setIsCorrect(null);

    // For fortune mode, start letter reveal timer
    if (soloMode === "fortune" || (filters && Object.keys(filters).length === 0)) {
      clearInterval(letterRevealRef.current);
    }

    return true;
  };

  const handleSoloGuess = async () => {
    if (!guess.trim()) return;

    const player = (soloMode === "infinite" || soloMode === "fortune") ? infinitePlayer : rounds[currentRound]?.player;
    if (!player) return;

    const allAliases = [player.name, ...(player.aliases || [])];
    const match = fuzzyMatch(guess, allAliases);

    if (match) {
      clearInterval(timerRef.current);
      clearInterval(revealRef.current);
      clearInterval(letterRevealRef.current);
      setIsCorrect(true);

      const timeBonus = Math.max(0, 300 - Math.floor(timer / 100));
      const revealBonus = Math.max(0, (player.career.length - revealedClubs) * 100);

      // Fortune mode: dynamic scoring based on revealed letters
      // More letters revealed = fewer points (25% → 100%, 70% → 20%)
      let modeMultiplier = 1;
      if (soloMode === "fortune") {
        const letterCount = player.name.split("").filter(c => c !== " ").length;
        const revealedPct = revealedLetters.length / letterCount;
        // Linear scale from 1.0 (at 25%) to 0.2 (at 70%)
        modeMultiplier = Math.max(0.2, 1.0 - ((revealedPct - 0.25) / 0.45) * 0.8);
      }
      const roundScore = Math.round((100 + timeBonus + revealBonus) * modeMultiplier);

      setScores(s => [...s, { player: player.name, score: roundScore, time: timer, clubs: revealedClubs }]);
      setStreak(s => s + 1);

      if (soloMode === "infinite" || soloMode === "fortune") {
        const newStats = updateInfiniteStats(roundScore, true);
        setInfiniteStats(newStats);
      }
    } else {
      // Show wrong guess feedback
      setWrongGuess(true);
      setTimeout(() => {
        setWrongGuess(false);
        setGuess("");
      }, 600);
    }
  };

  const handleSoloGiveUp = async () => {
    clearInterval(timerRef.current);
    clearInterval(revealRef.current);
    clearInterval(letterRevealRef.current);
    setIsCorrect(false);

    const player = (soloMode === "infinite" || soloMode === "fortune") ? infinitePlayer : rounds[currentRound]?.player;
    setScores(s => [...s, { player: player?.name || "Unknown", score: 0, time: timer, clubs: revealedClubs }]);
    setStreak(0);

    if (soloMode === "infinite" || soloMode === "fortune") {
      const newStats = updateInfiniteStats(0, false);
      setInfiniteStats(newStats);
    }
  };

  // Note: Fortune mode now caps letter reveals at 70%, so no auto give-up needed
  // Players must still guess with 30% of letters hidden

  const handleSoloNext = async () => {
    if (soloMode === "daily") {
      if (currentRound + 1 >= rounds.length) {
        // Daily challenge complete
        const total = scores.reduce((a, s) => a + s.score, 0);
        const correct = scores.filter(s => s.score > 0).length;
        setSoloDailyCompleted();
        saveSoloDailyScore(total, correct, rounds.length);
        setScreen("soloResult");
      } else {
        setCurrentRound(i => i + 1);
        setRevealedClubs(1);
        setGuess("");
        setTimer(0);
        setIsCorrect(null);
      }
    } else {
      // Infinite mode - load next player
      const newExcludeIds = [...playedPlayerIds, infinitePlayer?.id].filter(Boolean);
      setPlayedPlayerIds(newExcludeIds);
      const success = await loadNextInfinitePlayer(newExcludeIds);
      if (!success) {
        setScreen("soloResult");
      }
    }
  };

  const exitSoloMode = () => {
    clearInterval(letterRevealRef.current);
    setSoloMode(null);
    setInfinitePlayer(null);
    setRounds([]);
    setScores([]);
    setRevealedLetters([]);
    setScreen("home");
  };

  const totalScore = scores.reduce((a, s) => a + s.score, 0);

  // ---- HOME ----
  if (screen === "home") {
    return (
      <Container>
        <div style={s.homeWrap}>
          <div style={s.logoSection}>
            <span style={s.logoIcon}>⚽</span>
            <h1 style={s.logoTitle}>Career Quiz</h1>
            <p style={s.logoSub}>Guess football players from their club history</p>
          </div>

          {savedParties.length > 0 && (
            <div style={s.section}>
              <div style={s.sectionHeader}>MY PARTIES</div>
              {savedParties.map(({ party, member }) => (
                <div key={party.id} style={s.partyRow}>
                  <button
                    style={{ ...s.menuCard, flex: 1, marginBottom: 0 }}
                    onClick={() => rejoinParty(party, member)}
                  >
                    <span style={s.menuIcon}>{member.avatar_emoji || "⚽"}</span>
                    <div style={s.menuText}>
                      <span style={s.menuTitle}>{party.name}</span>
                      <span style={s.menuDesc}>Playing as {member.nickname}</span>
                    </div>
                    <span style={s.menuArrow}>→</span>
                  </button>
                  <button
                    style={s.deleteBtn}
                    onClick={(e) => deletePartyFromList(party.id, e)}
                    title="Remove party"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <div style={s.section}>
            <div style={s.sectionHeader}>SOLO MODE</div>
            <button style={s.menuCard} onClick={startSoloDaily} disabled={loading}>
              <span style={s.menuIcon}>📅</span>
              <div style={s.menuText}>
                <span style={s.menuTitle}>Daily Challenge</span>
                <span style={s.menuDesc}>
                  {hasSoloDailyCompleted()
                    ? `✓ Completed today (${getSoloDailyScore()?.score || 0} pts)`
                    : "5 players, same for everyone"}
                </span>
              </div>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.menuCard} onClick={() => openInfiniteSetup("fortune")} disabled={loading}>
              <span style={s.menuIcon}>🎡</span>
              <div style={s.menuText}>
                <span style={s.menuTitle}>Wheel of Fortune</span>
                <span style={s.menuDesc}>Get letter hints for the name</span>
              </div>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.menuCard} onClick={() => openInfiniteSetup("infinite")} disabled={loading}>
              <span style={s.menuIcon}>♾️</span>
              <div style={s.menuText}>
                <span style={s.menuTitle}>Classic Practice</span>
                <span style={s.menuDesc}>No hints, pure skill</span>
              </div>
              <span style={s.menuArrow}>→</span>
            </button>
          </div>

          <div style={s.section}>
            <div style={s.sectionHeader}>PLAY WITH FRIENDS</div>
            <button style={s.menuCard} onClick={() => setScreen("create")}>
              <span style={s.menuIcon}>➕</span>
              <div style={s.menuText}>
                <span style={s.menuTitle}>Create a Party</span>
                <span style={s.menuDesc}>Start a new game with friends</span>
              </div>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.menuCard} onClick={() => setScreen("join")}>
              <span style={s.menuIcon}>🎮</span>
              <div style={s.menuText}>
                <span style={s.menuTitle}>Join a Party</span>
                <span style={s.menuDesc}>Enter an invite code</span>
              </div>
              <span style={s.menuArrow}>→</span>
            </button>
          </div>

          {error && <div style={s.errorBox}>{error}</div>}

          <p style={s.footerNote}>Share your party code to challenge friends!</p>
        </div>
      </Container>
    );
  }

  // ---- CREATE PARTY ----
  if (screen === "create") {
    return (
      <Container>
        <CreatePartyScreen onBack={() => setScreen("home")} onCreate={createParty} loading={loading} error={error} />
      </Container>
    );
  }

  // ---- JOIN PARTY ----
  if (screen === "join") {
    return (
      <Container>
        <JoinPartyScreen onBack={() => setScreen("home")} onJoin={joinParty} loading={loading} error={error} />
      </Container>
    );
  }

  // ---- INFINITE SETUP ----
  if (screen === "infiniteSetup") {
    return (
      <Container>
        <InfiniteSetupScreen
          onBack={() => setScreen("home")}
          onStart={startSoloInfinite}
          loading={loading}
          error={error}
          gameType={setupGameType}
        />
      </Container>
    );
  }

  // ---- LOBBY ----
  if (screen === "lobby") {
    return (
      <Container>
        <div style={s.screenWrap}>
          <button style={s.backLink} onClick={() => setScreen("home")}>← Back</button>

          <div style={s.lobbyHeader}>
            <h2 style={s.lobbyTitle}>{party?.name}</h2>
            <div style={s.codeBox}>
              <span style={s.codeLabel}>INVITE CODE</span>
              <span style={s.codeValue}>{party?.invite_code}</span>
            </div>
          </div>

          <div style={s.infoRow}>
            <span style={s.infoLabel}>Rounds per day</span>
            <span style={s.infoValue}>{party?.rounds_per_day}</span>
          </div>

          <div style={s.section}>
            <div style={s.sectionHeader}>PLAYERS · {members.length}</div>
            {members.map((m, i) => (
              <div key={i} style={s.playerRow}>
                <span style={s.playerAvatar}>{m.avatar_emoji}</span>
                <span style={s.playerName}>{m.nickname}</span>
                {m.is_host && <span style={s.hostTag}>HOST</span>}
              </div>
            ))}
          </div>

          {error && <div style={s.errorBox}>{error}</div>}

          <div style={s.section}>
            <div style={s.sectionHeader}>ACTIONS</div>
            <button style={s.actionCard} onClick={startPlaying} disabled={loading}>
              <span style={s.actionIcon}>▶</span>
              <span style={s.actionText}>{loading ? "Loading..." : "Play Today's Rounds"}</span>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.actionCard} onClick={shareInvite}>
              <span style={s.actionIcon}>📲</span>
              <span style={s.actionText}>Invite via WhatsApp</span>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.actionCardMuted} onClick={viewLeaderboard} disabled={loading}>
              <span style={s.actionIcon}>🏆</span>
              <span style={s.actionText}>View Leaderboard</span>
              <span style={s.menuArrow}>→</span>
            </button>
          </div>
        </div>
      </Container>
    );
  }

  // ---- PLAYING ----
  if (screen === "playing") {
    // Determine which player to show based on mode
    const activePlayer = (soloMode === "infinite" || soloMode === "fortune") ? infinitePlayer : currentPlayer;
    const activeCareer = activePlayer?.career || [];

    // Determine which handlers to use
    const onGuess = soloMode ? handleSoloGuess : checkGuess;
    const onGiveUp = soloMode ? handleSoloGiveUp : giveUp;
    const onNext = soloMode ? handleSoloNext : nextRound;

    // Round display
    const roundDisplay = (soloMode === "infinite" || soloMode === "fortune")
      ? `#${scores.length + 1}`
      : `${currentRound + 1} / ${totalRounds}`;

    const showNextButton = (soloMode === "infinite" || soloMode === "fortune")
      ? true
      : currentRound + 1 < totalRounds;

    const nextButtonText = (soloMode === "infinite" || soloMode === "fortune")
      ? "Next Player →"
      : (currentRound + 1 >= totalRounds ? "See Results →" : "Next Player →");

    return (
      <Container>
        <div style={s.gameWrap}>
          <div style={s.gameTop}>
            {soloMode && (
              <button style={s.exitBtn} onClick={exitSoloMode}>✕</button>
            )}
            <span style={s.roundTag}>
              {soloMode === "daily" && "📅 "}
              {soloMode === "infinite" && "♾️ "}
              {soloMode === "fortune" && "🎡 "}
              {roundDisplay}
            </span>
            <span style={s.timerText}>{formatTime(timer)}</span>
            {streak > 1 && <span style={s.streakTag}>🔥 {streak}</span>}
          </div>

          {(soloMode === "infinite" || soloMode === "fortune") && (
            <div style={s.infiniteStats}>
              <span>{infiniteStats.correct}/{infiniteStats.played} correct</span>
              <span>·</span>
              <span>{infiniteStats.totalPoints} pts</span>
            </div>
          )}

          <div style={s.careerBox} onClick={revealNextClub}>
            <div style={s.sectionHeader}>SENIOR CAREER</div>
            <div style={s.careerHeader}>
              <span style={s.colYears}>Years</span>
              <span style={s.colClub}>Club</span>
              <span style={s.colStats}>Apps (Gls)</span>
            </div>
            {activeCareer.map((c, i) => {
              const visible = i < revealedClubs || isCorrect !== null;
              return (
                <div key={i} style={{
                  ...s.careerRow,
                  opacity: visible ? 1 : 0.1,
                  transition: "opacity 0.4s ease",
                }}>
                  <span style={s.colYears}>{visible ? c.years : "????–????"}</span>
                  <span style={s.colClub}>
                    {visible ? <>{getClubFlag(c.club, c.country_flag)} {c.club}</> : "██████████"}
                  </span>
                  <span style={s.colStats}>{visible ? `${c.matches} (${c.goals})` : "— (—)"}</span>
                </div>
              );
            })}
            <div style={s.progressDots}>
              {activeCareer.map((_, i) => (
                <span key={i} style={{
                  ...s.dot,
                  background: i < revealedClubs || isCorrect !== null ? "#fff" : "rgba(255,255,255,0.2)",
                }} />
              ))}
            </div>
            {isCorrect === null && revealedClubs < activeCareer.length && (
              <div style={s.tapHint}>Tap to reveal next club</div>
            )}
          </div>

          {isCorrect === null ? (
            <div style={s.guessArea}>
              {/* Fortune mode: Show partially revealed name */}
              {soloMode === "fortune" && activePlayer && (
                <div style={s.fortuneHint}>
                  <div style={s.fortuneLabel}>🎡 NAME HINT</div>
                  <div style={s.fortuneLetters}>
                    {activePlayer.name.split("").map((char, i) => (
                      <span
                        key={i}
                        style={{
                          ...s.fortuneLetter,
                          ...(char === " " ? s.fortuneSpace : {}),
                        }}
                      >
                        {char === " " ? "\u00A0" : (revealedLetters.includes(i) ? char.toUpperCase() : "_")}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <div style={{
                ...s.inputRow,
                animation: wrongGuess ? "shake 0.4s ease" : "none",
              }}>
                <input
                  ref={inputRef}
                  type="text"
                  value={guess}
                  onChange={e => setGuess(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && !wrongGuess && onGuess()}
                  placeholder="Type player name..."
                  style={{
                    ...s.guessInput,
                    borderColor: wrongGuess ? "#ef4444" : "#222",
                    transition: "border-color 0.2s ease",
                  }}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  disabled={wrongGuess}
                />
                <button style={s.submitBtn} onClick={onGuess} disabled={wrongGuess}>✓</button>
              </div>
              <button style={s.skipBtn} onClick={onGiveUp}>Skip this player</button>
            </div>
          ) : (
            <div style={s.feedbackArea}>
              <div style={{
                ...s.feedbackBox,
                borderColor: isCorrect ? "#22c55e" : "#ef4444",
              }}>
                <span style={s.feedbackIcon}>{isCorrect ? "✓" : "✗"}</span>
                <div style={s.feedbackContent}>
                  <span style={{ ...s.feedbackStatus, color: isCorrect ? "#22c55e" : "#ef4444" }}>
                    {isCorrect ? "Correct!" : "Wrong"}
                  </span>
                  <span style={s.feedbackName}>{activePlayer?.name}</span>
                  {isCorrect && (
                    <span style={s.feedbackMeta}>
                      +{scores[scores.length - 1]?.score} pts · {formatTime(timer)} · {revealedClubs} club{revealedClubs > 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <button style={s.nextBtn} onClick={onNext}>
                {nextButtonText}
              </button>
              {soloMode === "infinite" && (
                <button style={s.textBtn} onClick={exitSoloMode}>
                  End Session
                </button>
              )}
            </div>
          )}
        </div>
      </Container>
    );
  }

  // ---- RESULT ----
  if (screen === "result") {
    const correct = scores.filter(s => s.score > 0).length;
    return (
      <Container>
        <div style={s.screenWrap}>
          <div style={s.resultHeader}>
            <span style={s.resultScore}>{totalScore}</span>
            <span style={s.resultLabel}>POINTS</span>
            <span style={s.resultSub}>{correct} / {totalRounds} correct</span>
          </div>

          <div style={s.section}>
            <div style={s.sectionHeader}>BREAKDOWN</div>
            {scores.map((sc, i) => (
              <div key={i} style={{
                ...s.breakdownRow,
                borderLeftColor: sc.score > 0 ? "#22c55e" : "#ef4444",
              }}>
                <div>
                  <div style={s.breakdownName}>{sc.player}</div>
                  <div style={s.breakdownMeta}>{formatTime(sc.time)} · {sc.clubs} club{sc.clubs > 1 ? "s" : ""}</div>
                </div>
                <span style={{ ...s.breakdownPts, color: sc.score > 0 ? "#22c55e" : "#ef4444" }}>
                  {sc.score > 0 ? `+${sc.score}` : "0"}
                </span>
              </div>
            ))}
          </div>

          <div style={s.section}>
            <button style={s.actionCard} onClick={shareScore}>
              <span style={s.actionIcon}>📤</span>
              <span style={s.actionText}>Share on WhatsApp</span>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.actionCardMuted} onClick={viewLeaderboard}>
              <span style={s.actionIcon}>🏆</span>
              <span style={s.actionText}>View Leaderboard</span>
              <span style={s.menuArrow}>→</span>
            </button>
            <button style={s.textBtn} onClick={() => setScreen("lobby")}>
              Back to Lobby
            </button>
          </div>
        </div>
      </Container>
    );
  }

  // ---- SOLO RESULT ----
  if (screen === "soloResult") {
    const correct = scores.filter(s => s.score > 0).length;
    const total = scores.length;

    return (
      <Container>
        <div style={s.screenWrap}>
          <div style={s.resultHeader}>
            <span style={s.soloModeLabel}>
              {soloMode === "daily" && "📅 Daily Challenge"}
              {soloMode === "infinite" && "♾️ Classic Mode"}
              {soloMode === "fortune" && "🎡 Wheel of Fortune"}
            </span>
            <span style={s.resultScore}>{totalScore}</span>
            <span style={s.resultLabel}>POINTS</span>
            <span style={s.resultSub}>{correct} / {total} correct</span>
          </div>

          <div style={s.section}>
            <div style={s.sectionHeader}>BREAKDOWN</div>
            {scores.map((sc, i) => (
              <div key={i} style={{
                ...s.breakdownRow,
                borderLeftColor: sc.score > 0 ? "#22c55e" : "#ef4444",
              }}>
                <div>
                  <div style={s.breakdownName}>{sc.player}</div>
                  <div style={s.breakdownMeta}>{formatTime(sc.time)} · {sc.clubs} club{sc.clubs > 1 ? "s" : ""}</div>
                </div>
                <span style={{ ...s.breakdownPts, color: sc.score > 0 ? "#22c55e" : "#ef4444" }}>
                  {sc.score > 0 ? `+${sc.score}` : "0"}
                </span>
              </div>
            ))}
          </div>

          {(soloMode === "infinite" || soloMode === "fortune") && (
            <div style={s.section}>
              <div style={s.sectionHeader}>SESSION STATS</div>
              <div style={s.statsRow}>
                <span>Players guessed:</span>
                <span>{infiniteStats.played}</span>
              </div>
              <div style={s.statsRow}>
                <span>Accuracy:</span>
                <span>{infiniteStats.played > 0 ? Math.round((infiniteStats.correct / infiniteStats.played) * 100) : 0}%</span>
              </div>
              <div style={s.statsRow}>
                <span>Total points:</span>
                <span>{infiniteStats.totalPoints}</span>
              </div>
            </div>
          )}

          <div style={s.section}>
            {soloMode === "daily" && (
              <button style={s.actionCard} onClick={() => {
                const text = `⚽ Career Quiz Daily Challenge\n🏆 ${totalScore} pts — ${correct}/${total} correct\n\nCan you beat me?`;
                if (navigator.share) {
                  navigator.share({ text });
                } else {
                  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
                }
              }}>
                <span style={s.actionIcon}>📤</span>
                <span style={s.actionText}>Share Score</span>
                <span style={s.menuArrow}>→</span>
              </button>
            )}
            {(soloMode === "infinite" || soloMode === "fortune") && (
              <button style={s.actionCard} onClick={() => startSoloInfinite(infiniteFilters, soloMode)}>
                <span style={s.actionIcon}>🔄</span>
                <span style={s.actionText}>Play Again</span>
                <span style={s.menuArrow}>→</span>
              </button>
            )}
            <button style={s.textBtn} onClick={exitSoloMode}>
              Back to Home
            </button>
          </div>
        </div>
      </Container>
    );
  }

  // ---- LEADERBOARD ----
  if (screen === "leaderboard") {
    const sorted = [...leaderboard].sort((a, b) => b.total_points - a.total_points);
    return (
      <Container>
        <div style={s.screenWrap}>
          <button style={s.backLink} onClick={() => setScreen("lobby")}>← Back</button>

          <h2 style={s.pageTitle}>Leaderboard</h2>
          <p style={s.pageSubtitle}>{party?.name}</p>

          {sorted.length === 0 ? (
            <p style={s.emptyState}>No scores yet. Play today's rounds!</p>
          ) : (
            <div style={s.section}>
              {sorted.map((entry, i) => (
                <div key={i} style={{
                  ...s.lbRow,
                  background: i === 0 ? "rgba(250,204,21,0.08)" : "transparent",
                }}>
                  <span style={s.lbRank}>
                    {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}`}
                  </span>
                  <span style={s.lbAvatar}>{entry.avatar_emoji}</span>
                  <div style={s.lbInfo}>
                    <span style={s.lbName}>{entry.nickname}</span>
                    <span style={s.lbSub}>{entry.correct_answers} correct</span>
                  </div>
                  <span style={s.lbPts}>{entry.total_points}</span>
                </div>
              ))}
            </div>
          )}

          <button style={s.actionCardMuted} onClick={shareReminder}>
            <span style={s.actionIcon}>🔔</span>
            <span style={s.actionText}>Send Reminder to Play</span>
            <span style={s.menuArrow}>→</span>
          </button>
        </div>
      </Container>
    );
  }

  return null;
}

function Container({ children }) {
  return <div style={s.container}><div style={s.inner}>{children}</div></div>;
}

function CreatePartyScreen({ onBack, onCreate, loading, error }) {
  const [name, setName] = useState("");
  const [rounds, setRounds] = useState(5);
  const [nickname, setNickname] = useState("");
  const [avatar, setAvatar] = useState("⚽");
  const [showFilters, setShowFilters] = useState(false);
  const [yearOption, setYearOption] = useState(0); // Index into YEAR_OPTIONS
  const [selectedLeagues, setSelectedLeagues] = useState([]);
  const [selectedNationalities, setSelectedNationalities] = useState([]);

  const toggleLeague = (code) => {
    setSelectedLeagues(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
  };

  const toggleNationality = (code) => {
    setSelectedNationalities(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
  };

  const canSubmit = name.trim() && nickname.trim() && !loading;

  const handleCreate = () => {
    if (!canSubmit) return;
    const filters = {
      startYearMin: YEAR_OPTIONS[yearOption].min,
      startYearMax: YEAR_OPTIONS[yearOption].max,
      leagues: selectedLeagues,
      nationalities: selectedNationalities,
    };
    onCreate(name, rounds, nickname, avatar, filters);
  };

  return (
    <div style={s.screenWrap}>
      <button style={s.backLink} onClick={onBack}>← Back</button>
      <h2 style={s.pageTitle}>Create a Party</h2>

      <div style={s.section}>
        <div style={s.sectionHeader}>PARTY SETTINGS</div>

        <label style={s.fieldLabel}>Party name</label>
        <input
          style={s.textInput}
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="e.g. The Legends"
        />

        <label style={s.fieldLabel}>Rounds per day</label>
        <div style={s.optionRow}>
          {[3, 5, 10].map(n => (
            <button
              key={n}
              onClick={() => setRounds(n)}
              style={{
                ...s.optionBtn,
                ...(rounds === n ? s.optionActive : {}),
              }}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <div style={s.section}>
        <button
          style={s.filterToggle}
          onClick={() => setShowFilters(!showFilters)}
        >
          <span>🎯 Player Filters</span>
          <span style={s.filterToggleArrow}>{showFilters ? "▼" : "▶"}</span>
        </button>

        {showFilters && (
          <div style={s.filterContent}>
            <label style={s.fieldLabel}>Career era</label>
            <div style={s.eraGrid}>
              {YEAR_OPTIONS.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => setYearOption(i)}
                  style={{
                    ...s.eraBtn,
                    ...(yearOption === i ? s.optionActive : {}),
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <label style={s.fieldLabel}>Leagues played in (optional)</label>
            <div style={s.leagueGrid}>
              {LEAGUES.map(league => (
                <button
                  key={league.code}
                  onClick={() => toggleLeague(league.code)}
                  style={{
                    ...s.leagueBtn,
                    ...(selectedLeagues.includes(league.code) ? s.leagueActive : {}),
                  }}
                >
                  <span>{league.flag}</span>
                  <span style={s.leagueName}>{league.name}</span>
                </button>
              ))}
            </div>
            {selectedLeagues.length > 0 && (
              <p style={s.filterHint}>
                Players who played in any of these leagues
              </p>
            )}

            <label style={s.fieldLabel}>Player nationality (optional)</label>
            <div style={s.leagueGrid}>
              {NATIONALITIES.map(nat => (
                <button
                  key={nat.code}
                  onClick={() => toggleNationality(nat.code)}
                  style={{
                    ...s.leagueBtn,
                    ...(selectedNationalities.includes(nat.code) ? s.leagueActive : {}),
                  }}
                >
                  <span>{nat.flag}</span>
                  <span style={s.leagueName}>{nat.name}</span>
                </button>
              ))}
            </div>
            {selectedNationalities.length > 0 && (
              <p style={s.filterHint}>
                Players from any of these countries
              </p>
            )}
          </div>
        )}
      </div>

      <div style={s.section}>
        <div style={s.sectionHeader}>YOUR PROFILE</div>

        <label style={s.fieldLabel}>Nickname</label>
        <input
          style={s.textInput}
          value={nickname}
          onChange={e => setNickname(e.target.value)}
          placeholder="e.g. Zizou"
        />

        <label style={s.fieldLabel}>Avatar</label>
        <div style={s.avatarGrid}>
          {AVATARS.map(a => (
            <button
              key={a}
              onClick={() => setAvatar(a)}
              style={{
                ...s.avatarBtn,
                ...(avatar === a ? s.avatarActive : {}),
              }}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {error && <div style={s.errorBox}>{error}</div>}

      <button
        style={{
          ...s.primaryBtn,
          opacity: canSubmit ? 1 : 0.4,
          cursor: canSubmit ? "pointer" : "not-allowed",
        }}
        onClick={handleCreate}
      >
        {loading ? "Creating..." : "Create Party →"}
      </button>
    </div>
  );
}

function InfiniteSetupScreen({ onBack, onStart, loading, error, gameType }) {
  const [yearOption, setYearOption] = useState(0);
  const [selectedLeagues, setSelectedLeagues] = useState([]);
  const [selectedNationalities, setSelectedNationalities] = useState([]);

  const toggleLeague = (code) => {
    setSelectedLeagues(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
  };

  const toggleNationality = (code) => {
    setSelectedNationalities(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
  };

  const handleStart = () => {
    const filters = {
      startYearMin: YEAR_OPTIONS[yearOption].min,
      startYearMax: YEAR_OPTIONS[yearOption].max,
      leagues: selectedLeagues,
      nationalities: selectedNationalities,
    };
    onStart(filters, gameType);
  };

  const title = gameType === "fortune" ? "Wheel of Fortune" : "Classic Practice";
  const icon = gameType === "fortune" ? "🎡" : "♾️";
  const subtitle = gameType === "fortune"
    ? "Get letter hints for the player name"
    : "Guess from career history only";

  return (
    <div style={s.screenWrap}>
      <button style={s.backLink} onClick={onBack}>← Back</button>
      <div style={s.setupHeader}>
        <span style={s.setupIcon}>{icon}</span>
        <h2 style={s.pageTitle}>{title}</h2>
        <p style={s.pageSubtitle}>{subtitle}</p>
      </div>

      <div style={s.section}>
        <div style={s.sectionHeader}>PLAYER FILTERS</div>

        <label style={s.fieldLabel}>Career era</label>
        <div style={s.eraGrid}>
          {YEAR_OPTIONS.map((opt, i) => (
            <button
              key={i}
              onClick={() => setYearOption(i)}
              style={{
                ...s.eraBtn,
                ...(yearOption === i ? s.optionActive : {}),
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <label style={s.fieldLabel}>Leagues (optional)</label>
        <div style={s.leagueGrid}>
          {LEAGUES.map(league => (
            <button
              key={league.code}
              onClick={() => toggleLeague(league.code)}
              style={{
                ...s.leagueBtn,
                ...(selectedLeagues.includes(league.code) ? s.leagueActive : {}),
              }}
            >
              <span>{league.flag}</span>
              <span style={s.leagueName}>{league.name}</span>
            </button>
          ))}
        </div>
        {selectedLeagues.length > 0 && (
          <p style={s.filterHint}>
            Players who played in any of these leagues
          </p>
        )}

        <label style={s.fieldLabel}>Player nationality (optional)</label>
        <div style={s.leagueGrid}>
          {NATIONALITIES.map(nat => (
            <button
              key={nat.code}
              onClick={() => toggleNationality(nat.code)}
              style={{
                ...s.leagueBtn,
                ...(selectedNationalities.includes(nat.code) ? s.leagueActive : {}),
              }}
            >
              <span>{nat.flag}</span>
              <span style={s.leagueName}>{nat.name}</span>
            </button>
          ))}
        </div>
        {selectedNationalities.length > 0 && (
          <p style={s.filterHint}>
            Players from any of these countries
          </p>
        )}
      </div>

      {error && <div style={s.errorBox}>{error}</div>}

      <button style={s.primaryBtn} onClick={handleStart} disabled={loading}>
        {loading ? "Loading..." : "Start Practice →"}
      </button>
    </div>
  );
}

function JoinPartyScreen({ onBack, onJoin, loading, error }) {
  const [code, setCode] = useState(() => {
    if (typeof window !== "undefined") return new URLSearchParams(window.location.search).get("join") || "";
    return "";
  });
  const [nickname, setNickname] = useState("");
  const [avatar, setAvatar] = useState("⚽");

  const canSubmit = code.length === 6 && nickname.trim() && !loading;

  return (
    <div style={s.screenWrap}>
      <button style={s.backLink} onClick={onBack}>← Back</button>
      <h2 style={s.pageTitle}>Join a Party</h2>

      <div style={s.section}>
        <div style={s.sectionHeader}>INVITE CODE</div>
        <input
          style={s.codeInput}
          value={code}
          onChange={e => setCode(e.target.value.toUpperCase().slice(0, 6))}
          placeholder="ABC123"
          maxLength={6}
        />
      </div>

      <div style={s.section}>
        <div style={s.sectionHeader}>YOUR PROFILE</div>

        <label style={s.fieldLabel}>Nickname</label>
        <input
          style={s.textInput}
          value={nickname}
          onChange={e => setNickname(e.target.value)}
          placeholder="e.g. Ronaldo"
        />

        <label style={s.fieldLabel}>Avatar</label>
        <div style={s.avatarGrid}>
          {AVATARS.map(a => (
            <button
              key={a}
              onClick={() => setAvatar(a)}
              style={{
                ...s.avatarBtn,
                ...(avatar === a ? s.avatarActive : {}),
              }}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {error && <div style={s.errorBox}>{error}</div>}

      <button
        style={{
          ...s.primaryBtn,
          opacity: canSubmit ? 1 : 0.4,
          cursor: canSubmit ? "pointer" : "not-allowed",
        }}
        onClick={() => canSubmit && onJoin(code, nickname, avatar)}
      >
        {loading ? "Joining..." : "Join Party →"}
      </button>
    </div>
  );
}

// =====================================================
// STYLES — Clean, minimal dark theme inspired by howmuch.tax
// =====================================================
const s = {
  // Layout
  container: {
    minHeight: "100vh",
    background: "#0a0a0a",
    color: "#fafafa",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  inner: {
    maxWidth: 460,
    margin: "0 auto",
    padding: "0 20px",
  },
  screenWrap: {
    paddingTop: 16,
    paddingBottom: 40,
  },

  // Navigation
  backLink: {
    background: "none",
    border: "none",
    color: "#666",
    fontSize: 14,
    padding: "12px 0",
    cursor: "pointer",
    fontFamily: "inherit",
  },

  // Typography
  pageTitle: {
    fontSize: 28,
    fontWeight: 600,
    margin: "8px 0 4px",
    letterSpacing: "-0.5px",
  },
  pageSubtitle: {
    fontSize: 14,
    color: "#666",
    margin: "0 0 24px",
  },

  // Sections
  section: {
    marginTop: 24,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "1.5px",
    color: "#666",
    marginBottom: 12,
  },

  // Home screen
  homeWrap: {
    paddingTop: 80,
    paddingBottom: 40,
  },
  logoSection: {
    textAlign: "center",
    marginBottom: 48,
  },
  logoIcon: {
    fontSize: 48,
    display: "block",
    marginBottom: 16,
  },
  logoTitle: {
    fontSize: 32,
    fontWeight: 600,
    margin: 0,
    letterSpacing: "-1px",
  },
  logoSub: {
    fontSize: 15,
    color: "#666",
    marginTop: 8,
  },
  footerNote: {
    fontSize: 12,
    color: "#444",
    textAlign: "center",
    marginTop: 48,
  },

  // Menu cards
  menuCard: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "16px 18px",
    marginBottom: 8,
    background: "transparent",
    border: "1px solid #222",
    borderRadius: 12,
    color: "#fafafa",
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
  },
  menuIcon: {
    fontSize: 20,
    width: 28,
    textAlign: "center",
  },
  menuText: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  menuTitle: {
    fontSize: 15,
    fontWeight: 500,
  },
  menuDesc: {
    fontSize: 13,
    color: "#666",
  },
  menuArrow: {
    fontSize: 16,
    color: "#444",
  },

  // Action cards
  actionCard: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "16px 18px",
    marginBottom: 8,
    background: "transparent",
    border: "1px solid #333",
    borderRadius: 12,
    color: "#fafafa",
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
  },
  actionCardMuted: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "16px 18px",
    marginBottom: 8,
    background: "transparent",
    border: "1px solid #1a1a1a",
    borderRadius: 12,
    color: "#888",
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
  },
  actionIcon: {
    fontSize: 18,
    width: 24,
    textAlign: "center",
  },
  actionText: {
    flex: 1,
    fontSize: 15,
    fontWeight: 500,
  },

  // Lobby
  lobbyHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginTop: 8,
    marginBottom: 24,
  },
  lobbyTitle: {
    fontSize: 24,
    fontWeight: 600,
    margin: 0,
    letterSpacing: "-0.5px",
  },
  codeBox: {
    textAlign: "right",
  },
  codeLabel: {
    display: "block",
    fontSize: 9,
    fontWeight: 600,
    letterSpacing: "1.5px",
    color: "#666",
    marginBottom: 4,
  },
  codeValue: {
    fontSize: 18,
    fontWeight: 700,
    letterSpacing: "2px",
    color: "#fff",
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "12px 0",
    borderBottom: "1px solid #1a1a1a",
  },
  infoLabel: {
    fontSize: 14,
    color: "#666",
  },
  infoValue: {
    fontSize: 14,
    fontWeight: 600,
  },
  playerRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "12px 0",
    borderBottom: "1px solid #111",
  },
  playerAvatar: {
    fontSize: 22,
  },
  playerName: {
    flex: 1,
    fontSize: 15,
    fontWeight: 500,
  },
  hostTag: {
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: "1px",
    padding: "4px 8px",
    borderRadius: 4,
    background: "#1a1a1a",
    color: "#888",
  },

  // Forms
  fieldLabel: {
    display: "block",
    fontSize: 13,
    color: "#666",
    marginBottom: 8,
    marginTop: 16,
  },
  textInput: {
    width: "100%",
    padding: "14px 16px",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 10,
    color: "#fafafa",
    fontSize: 15,
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
  },
  codeInput: {
    width: "100%",
    padding: "18px 16px",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 10,
    color: "#fafafa",
    fontSize: 24,
    fontWeight: 700,
    letterSpacing: "6px",
    textAlign: "center",
    textTransform: "uppercase",
    outline: "none",
    fontFamily: "inherit",
    boxSizing: "border-box",
  },
  optionRow: {
    display: "flex",
    gap: 10,
  },
  optionBtn: {
    flex: 1,
    padding: "14px 0",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 10,
    color: "#888",
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  optionActive: {
    background: "#1a1a1a",
    borderColor: "#fff",
    color: "#fff",
  },
  avatarGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(6, 1fr)",
    gap: 8,
  },
  avatarBtn: {
    padding: "12px 0",
    background: "#0f0f0f",
    border: "1px solid #1a1a1a",
    borderRadius: 8,
    fontSize: 22,
    cursor: "pointer",
    textAlign: "center",
  },
  avatarActive: {
    background: "#1a1a1a",
    borderColor: "#fff",
  },
  // Filter styles
  filterToggle: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 16px",
    background: "#0f0f0f",
    border: "1px solid #1a1a1a",
    borderRadius: 10,
    color: "#888",
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  filterToggleArrow: {
    fontSize: 10,
    color: "#555",
  },
  filterContent: {
    marginTop: 12,
    padding: "16px",
    background: "#0a0a0a",
    border: "1px solid #1a1a1a",
    borderRadius: 10,
  },
  eraGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: 8,
  },
  eraBtn: {
    padding: "12px 8px",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 8,
    color: "#888",
    fontSize: 13,
    fontWeight: 500,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  leagueGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: 8,
  },
  leagueBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 12px",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 8,
    color: "#888",
    fontSize: 13,
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
  },
  leagueActive: {
    background: "#1a1a1a",
    borderColor: "#fff",
    color: "#fff",
  },
  leagueName: {
    fontSize: 12,
  },
  filterHint: {
    fontSize: 11,
    color: "#555",
    marginTop: 8,
    fontStyle: "italic",
  },
  primaryBtn: {
    width: "100%",
    padding: "16px 0",
    marginTop: 24,
    background: "#fff",
    border: "none",
    borderRadius: 10,
    color: "#000",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  textBtn: {
    width: "100%",
    padding: "14px 0",
    background: "none",
    border: "none",
    color: "#666",
    fontSize: 14,
    cursor: "pointer",
    fontFamily: "inherit",
  },

  // Game screen
  gameWrap: {
    paddingTop: 16,
    paddingBottom: 32,
  },
  gameTop: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  roundTag: {
    fontSize: 13,
    fontWeight: 600,
    color: "#666",
    background: "#111",
    padding: "6px 12px",
    borderRadius: 6,
  },
  timerText: {
    fontSize: 22,
    fontWeight: 700,
    fontVariantNumeric: "tabular-nums",
  },
  streakTag: {
    fontSize: 13,
    fontWeight: 600,
    color: "#f97316",
    background: "rgba(249,115,22,0.1)",
    padding: "6px 12px",
    borderRadius: 6,
  },
  careerBox: {
    background: "#0f0f0f",
    border: "1px solid #1a1a1a",
    borderRadius: 14,
    padding: "20px 16px 16px",
    marginBottom: 20,
    cursor: "pointer",
    userSelect: "none",
  },
  tapHint: {
    textAlign: "center",
    fontSize: 12,
    color: "#555",
    marginTop: 12,
    fontStyle: "italic",
  },
  careerHeader: {
    display: "flex",
    fontSize: 11,
    color: "#444",
    fontWeight: 600,
    paddingBottom: 10,
    borderBottom: "1px solid #1a1a1a",
    marginBottom: 4,
  },
  careerRow: {
    display: "flex",
    alignItems: "center",
    padding: "11px 0",
    fontSize: 14,
    borderBottom: "1px solid #111",
  },
  colYears: {
    width: "28%",
    fontSize: 13,
    color: "#666",
  },
  colClub: {
    flex: 1,
    fontWeight: 500,
  },
  colStats: {
    width: "24%",
    textAlign: "right",
    fontSize: 13,
    color: "#555",
  },
  progressDots: {
    display: "flex",
    justifyContent: "center",
    gap: 6,
    marginTop: 16,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    transition: "background 0.3s ease",
  },
  guessArea: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 12,
  },
  inputRow: {
    display: "flex",
    gap: 8,
    width: "100%",
  },
  guessInput: {
    flex: 1,
    padding: "16px 18px",
    background: "#0f0f0f",
    border: "1px solid #222",
    borderRadius: 10,
    color: "#fafafa",
    fontSize: 16,
    outline: "none",
    fontFamily: "inherit",
  },
  submitBtn: {
    padding: "16px 22px",
    background: "#fff",
    border: "none",
    borderRadius: 10,
    color: "#000",
    fontSize: 18,
    fontWeight: 600,
    cursor: "pointer",
  },
  skipBtn: {
    background: "none",
    border: "none",
    color: "#444",
    fontSize: 13,
    cursor: "pointer",
    padding: "8px 16px",
    fontFamily: "inherit",
  },
  feedbackArea: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  feedbackBox: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    padding: "18px 20px",
    background: "#0f0f0f",
    borderWidth: 1,
    borderStyle: "solid",
    borderRadius: 12,
  },
  feedbackIcon: {
    fontSize: 28,
    fontWeight: 700,
  },
  feedbackContent: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  feedbackStatus: {
    fontSize: 14,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  feedbackName: {
    fontSize: 18,
    fontWeight: 600,
  },
  feedbackMeta: {
    fontSize: 13,
    color: "#666",
    marginTop: 2,
  },
  nextBtn: {
    width: "100%",
    padding: "16px 0",
    background: "#111",
    border: "1px solid #222",
    borderRadius: 10,
    color: "#fafafa",
    fontSize: 15,
    fontWeight: 500,
    cursor: "pointer",
    fontFamily: "inherit",
  },

  // Results
  resultHeader: {
    textAlign: "center",
    paddingTop: 40,
    paddingBottom: 32,
  },
  resultScore: {
    display: "block",
    fontSize: 64,
    fontWeight: 700,
    letterSpacing: "-2px",
    lineHeight: 1,
  },
  resultLabel: {
    display: "block",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "2px",
    color: "#666",
    marginTop: 8,
  },
  resultSub: {
    display: "block",
    fontSize: 15,
    color: "#888",
    marginTop: 8,
  },
  breakdownRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 16px",
    marginBottom: 6,
    background: "#0f0f0f",
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftStyle: "solid",
  },
  breakdownName: {
    fontSize: 15,
    fontWeight: 500,
  },
  breakdownMeta: {
    fontSize: 12,
    color: "#555",
    marginTop: 2,
  },
  breakdownPts: {
    fontSize: 18,
    fontWeight: 700,
  },

  // Leaderboard
  lbRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "14px 16px",
    marginBottom: 6,
    borderRadius: 10,
    border: "1px solid #1a1a1a",
  },
  lbRank: {
    width: 28,
    fontSize: 18,
    fontWeight: 700,
    textAlign: "center",
  },
  lbAvatar: {
    fontSize: 24,
  },
  lbInfo: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  lbName: {
    fontSize: 15,
    fontWeight: 500,
  },
  lbSub: {
    fontSize: 12,
    color: "#555",
  },
  lbPts: {
    fontSize: 20,
    fontWeight: 700,
  },

  // Misc
  errorBox: {
    padding: "12px 16px",
    background: "rgba(239,68,68,0.1)",
    border: "1px solid rgba(239,68,68,0.3)",
    borderRadius: 8,
    color: "#ef4444",
    fontSize: 14,
    marginTop: 16,
  },
  emptyState: {
    fontSize: 14,
    color: "#555",
    textAlign: "center",
    padding: "40px 0",
  },

  // Solo mode
  exitBtn: {
    background: "none",
    border: "none",
    color: "#666",
    fontSize: 14,
    padding: "12px 0",
    cursor: "pointer",
    fontFamily: "inherit",
  },
  soloModeLabel: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "1.5px",
    color: "#666",
    textTransform: "uppercase",
    marginBottom: 8,
  },
  infiniteStats: {
    display: "flex",
    justifyContent: "center",
    gap: 24,
    padding: "16px 0",
    marginBottom: 16,
    borderBottom: "1px solid #1a1a1a",
  },
  statsRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 16px",
    marginBottom: 4,
    background: "#0f0f0f",
    borderRadius: 8,
    fontSize: 14,
  },

  // Party management
  partyRow: {
    display: "flex",
    alignItems: "stretch",
    gap: 8,
    marginBottom: 8,
  },
  deleteBtn: {
    background: "transparent",
    border: "1px solid #333",
    borderRadius: 12,
    color: "#666",
    fontSize: 14,
    padding: "0 14px",
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "all 0.2s ease",
  },

  // Infinite setup - Game type cards
  gameTypeCard: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "16px 18px",
    marginBottom: 8,
    background: "transparent",
    border: "1px solid #222",
    borderRadius: 12,
    color: "#fafafa",
    cursor: "pointer",
    fontFamily: "inherit",
    textAlign: "left",
  },
  gameTypeActive: {
    borderColor: "#22c55e",
    background: "rgba(34, 197, 94, 0.05)",
  },
  gameTypeIcon: {
    fontSize: 24,
    width: 36,
    textAlign: "center",
  },
  checkMark: {
    color: "#22c55e",
    fontSize: 18,
    fontWeight: 700,
  },

  // Fortune mode - Letter hints
  fortuneHint: {
    background: "#0f0f0f",
    border: "1px solid #f97316",
    borderRadius: 12,
    padding: "16px 20px",
    marginBottom: 16,
    textAlign: "center",
  },
  fortuneLabel: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "1.5px",
    color: "#f97316",
    marginBottom: 12,
  },
  fortuneLetters: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 4,
  },
  fortuneLetter: {
    fontSize: 22,
    fontWeight: 700,
    fontFamily: "monospace",
    color: "#fafafa",
    minWidth: 18,
    textAlign: "center",
  },
  fortuneSpace: {
    minWidth: 12,
  },

  // Setup screen header
  setupHeader: {
    textAlign: "center",
    marginBottom: 24,
  },
  setupIcon: {
    fontSize: 48,
    display: "block",
    marginBottom: 12,
  },
};
