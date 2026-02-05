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
} from "./lib/supabase";

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
  const [savedParties, setSavedParties] = useState([]);

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
            <span style={s.logoIcon}>⚽</span>
            <h1 style={s.logoTitle}>Career Quiz</h1>
            <p style={s.logoSub}>Guess football players from their club history</p>
          </div>

          {savedParties.length > 0 && (
            <div style={s.section}>
              <div style={s.sectionHeader}>MY PARTIES</div>
              {savedParties.map(({ party, member }) => (
                <button
                  key={party.id}
                  style={s.menuCard}
                  onClick={() => rejoinParty(party, member)}
                >
                  <span style={s.menuIcon}>{member.avatar_emoji || "⚽"}</span>
                  <div style={s.menuText}>
                    <span style={s.menuTitle}>{party.name}</span>
                    <span style={s.menuDesc}>Playing as {member.nickname}</span>
                  </div>
                  <span style={s.menuArrow}>→</span>
                </button>
              ))}
            </div>
          )}

          <div style={s.section}>
            <div style={s.sectionHeader}>GET STARTED</div>
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

          <p style={s.footerNote}>Challenge friends via WhatsApp</p>
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
    return (
      <Container>
        <div style={s.gameWrap}>
          <div style={s.gameTop}>
            <span style={s.roundTag}>{currentRound + 1} / {totalRounds}</span>
            <span style={s.timerText}>{formatTime(timer)}</span>
            {streak > 1 && <span style={s.streakTag}>🔥 {streak}</span>}
          </div>

          <div style={s.careerBox}>
            <div style={s.sectionHeader}>SENIOR CAREER</div>
            <div style={s.careerHeader}>
              <span style={s.colYears}>Years</span>
              <span style={s.colClub}>Club</span>
              <span style={s.colStats}>Apps (Gls)</span>
            </div>
            {currentPlayer?.career.map((c, i) => {
              const visible = i < revealedClubs || isCorrect !== null;
              return (
                <div key={i} style={{
                  ...s.careerRow,
                  opacity: visible ? 1 : 0.1,
                  transition: "opacity 0.4s ease",
                }}>
                  <span style={s.colYears}>{visible ? c.years : "????–????"}</span>
                  <span style={s.colClub}>
                    {visible ? <>{c.country_flag} {c.club}</> : "██████████"}
                  </span>
                  <span style={s.colStats}>{visible ? `${c.matches} (${c.goals})` : "— (—)"}</span>
                </div>
              );
            })}
            <div style={s.progressDots}>
              {currentPlayer?.career.map((_, i) => (
                <span key={i} style={{
                  ...s.dot,
                  background: i < revealedClubs || isCorrect !== null ? "#fff" : "rgba(255,255,255,0.2)",
                }} />
              ))}
            </div>
          </div>

          {isCorrect === null ? (
            <div style={s.guessArea}>
              <div style={s.inputRow}>
                <input
                  ref={inputRef}
                  type="text"
                  value={guess}
                  onChange={e => setGuess(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && checkGuess()}
                  placeholder="Type player name..."
                  style={s.guessInput}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                />
                <button style={s.submitBtn} onClick={checkGuess}>→</button>
              </div>
              <button style={s.skipBtn} onClick={giveUp}>Skip this player</button>
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
                  <span style={s.feedbackName}>{currentPlayer?.name}</span>
                  {isCorrect && (
                    <span style={s.feedbackMeta}>
                      +{scores[scores.length - 1]?.score} pts · {formatTime(timer)} · {revealedClubs} club{revealedClubs > 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>
              <button style={s.nextBtn} onClick={nextRound}>
                {currentRound + 1 >= totalRounds ? "See Results →" : "Next Player →"}
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

  const canSubmit = name.trim() && nickname.trim() && !loading;

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
        onClick={() => canSubmit && onCreate(name, rounds, nickname, avatar)}
      >
        {loading ? "Creating..." : "Create Party →"}
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
};
