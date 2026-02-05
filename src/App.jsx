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
} from "./lib/supabase";

/*
  Career Quiz — Full App with Supabase Integration
  Screens: Home → Create/Join Party → Lobby → Daily Play → Leaderboard
*/

const REVEAL_INTERVAL = 3200;
const AVATARS = ["⚽", "🥅", "🏟️", "🧤", "👟", "🎯", "🏆", "⭐", "🦁", "🐉", "🦅", "🐺"];

function normalize(str) {
  return str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9\s]/g, "").trim();
}

function formatTime(ms) {
  const s = Math.floor(ms / 1000);
  const d = Math.floor((ms % 1000) / 100);
  return `${s}.${d}s`;
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

  const inputRef = useRef(null);
  const timerRef = useRef(null);
  const revealRef = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("join");
    if (code) setScreen("join");
  }, []);

  const currentPlayer = rounds[currentRound]?.player;
  const currentDailyRoundId = rounds[currentRound]?.id;
  const totalRounds = rounds.length;

  useEffect(() => {
    if (screen !== "playing" || isCorrect !== null) return;
    timerRef.current = setInterval(() => setTimer(t => t + 100), 100);
    return () => clearInterval(timerRef.current);
  }, [screen, isCorrect, currentRound]);

  useEffect(() => {
    if (screen !== "playing" || isCorrect !== null || !currentPlayer) return;
    setRevealedClubs(1);
    revealRef.current = setInterval(() => {
      setRevealedClubs(r => {
        if (r >= currentPlayer.career.length) { clearInterval(revealRef.current); return r; }
        return r + 1;
      });
    }, REVEAL_INTERVAL);
    return () => clearInterval(revealRef.current);
  }, [screen, currentRound, isCorrect, currentPlayer]);

  useEffect(() => {
    if (screen === "playing" && isCorrect === null) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [screen, isCorrect, currentRound]);

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

  const createParty = async (name, roundsPerDay, nickname, avatar) => {
    setLoading(true);
    setError(null);
    try {
      const { party: newParty, member: newMember } = await supabaseCreateParty(name, roundsPerDay, nickname, avatar);
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

  const checkGuess = async () => {
    if (!guess.trim() || !currentPlayer) return;
    const ng = normalize(guess);
    const allAliases = [currentPlayer.name, ...(currentPlayer.aliases || [])];
    const match = allAliases.some(
      a => normalize(a) === ng || normalize(a).includes(ng) || ng.includes(normalize(a))
    );
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
      setGuess("");
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

  const totalScore = scores.reduce((a, s) => a + s.score, 0);

  // ---- HOME ----
  if (screen === "home") {
    return (
      <Container>
        <div style={s.homeWrap}>
          <div style={s.logoSection}>
            <div style={s.ball}>⚽</div>
            <h1 style={s.title}>CAREER<br/>QUIZ</h1>
            <p style={s.subtitle}>Guess football players from their club careers</p>
          </div>
          <div style={s.homeButtons}>
            <button style={s.primaryBtn} onClick={() => setScreen("create")}>Create a Party</button>
            <button style={s.secondaryBtn} onClick={() => setScreen("join")}>Join a Party</button>
          </div>
          <p style={s.footerText}>Challenge your friends on WhatsApp</p>
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

  // ---- LOBBY ----
  if (screen === "lobby") {
    return (
      <Container>
        <div style={s.lobbyWrap}>
          <button style={s.backBtn} onClick={() => setScreen("home")}>← Back</button>
          <div style={s.partyHeader}>
            <h2 style={s.partyName}>{party?.name}</h2>
            <div style={s.codeBadge}>
              <span style={s.codeLabel}>CODE</span>
              <span style={s.codeValue}>{party?.invite_code}</span>
            </div>
          </div>
          <div style={s.configRow}>
            <span style={s.configLabel}>Rounds per day</span>
            <span style={s.configValue}>{party?.rounds_per_day}</span>
          </div>
          <div style={s.membersSection}>
            <div style={s.sectionTitle}>Players ({members.length})</div>
            {members.map((m, i) => (
              <div key={i} style={s.memberRow}>
                <span style={s.memberAvatar}>{m.avatar_emoji}</span>
                <span style={s.memberName}>{m.nickname}</span>
                {m.is_host && <span style={s.hostBadge}>HOST</span>}
              </div>
            ))}
          </div>
          {error && <div style={s.errorText}>{error}</div>}
          <div style={s.lobbyActions}>
            <button style={s.primaryBtn} onClick={startPlaying} disabled={loading}>
              {loading ? "Loading..." : "▶ Play Today's Rounds"}
            </button>
            <button style={s.whatsappBtn} onClick={shareInvite}>📲 Invite via WhatsApp</button>
            <button style={s.outlineBtn} onClick={shareReminder}>🔔 Send Daily Reminder</button>
            <button style={s.ghostBtn} onClick={viewLeaderboard} disabled={loading}>🏆 Leaderboard</button>
          </div>
        </div>
      </Container>
    );
  }

  // ---- PLAYING ----
  if (screen === "playing") {
    return (
      <Container>
        <div style={s.gameWrap}>
          <div style={s.gameHeader}>
            <div style={s.roundBadge}>{currentRound + 1}/{totalRounds}</div>
            <div style={s.timerDisplay}>{formatTime(timer)}</div>
            {streak > 1 && <div style={s.streakBadge}>🔥 {streak}</div>}
          </div>
          <div style={s.careerCard}>
            <div style={s.cardTitle}>SENIOR CAREER</div>
            <div style={s.tableHeader}>
              <span style={s.colYear}>Years</span>
              <span style={s.colClub}>Club</span>
              <span style={s.colStats}>M. (G.)</span>
            </div>
            {currentPlayer?.career.map((c, i) => {
              const visible = i < revealedClubs || isCorrect !== null;
              return (
                <div key={i} style={{
                  ...s.tableRow,
                  opacity: visible ? 1 : 0.08,
                  transform: visible ? "none" : "scale(0.98)",
                  transition: "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                }}>
                  <span style={s.colYear}>{visible ? c.years : "????–????"}</span>
                  <span style={s.colClub}>
                    {visible ? <><span style={s.flag}>{c.country_flag}</span> {c.club}</> : "██████████"}
                  </span>
                  <span style={s.colStats}>{visible ? `${c.matches} (${c.goals})` : "— (—)"}</span>
                </div>
              );
            })}
            <div style={s.dotRow}>
              {currentPlayer?.career.map((_, i) => (
                <div key={i} style={{
                  ...s.dot,
                  background: i < revealedClubs || isCorrect !== null ? "#3b82f6" : "rgba(255,255,255,0.15)",
                }} />
              ))}
            </div>
          </div>
          {isCorrect === null ? (
            <div style={s.inputArea}>
              <div style={s.inputRow}>
                <input ref={inputRef} type="text" value={guess}
                  onChange={e => setGuess(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && checkGuess()}
                  placeholder="Type player name..." style={s.input}
                  autoComplete="off" autoCorrect="off" autoCapitalize="off" />
                <button style={s.submitBtn} onClick={checkGuess}>→</button>
              </div>
              <button style={s.giveUpBtn} onClick={giveUp}>I don't know</button>
            </div>
          ) : (
            <div style={s.resultArea}>
              <div style={{
                ...s.resultBanner,
                background: isCorrect ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
                borderColor: isCorrect ? "#22c55e" : "#ef4444",
              }}>
                <div style={s.resultEmoji}>{isCorrect ? "✅" : "❌"}</div>
                <div>
                  <div style={{ ...s.resultTitle, color: isCorrect ? "#22c55e" : "#ef4444" }}>
                    {isCorrect ? "Correct!" : "Wrong!"}
                  </div>
                  <div style={s.resultName}>{currentPlayer?.name}</div>
                  {isCorrect && (
                    <div style={s.resultMeta}>
                      +{scores[scores.length - 1]?.score} pts · {formatTime(timer)} · {revealedClubs} club{revealedClubs > 1 ? "s" : ""}
                    </div>
                  )}
                </div>
              </div>
              <button style={s.nextBtn} onClick={nextRound}>
                {currentRound + 1 >= totalRounds ? "See Results" : "Next Player →"}
              </button>
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
        <div style={s.resultWrap}>
          <div style={s.scoreHeader}>
            <div style={s.finalScore}>{totalScore}</div>
            <div style={s.finalLabel}>POINTS</div>
            <div style={s.finalSub}>{correct}/{totalRounds} correct</div>
          </div>
          <div style={s.scoresList}>
            {scores.map((sc, i) => (
              <div key={i} style={{ ...s.scoreRow, borderLeft: sc.score > 0 ? "3px solid #22c55e" : "3px solid #ef4444" }}>
                <div>
                  <div style={s.scorePlayer}>{sc.player}</div>
                  <div style={s.scoreMeta}>{formatTime(sc.time)} · {sc.clubs} club{sc.clubs > 1 ? "s" : ""}</div>
                </div>
                <div style={{ ...s.scorePoints, color: sc.score > 0 ? "#22c55e" : "#ef4444" }}>
                  {sc.score > 0 ? `+${sc.score}` : "0"}
                </div>
              </div>
            ))}
          </div>
          <div style={s.btnCol}>
            <button style={s.whatsappBtn} onClick={shareScore}>📤 Share on WhatsApp</button>
            <button style={s.secondaryBtn} onClick={viewLeaderboard}>🏆 Leaderboard</button>
            <button style={s.ghostBtn} onClick={() => setScreen("lobby")}>Back to Lobby</button>
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
        <div style={s.lbWrap}>
          <button style={s.backBtn} onClick={() => setScreen("lobby")}>← Back</button>
          <h2 style={s.lbTitle}>🏆 Leaderboard</h2>
          <p style={s.lbParty}>{party?.name}</p>
          {sorted.length === 0 ? (
            <p style={s.emptyText}>No scores yet. Play today's rounds!</p>
          ) : (
            <div style={s.lbList}>
              {sorted.map((entry, i) => (
                <div key={i} style={{ ...s.lbRow, background: i === 0 ? "rgba(250,204,21,0.08)" : "rgba(255,255,255,0.04)" }}>
                  <div style={s.lbRank}>{i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}`}</div>
                  <div style={s.lbAvatar}>{entry.avatar_emoji}</div>
                  <div style={s.lbInfo}>
                    <div style={s.lbName}>{entry.nickname}</div>
                    <div style={s.lbSub}>{entry.correct_answers} correct</div>
                  </div>
                  <div style={s.lbScore}>{entry.total_points}</div>
                </div>
              ))}
            </div>
          )}
          <button style={s.whatsappBtn} onClick={shareReminder}>🔔 Send Reminder to Play</button>
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

  return (
    <div style={s.formWrap}>
      <button style={s.backBtn} onClick={onBack}>← Back</button>
      <h2 style={s.formTitle}>Create a Party</h2>
      <label style={s.label}>Party name</label>
      <input style={s.formInput} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. The Legends" />
      <label style={s.label}>Rounds per day</label>
      <div style={s.roundPicker}>
        {[3, 5, 10].map(n => (
          <button key={n} onClick={() => setRounds(n)} style={{ ...s.roundOption, ...(rounds === n ? s.roundActive : {}) }}>{n}</button>
        ))}
      </div>
      <label style={s.label}>Your nickname</label>
      <input style={s.formInput} value={nickname} onChange={e => setNickname(e.target.value)} placeholder="e.g. Zizou" />
      <label style={s.label}>Pick your avatar</label>
      <div style={s.avatarGrid}>
        {AVATARS.map(a => (
          <button key={a} onClick={() => setAvatar(a)} style={{ ...s.avatarBtn, ...(avatar === a ? s.avatarActive : {}) }}>{a}</button>
        ))}
      </div>
      {error && <div style={s.errorText}>{error}</div>}
      <button style={{ ...s.primaryBtn, opacity: name && nickname && !loading ? 1 : 0.4, pointerEvents: name && nickname && !loading ? "auto" : "none", marginTop: 24 }}
        onClick={() => onCreate(name, rounds, nickname, avatar)}>
        {loading ? "Creating..." : "Create Party"}
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

  return (
    <div style={s.formWrap}>
      <button style={s.backBtn} onClick={onBack}>← Back</button>
      <h2 style={s.formTitle}>Join a Party</h2>
      <label style={s.label}>Invite code</label>
      <input style={{ ...s.formInput, textTransform: "uppercase", letterSpacing: "4px", textAlign: "center", fontSize: 22, fontWeight: 800 }}
        value={code} onChange={e => setCode(e.target.value.toUpperCase().slice(0, 6))} placeholder="ABC123" maxLength={6} />
      <label style={s.label}>Your nickname</label>
      <input style={s.formInput} value={nickname} onChange={e => setNickname(e.target.value)} placeholder="e.g. Ronaldo" />
      <label style={s.label}>Pick your avatar</label>
      <div style={s.avatarGrid}>
        {AVATARS.map(a => (
          <button key={a} onClick={() => setAvatar(a)} style={{ ...s.avatarBtn, ...(avatar === a ? s.avatarActive : {}) }}>{a}</button>
        ))}
      </div>
      {error && <div style={s.errorText}>{error}</div>}
      <button style={{ ...s.primaryBtn, opacity: code.length === 6 && nickname && !loading ? 1 : 0.4, pointerEvents: code.length === 6 && nickname && !loading ? "auto" : "none", marginTop: 24 }}
        onClick={() => onJoin(code, nickname, avatar)}>
        {loading ? "Joining..." : "Join Party"}
      </button>
    </div>
  );
}

const s = {
  container: { minHeight: "100vh", background: "#0a0e17", color: "#e2e8f0", fontFamily: "'DM Sans', 'Helvetica Neue', sans-serif", display: "flex", justifyContent: "center" },
  inner: { width: "100%", maxWidth: 420, padding: "0 16px" },
  homeWrap: { padding: "60px 8px 40px", display: "flex", flexDirection: "column", alignItems: "center", gap: 32 },
  logoSection: { textAlign: "center" },
  ball: { fontSize: 56, marginBottom: 12 },
  title: { fontSize: 42, fontWeight: 900, letterSpacing: "-2px", lineHeight: 1, margin: 0, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  subtitle: { color: "#94a3b8", marginTop: 12, fontSize: 15 },
  homeButtons: { width: "100%", display: "flex", flexDirection: "column", gap: 12 },
  footerText: { fontSize: 12, color: "#475569" },
  primaryBtn: { width: "100%", padding: "18px 0", borderRadius: 14, border: "none", background: "linear-gradient(135deg, #3b82f6, #6366f1)", color: "#fff", fontSize: 16, fontWeight: 800, cursor: "pointer", letterSpacing: "0.5px" },
  secondaryBtn: { width: "100%", padding: "16px 0", borderRadius: 14, border: "1px solid rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.06)", color: "#e2e8f0", fontSize: 15, fontWeight: 700, cursor: "pointer" },
  whatsappBtn: { width: "100%", padding: "16px 0", borderRadius: 14, border: "none", background: "linear-gradient(135deg, #25D366, #128C7E)", color: "#fff", fontSize: 15, fontWeight: 700, cursor: "pointer" },
  outlineBtn: { width: "100%", padding: "14px 0", borderRadius: 14, border: "1px solid rgba(255,255,255,0.1)", background: "transparent", color: "#94a3b8", fontSize: 14, fontWeight: 600, cursor: "pointer" },
  ghostBtn: { width: "100%", padding: "14px 0", borderRadius: 14, border: "none", background: "transparent", color: "#64748b", fontSize: 14, fontWeight: 600, cursor: "pointer" },
  backBtn: { background: "none", border: "none", color: "#64748b", fontSize: 14, cursor: "pointer", padding: "16px 0 8px", fontFamily: "inherit" },
  formWrap: { padding: "0 8px 40px" },
  formTitle: { fontSize: 24, fontWeight: 800, margin: "16px 0 24px" },
  label: { display: "block", fontSize: 13, fontWeight: 600, color: "#94a3b8", marginBottom: 8, marginTop: 20 },
  formInput: { width: "100%", padding: "14px 16px", borderRadius: 12, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.06)", color: "#e2e8f0", fontSize: 16, outline: "none", fontFamily: "inherit", boxSizing: "border-box" },
  roundPicker: { display: "flex", gap: 10 },
  roundOption: { flex: 1, padding: "14px 0", borderRadius: 12, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.04)", color: "#94a3b8", fontSize: 18, fontWeight: 800, cursor: "pointer", fontFamily: "inherit" },
  roundActive: { background: "rgba(59,130,246,0.15)", borderColor: "#3b82f6", color: "#3b82f6" },
  avatarGrid: { display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 8 },
  avatarBtn: { padding: "12px 0", borderRadius: 12, border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.04)", fontSize: 24, cursor: "pointer", textAlign: "center" },
  avatarActive: { background: "rgba(59,130,246,0.15)", borderColor: "#3b82f6" },
  lobbyWrap: { padding: "0 8px 40px" },
  partyHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 8 },
  partyName: { fontSize: 22, fontWeight: 800, margin: 0 },
  codeBadge: { display: "flex", flexDirection: "column", alignItems: "center", background: "rgba(255,255,255,0.06)", padding: "8px 16px", borderRadius: 12 },
  codeLabel: { fontSize: 9, fontWeight: 700, letterSpacing: "2px", color: "#64748b" },
  codeValue: { fontSize: 18, fontWeight: 900, letterSpacing: "3px", color: "#3b82f6" },
  configRow: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", marginTop: 16 },
  configLabel: { fontSize: 14, color: "#94a3b8" },
  configValue: { fontSize: 16, fontWeight: 700 },
  membersSection: { marginTop: 24 },
  sectionTitle: { fontSize: 13, fontWeight: 700, color: "#64748b", letterSpacing: "1px", marginBottom: 12 },
  memberRow: { display: "flex", alignItems: "center", gap: 12, padding: "10px 0" },
  memberAvatar: { fontSize: 24 },
  memberName: { fontSize: 15, fontWeight: 600, flex: 1 },
  hostBadge: { fontSize: 10, fontWeight: 800, letterSpacing: "1px", padding: "4px 10px", borderRadius: 20, background: "rgba(250,204,21,0.15)", color: "#facc15" },
  lobbyActions: { display: "flex", flexDirection: "column", gap: 10, marginTop: 32 },
  gameWrap: { padding: "16px 0 32px", display: "flex", flexDirection: "column", gap: 16 },
  gameHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0" },
  roundBadge: { fontSize: 13, fontWeight: 700, color: "#94a3b8", background: "rgba(255,255,255,0.06)", padding: "6px 14px", borderRadius: 20 },
  timerDisplay: { fontSize: 22, fontWeight: 800, fontVariantNumeric: "tabular-nums", letterSpacing: "-0.5px" },
  streakBadge: { fontSize: 13, fontWeight: 700, padding: "6px 14px", borderRadius: 20, background: "rgba(249,115,22,0.15)", color: "#f97316" },
  careerCard: { background: "rgba(255,255,255,0.04)", borderRadius: 16, padding: "20px 16px 16px", border: "1px solid rgba(255,255,255,0.06)" },
  cardTitle: { fontSize: 11, fontWeight: 800, letterSpacing: "2px", color: "#64748b", marginBottom: 14 },
  tableHeader: { display: "flex", fontSize: 11, color: "#475569", fontWeight: 600, paddingBottom: 8, borderBottom: "1px solid rgba(255,255,255,0.06)", marginBottom: 4 },
  tableRow: { display: "flex", padding: "10px 0", fontSize: 14, borderBottom: "1px solid rgba(255,255,255,0.03)", alignItems: "center" },
  colYear: { width: "30%", fontSize: 13, color: "#94a3b8" },
  colClub: { flex: 1, fontWeight: 600, fontSize: 14 },
  colStats: { width: "22%", textAlign: "right", fontSize: 13, color: "#64748b" },
  flag: { marginRight: 6 },
  dotRow: { display: "flex", gap: 6, justifyContent: "center", marginTop: 14 },
  dot: { width: 8, height: 8, borderRadius: "50%", transition: "background 0.3s" },
  inputArea: { display: "flex", flexDirection: "column", gap: 10, alignItems: "center" },
  inputRow: { display: "flex", gap: 8, width: "100%" },
  input: { flex: 1, padding: "16px 18px", borderRadius: 14, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.06)", color: "#e2e8f0", fontSize: 16, outline: "none", fontFamily: "inherit" },
  submitBtn: { padding: "16px 22px", borderRadius: 14, border: "none", background: "#3b82f6", color: "#fff", fontSize: 20, fontWeight: 700, cursor: "pointer" },
  giveUpBtn: { background: "none", border: "none", color: "#475569", fontSize: 13, cursor: "pointer", padding: "8px 16px" },
  resultArea: { display: "flex", flexDirection: "column", gap: 12 },
  resultBanner: { display: "flex", alignItems: "center", gap: 14, padding: "18px 20px", borderRadius: 14, border: "1px solid" },
  resultEmoji: { fontSize: 32 },
  resultTitle: { fontWeight: 800, fontSize: 16 },
  resultName: { fontSize: 20, fontWeight: 800, marginTop: 2 },
  resultMeta: { fontSize: 13, color: "#94a3b8", marginTop: 4 },
  nextBtn: { width: "100%", padding: "16px 0", borderRadius: 14, border: "none", background: "rgba(255,255,255,0.08)", color: "#e2e8f0", fontSize: 15, fontWeight: 700, cursor: "pointer" },
  resultWrap: { padding: "40px 8px", display: "flex", flexDirection: "column", gap: 24 },
  scoreHeader: { textAlign: "center" },
  finalScore: { fontSize: 64, fontWeight: 900, lineHeight: 1, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  finalLabel: { fontSize: 13, fontWeight: 800, letterSpacing: "3px", color: "#64748b", marginTop: 4 },
  finalSub: { fontSize: 15, color: "#94a3b8", marginTop: 8 },
  scoresList: { display: "flex", flexDirection: "column", gap: 8 },
  scoreRow: { display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(255,255,255,0.04)", padding: "14px 16px", borderRadius: 12 },
  scorePlayer: { fontWeight: 700, fontSize: 15 },
  scoreMeta: { fontSize: 12, color: "#64748b", marginTop: 2 },
  scorePoints: { fontWeight: 800, fontSize: 18 },
  btnCol: { display: "flex", flexDirection: "column", gap: 10 },
  lbWrap: { padding: "0 8px 40px" },
  lbTitle: { fontSize: 24, fontWeight: 800, margin: "16px 0 4px" },
  lbParty: { fontSize: 14, color: "#64748b", marginBottom: 24 },
  lbList: { display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 },
  lbRow: { display: "flex", alignItems: "center", gap: 12, padding: "16px", borderRadius: 14, border: "1px solid rgba(255,255,255,0.06)" },
  lbRank: { fontSize: 20, width: 32, textAlign: "center", fontWeight: 800 },
  lbAvatar: { fontSize: 28 },
  lbInfo: { flex: 1 },
  lbName: { fontWeight: 700, fontSize: 16 },
  lbSub: { fontSize: 12, color: "#64748b", marginTop: 2 },
  lbScore: { fontSize: 22, fontWeight: 900, background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  emptyText: { fontSize: 14, color: "#475569", textAlign: "center", padding: "40px 0" },
  errorText: { color: "#ef4444", fontSize: 14, marginTop: 12, textAlign: "center" },
};
