import { useState, useEffect } from 'react';
import { api, setToken, getToken, ptLabel, setsWon } from './api';

type MatchConfig = {
  mode: 'singles' | 'doubles';
  setsToWin: number;
  gamesPerSet: number;
  tiebreakAt: number;
  tiebreakWinBy: number;
};

type Player = { id: string; name: string; seed?: number; photo?: string };
type MatchPhoto = { id: number; match_id: string; photo: string; caption?: string };
type Match = {
  id: string; court_id: string; mode: string; sets_to_win: number; games_per_set: number;
  tiebreak_at: number; tiebreak_win_by: number; server: number; status: string; winner: number | null;
  player1: Player | null; player2: Player | null; player1b: Player | null; player2b: Player | null;
  sets: { p1: number; p2: number }[]; current_game: { p1_points: number; p2_points: number };
};
type Court = { id: string; name: string; match_count: number };
type User = { username: string; name: string };
type Screen = 'login' | 'setup' | 'home' | 'court' | 'match' | 'users';

// ─── Player Avatar ────────────────────────────────────────────────────────────

const AVATAR_COLORS = ['#3b82f6', '#22c55e', '#ef4444', '#eab308', '#8b5cf6', '#f97316', '#06b6d4'];

function avatarColor(name: string): string {
  return AVATAR_COLORS[name.charCodeAt(0) % AVATAR_COLORS.length];
}

function PlayerAvatar({ player, size = 32, onClick }: {
  player: Player | null;
  size?: number;
  onClick?: () => void;
}) {
  const base: React.CSSProperties = {
    width: size, height: size, borderRadius: '50%', flexShrink: 0,
    cursor: onClick ? 'pointer' : 'default',
  };
  if (!player) return null;
  if (player.photo) {
    return (
      <img src={player.photo} alt={player.name} onClick={onClick}
        style={{ ...base, objectFit: 'cover', border: '2px solid #334155' }} />
    );
  }
  const initial = player.name.charAt(0).toUpperCase();
  return (
    <div onClick={onClick} style={{
      ...base, background: avatarColor(player.name), color: 'white',
      fontSize: Math.round(size * 0.44), fontWeight: 800,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      {initial}
    </div>
  );
}

// ─── Login Screen ────────────────────────────────────────────────────────────

function LoginScreen({ onLogin }: { onLogin: (username: string, name: string) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.auth.login(username, password);
      setToken(res.token);
      onLogin(res.username, res.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Usuário ou senha incorretos');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen login-screen">
      <div className="app-logo">🎾</div>
      <h1 className="app-title">Beach Tênis Score Bordon</h1>
      <p className="app-subtitle">Faça login para continuar</p>
      <form onSubmit={handleSubmit} className="login-form">
        <input className="input" placeholder="Usuário" value={username}
          onChange={e => setUsername(e.target.value)} autoComplete="username" />
        <input className="input" type="password" placeholder="Senha" value={password}
          onChange={e => setPassword(e.target.value)} autoComplete="current-password" />
        {error && <div className="error-msg">{error}</div>}
        <button type="submit" className="btn-login" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}

// ─── Setup Screen ────────────────────────────────────────────────────────────

function SetupScreen({ onStart }: { onStart: (config: MatchConfig) => void }) {
  const [mode, setMode] = useState<'singles' | 'doubles'>('singles');
  const [setsToWin, setSetsToWin] = useState(3);
  const [gamesPerSet, setGamesPerSet] = useState(6);
  const [tiebreakAt, setTiebreakAt] = useState(7);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onStart({ mode, setsToWin, gamesPerSet, tiebreakAt, tiebreakWinBy: 2 });
  }

  return (
    <div className="screen setup-screen">
      <div className="app-logo">🎾</div>
      <h1 className="app-title">Beach Tênis Score Bordon</h1>
      <p className="app-subtitle">Configure a partida</p>
      <form onSubmit={handleSubmit} className="setup-form">
        <div className="form-group">
          <label className="form-label">Modalidade</label>
          <div className="toggle-row">
            <button type="button" className={`toggle-btn ${mode === 'singles' ? 'active' : ''}`}
              onClick={() => setMode('singles')}>🎾 Simples</button>
            <button type="button" className={`toggle-btn ${mode === 'doubles' ? 'active' : ''}`}
              onClick={() => setMode('doubles')}>🎾 Duplas</button>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Sets pra fechar a partida</label>
          <div className="toggle-row">
            {[2, 3, 5].map(n => (
              <button key={n} type="button" className={`toggle-btn ${setsToWin === n ? 'active' : ''}`}
                onClick={() => setSetsToWin(n)}>
                {n === 2 ? 'Melhor de 3' : n === 3 ? 'Melhor de 5' : 'Melhor de 7'} ({n} sets)
              </button>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Games por set</label>
          <div className="toggle-row">
            {[4, 6].map(n => (
              <button key={n} type="button" className={`toggle-btn ${gamesPerSet === n ? 'active' : ''}`}
                onClick={() => setGamesPerSet(n)}> {n} games</button>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Tiebreak</label>
          <div className="toggle-row">
            <button type="button" className={`toggle-btn ${tiebreakAt === 7 ? 'active' : ''}`}
              onClick={() => setTiebreakAt(7)}>Sim (7 pts)</button>
            <button type="button" className={`toggle-btn ${tiebreakAt === 0 ? 'active' : ''}`}
              onClick={() => setTiebreakAt(0)}>Não</button>
          </div>
        </div>
        <div className="setup-summary">
          {setsToWin === 2 ? 'Melhor de 3' : setsToWin === 3 ? 'Melhor de 5' : 'Melhor de 7'}
          {gamesPerSet === 4 ? ' · 4 games/set' : ' · 6 games/set'}
          {tiebreakAt > 0 ? ' · Tiebreak a 7' : ' · Sem tiebreak'}
          {mode === 'doubles' ? ' · Duplas' : ' · Simples'}
        </div>
        <button type="submit" className="btn-start-match">Começar 🎾</button>
      </form>
    </div>
  );
}

// ─── Home Screen ─────────────────────────────────────────────────────────────

function HomeScreen({ config, user, onSelectCourt, onLogout, onBackToSetup, onManageUsers }: {
  config: MatchConfig;
  user: User | null;
  onSelectCourt: (id: string) => void;
  onLogout: () => void;
  onBackToSetup: () => void;
  onManageUsers: () => void;
}) {
  const [courts, setCourts] = useState<Court[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [newPlayerSeed, setNewPlayerSeed] = useState('');
  const [newPlayerPhoto, setNewPlayerPhoto] = useState<string | undefined>();
  const [error, setError] = useState('');

  function load() {
    api.courts.list().then(setCourts).catch(() => {});
    api.players.list().then(setPlayers).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function addPlayer(e: React.FormEvent) {
    e.preventDefault();
    if (!newPlayerName.trim()) return;
    try {
      const p = await api.players.create(newPlayerName.trim(), newPlayerSeed ? parseInt(newPlayerSeed) : undefined, newPlayerPhoto);
      setPlayers(prev => [...prev, p]);
      setNewPlayerName(''); setNewPlayerSeed('');
      setNewPlayerPhoto(undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar jogador');
    }
  }

  async function removePlayer(id: string) {
    await api.players.delete(id);
    setPlayers(prev => prev.filter(p => p.id !== id));
  }

  async function removeCourt(id: string) {
    await api.courts.delete(id);
    setCourts(prev => prev.filter(c => c.id !== id));
  }

  async function addCourt() {
    const name = prompt('Nome da quadra:');
    if (!name) return;
    try {
      const c = await api.courts.create(name);
      setCourts(prev => [...prev, c]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar quadra');
    }
  }

  return (
    <div className="screen home-screen">
      <div className="home-header">
        <div className="home-title-block">
          <span className="app-logo-small">🎾</span>
          <h1 className="app-title-sm">Beach Tênis Score Bordon</h1>
        </div>
        <div className="home-actions">
          {user?.username === 'admin' && (
            <button className="btn-icon" onClick={onManageUsers} title="Gerenciar usuários">👥</button>
          )}
          <button className="btn-icon" onClick={onBackToSetup} title="Configurações">⚙️</button>
          <button className="btn-icon" onClick={onLogout} title="Sair">🚪</button>
        </div>
      </div>

      <div className="config-badge">
        {config.setsToWin === 2 ? 'Melhor de 3' : config.setsToWin === 3 ? 'Melhor de 5' : 'Melhor de 7'}
        · {config.gamesPerSet} games/set · {config.mode === 'doubles' ? 'Duplas' : 'Simples'}
      </div>

      {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      {/* Players */}
      <section className="section">
        <h3 className="section-title">🏃 Jogadores ({players.length})</h3>
        <div className="players-grid">
          {players.map(p => (
            <div key={p.id} className="player-chip">
              <label className="chip-avatar-edit" title="Clique para trocar foto">
                <PlayerAvatar player={p} size={28} />
                <input type="file" accept="image/*" style={{ display: 'none' }}
                  onChange={async e => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    const reader = new FileReader();
                    reader.onload = async ev => {
                      const photo = ev.target?.result as string;
                      try {
                        const updated = await api.players.update(p.id, { photo });
                        setPlayers(prev => prev.map(x => x.id === p.id ? { ...x, photo: updated.photo } : x));
                      } catch { /* silent photo update failure */ }
                    };
                    reader.readAsDataURL(file);
                    e.target.value = '';
                  }} />
              </label>
              <span>{p.name}</span>
              {p.seed && <span className="seed-badge">{p.seed}º</span>}
              <button className="chip-remove" onClick={() => removePlayer(p.id)}>×</button>
            </div>
          ))}
          {players.length === 0 && <span className="empty-hint">Cadastre jogadores</span>}
        </div>
        <form onSubmit={addPlayer} className="add-player-form">
          <input className="input" placeholder="Nome do jogador" value={newPlayerName}
            onChange={e => setNewPlayerName(e.target.value)} />
          <input className="input seed-input" placeholder="Nº" type="number" min="1"
            value={newPlayerSeed} onChange={e => setNewPlayerSeed(e.target.value)} />
          <label className="photo-picker-btn" title="Adicionar foto">
            {newPlayerPhoto ? '📷✓' : '📷'}
            <input type="file" accept="image/*" capture="environment"
              onChange={async e => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = ev => { setNewPlayerPhoto(ev.target?.result as string); };
                reader.readAsDataURL(file);
                e.target.value = '';
              }} style={{ display: 'none' }} />
          </label>
          <button type="submit" className="btn btn-primary">+</button>
        </form>
        {newPlayerPhoto && (
          <div className="photo-preview">
            <img src={newPlayerPhoto} alt="preview" />
            <button onClick={() => setNewPlayerPhoto(undefined)}>×</button>
          </div>
        )}
      </section>

      {/* Courts */}
      <section className="section">
        <div className="section-header">
          <h3 className="section-title">🏟️ Quadras ({courts.length})</h3>
          <button className="btn btn-primary" onClick={addCourt}>+ Quadra</button>
        </div>
        <div className="courts-list">
          {courts.map(c => (
            <div key={c.id} className="court-card" onClick={() => onSelectCourt(c.id)}>
              <div className="court-info">
                <span className="court-name">{c.name}</span>
                <span className="court-meta">{c.match_count} partida{c.match_count !== 1 ? 's' : ''}</span>
              </div>
              <button className="court-remove" onClick={e => { e.stopPropagation(); removeCourt(c.id); }}>×</button>
            </div>
          ))}
          {courts.length === 0 && <span className="empty-hint">Nenhuma quadra cadastrada</span>}
        </div>
      </section>
    </div>
  );
}

// ─── Court Screen ─────────────────────────────────────────────────────────────

function CourtScreen({ courtId, config, onBack }: { courtId: string; config: MatchConfig; onBack: () => void }) {
  const [court, setCourt] = useState<{ id: string; name: string } | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);

  useEffect(() => {
    api.courts.list().then(cs => {
      const c = (cs as Court[]).find(x => x.id === courtId);
      setCourt(c || null);
    }).catch(() => {});
    api.players.list().then(setPlayers).catch(() => {});
    api.courts.matches(courtId).then(setMatches).catch(() => {});
  }, [courtId]);

  async function addMatch() {
    const m = await api.courts.createMatch(courtId, {
      court_id: courtId, mode: config.mode, sets_to_win: config.setsToWin,
      games_per_set: config.gamesPerSet, tiebreak_at: config.tiebreakAt,
      tiebreak_win_by: config.tiebreakWinBy,
    });
    setMatches(prev => [...prev, m]);
  }

  async function updateMatchPlayers(matchId: string, p1: string | null, p2: string | null, p1b: string | null, p2b: string | null) {
    const m = matches.find(x => x.id === matchId);
    if (!m) return;

    const resolve = (id: string | null) => id ? players.find(x => x.id === id) || null : null;
    const optimistic = { ...m, player1: resolve(p1), player2: resolve(p2), player1b: resolve(p1b), player2b: resolve(p2b) };
    setMatches(prev => prev.map(x => x.id === matchId ? optimistic : x));

    try {
      const updated = await api.matches.updatePlayers(matchId, p1, p2, p1b, p2b);
      setMatches(prev => prev.map(x => x.id === matchId ? updated : x));
    } catch {
      setMatches(prev => prev.map(x => x.id === matchId ? m : x));
    }
  }

  async function removeMatch(matchId: string) {
    await api.courts.deleteMatch(courtId, matchId);
    setMatches(prev => prev.filter(m => m.id !== matchId));
  }

  function PlayerSelectRow({ player, label, onChange }: {
    player: Player | null;
    label: string;
    onChange: (id: string | null) => void;
  }) {
    return (
      <div className="player-selector-wrap">
        <PlayerAvatar player={player} size={28} />
        <select className="player-select" value={player?.id ?? ''}
          onChange={e => onChange(e.target.value || null)}>
          <option value="">{label}</option>
          {players.map(pl => (
            <option key={pl.id} value={pl.id}>{pl.name}{pl.seed ? ` (${pl.seed}º)` : ''}</option>
          ))}
        </select>
      </div>
    );
  }

  const p1Sets = (m: Match) => setsWon(m.sets, 1);
  const p2Sets = (m: Match) => setsWon(m.sets, 2);

  return (
    <div className="screen court-screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>← Início</button>
        <h2 className="screen-title">{court?.name ?? '...'}</h2>
      </div>

      <div className="court-matches">
        {matches.map((m) => (
          <div key={m.id} className={`match-card ${m.status === 'complete' ? 'complete' : ''}`}>
            <div className="match-card-header">
              <span className="match-label">Partida</span>
              {m.status === 'complete' && <span className="match-status done">✅</span>}
              {m.status === 'live' && <span className="match-status live">🔴</span>}
              {m.status === 'pending' && <span className="match-status pending">⏳</span>}
            </div>

            <div className="match-players">
              {config.mode === 'doubles' ? (
                <>
                  <div className="doubles-team">
                    <div className="team-label">Dupla 1</div>
                    <PlayerSelectRow player={m.player1} label="P1"
                      onChange={id => updateMatchPlayers(m.id, id, m.player2?.id ?? null, m.player1b?.id ?? null, m.player2b?.id ?? null)} />
                    <PlayerSelectRow player={m.player1b} label="P2"
                      onChange={id => updateMatchPlayers(m.id, m.player1?.id ?? null, m.player2?.id ?? null, id, m.player2b?.id ?? null)} />
                  </div>
                  <div className="vs-divider">×</div>
                  <div className="doubles-team">
                    <div className="team-label">Dupla 2</div>
                    <PlayerSelectRow player={m.player2} label="P1"
                      onChange={id => updateMatchPlayers(m.id, m.player1?.id ?? null, id, m.player1b?.id ?? null, m.player2b?.id ?? null)} />
                    <PlayerSelectRow player={m.player2b} label="P2"
                      onChange={id => updateMatchPlayers(m.id, m.player1?.id ?? null, m.player2?.id ?? null, m.player1b?.id ?? null, id)} />
                  </div>
                </>
              ) : (
                <>
                  <PlayerSelectRow player={m.player1} label="Jogador 1"
                    onChange={id => updateMatchPlayers(m.id, id, m.player2?.id ?? null, null, null)} />
                  <div className="vs-divider">×</div>
                  <PlayerSelectRow player={m.player2} label="Jogador 2"
                    onChange={id => updateMatchPlayers(m.id, m.player1?.id ?? null, id, null, null)} />
                </>
              )}
            </div>

            {m.sets.length > 0 && (
              <div className="match-score-preview">
                {m.sets.map((s, i) => (
                  <span key={i} className={`set-chip ${s.p1 > s.p2 ? 'lead' : s.p2 > s.p1 ? 'lead2' : ''}`}>
                    {s.p1}×{s.p2}
                  </span>
                ))}
                {(m.current_game.p1_points > 0 || m.current_game.p2_points > 0) && (
                  <span className="game-chip">
                    {ptLabel(m.current_game.p1_points)} · {ptLabel(m.current_game.p2_points)}
                  </span>
                )}
              </div>
            )}

            <div className="match-info-row">
              <span className="match-sets-score">{p1Sets(m)} × {p2Sets(m)}</span>
            </div>

            <div className="match-actions">
              <button className="btn-start"
                disabled={config.mode === 'doubles'
                  ? !m.player1 || !m.player2 || !m.player1b || !m.player2b
                  : !m.player1 || !m.player2}
                onClick={() => { window.location.hash = `#/match/${m.id}`; }}>
                {m.status === 'complete' ? 'Ver' : m.status === 'live' ? 'Continuar' : 'Iniciar'}
              </button>
              {matches.length > 1 && (
                <button className="btn-remove" onClick={() => removeMatch(m.id)}>🗑</button>
              )}
            </div>
          </div>
        ))}

        <button className="btn-add-match" onClick={addMatch}>+ Nova Partida</button>
      </div>
    </div>
  );
}

// ─── Match Screen ─────────────────────────────────────────────────────────────

function MatchScreen({ matchId, onBack }: { matchId: string; onBack: () => void }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [photos, setPhotos] = useState<MatchPhoto[]>([]);

  useEffect(() => {
    loadMatch();
    loadPhotos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId]);

  async function loadMatch() {
    const courts = await api.courts.list();
    for (const c of courts) {
      const matches = await api.courts.matches(c.id);
      const m = (matches as Match[]).find(x => x.id === matchId);
      if (m) { setMatch(m); return; }
    }
  }

  async function loadPhotos() {
    try {
      const p = await api.matches.listPhotos(matchId);
      setPhotos(p);
    } catch { /* ignore */ }
  }

  async function scorePoint(winner: 1 | 2) {
    if (!match) return;
    const updated = await api.matches.scorePoint(match.id, winner);
    setMatch(updated);
  }

  async function handlePhotoFile(file: File) {
    const reader = new FileReader();
    reader.onload = async ev => {
      const base64 = ev.target?.result as string;
      const p = await api.matches.addPhoto(matchId, base64);
      setPhotos(prev => [...prev, p]);
    };
    reader.readAsDataURL(file);
  }

  if (!match) return <div className="screen"><p className="empty-hint" style={{ marginTop: 80 }}>Carregando...</p></div>;

  const cfg = {
    mode: match.mode as 'singles' | 'doubles',
    setsToWin: match.sets_to_win, gamesPerSet: match.games_per_set,
    tiebreakAt: match.tiebreak_at, tiebreakWinBy: match.tiebreak_win_by,
  };

  const isDoubles = cfg.mode === 'doubles';
  const p1Name = isDoubles
    ? `${match.player1?.name ?? 'P1'}/${match.player1b?.name ?? 'P2'}`
    : match.player1?.name ?? 'Jogador 1';
  const p2Name = isDoubles
    ? `${match.player2?.name ?? 'P1'}/${match.player2b?.name ?? 'P2'}`
    : match.player2?.name ?? 'Jogador 2';
  const p1W = setsWon(match.sets, 1);
  const p2W = setsWon(match.sets, 2);

  const p1ShortName = p1Name.split('/')[0].split(' ')[0];
  const p2ShortName = p2Name.split('/')[0].split(' ')[0];

  return (
    <div className="screen match-screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>← Voltar</button>
      </div>

      <div className="match-score-layout">
        {/* Sets tracker */}
        <div className="sets-tracker">
          <div className="sets-pips">
            {Array.from({ length: cfg.setsToWin }, (_, i) => (
              <div key={i} className={`pip pip-p1 ${i < p1W ? 'filled' : ''}`} />
            ))}
          </div>
          <div className="sets-label">{p1W} × {p2W}</div>
          <div className="sets-pips">
            {Array.from({ length: cfg.setsToWin }, (_, i) => (
              <div key={i} className={`pip pip-p2 ${i < p2W ? 'filled' : ''}`} />
            ))}
          </div>
        </div>

        {/* Players */}
        <div className="players-row">
          <div className="player-name" data-winner={match.winner === 1}>
            <div className="player-avatars">
              <PlayerAvatar player={match.player1} size={40} />
              {isDoubles && <PlayerAvatar player={match.player1b} size={40} />}
            </div>
            <span className="player-name-text">
              {match.winner === 1 && '🏆 '}{p1Name}
              {match.server === 1 && <span className="server-dot" />}
            </span>
          </div>
          <div className="vs-label">×</div>
          <div className="player-name" data-winner={match.winner === 2}>
            <div className="player-avatars">
              <PlayerAvatar player={match.player2} size={40} />
              {isDoubles && <PlayerAvatar player={match.player2b} size={40} />}
            </div>
            <span className="player-name-text">
              {match.winner === 2 && '🏆 '}{p2Name}
              {match.server === 2 && <span className="server-dot" />}
            </span>
          </div>
        </div>

        {/* Sets row */}
        <div className="sets-row">
          {Array.from({ length: Math.max(match.sets.length, cfg.setsToWin * 2 - 1) }, (_, i) => {
            const s = match.sets[i];
            if (!s) return <div key={i} className="set-box empty"><span className="set-num">—</span></div>;
            return (
              <div key={i} className="set-box">
                <span className="set-num" style={{ color: s.p1 > s.p2 ? '#4ade80' : '#94a3b8' }}>{s.p1}</span>
                <span className="set-sep">×</span>
                <span className="set-num" style={{ color: s.p2 > s.p1 ? '#4ade80' : '#94a3b8' }}>{s.p2}</span>
              </div>
            );
          })}
        </div>

        {/* Current game */}
        {match.status !== 'complete' && (
          <div className="current-game">
            <div className="current-game-label">GAME</div>
            <div className="game-points">
              <span className="game-pt">{ptLabel(match.current_game.p1_points)}</span>
              <span className="game-sep">·</span>
              <span className="game-pt">{ptLabel(match.current_game.p2_points)}</span>
            </div>
          </div>
        )}

        {/* Winner */}
        {match.status === 'complete' && match.winner && (
          <div className="winner-banner">
            🏆 {match.winner === 1 ? p1Name : p2Name} venceu {p1W > p2W ? p1W : p2W}×{p2W > p1W ? p2W : p1W}
          </div>
        )}

        {/* Point buttons */}
        {match.status !== 'complete' && (
          <div className="point-buttons">
            <button className="pt-btn pt-btn-p1" onPointerDown={() => scorePoint(1)}>
              {p1ShortName}
            </button>
            <button className="pt-btn pt-btn-p2" onPointerDown={() => scorePoint(2)}>
              {p2ShortName}
            </button>
          </div>
        )}

        {match.status === 'complete' && (
          <button className="btn-reset-score" onClick={async () => {
            await api.matches.reset(match.id);
            loadMatch();
          }}>
            🔄 Reiniciar Pontuação
          </button>
        )}

        {/* Photo section */}
        <div className="match-photo-section">
          <label className="btn-add-photo">
            📷 Adicionar Foto
            <input type="file" accept="image/*" capture="environment" style={{ display: 'none' }}
              onChange={e => { const f = e.target.files?.[0]; if (f) handlePhotoFile(f); e.target.value = ''; }} />
          </label>
          {photos.length > 0 && (
            <div className="photo-gallery">
              {photos.map(ph => (
                <div key={ph.id} className="photo-item">
                  <img src={ph.photo} alt={ph.caption || 'foto'} />
                  <button className="photo-remove" onClick={async () => {
                    await api.matches.deletePhoto(matchId, ph.id);
                    setPhotos(prev => prev.filter(p => p.id !== ph.id));
                  }}>×</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Users Screen ─────────────────────────────────────────────────────────────

function UsersScreen({ user, onBack }: { user: User | null; onBack: () => void }) {
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newName, setNewName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const isAdmin = user?.username === 'admin';

  useEffect(() => {
    api.users.list().then(setUsers).catch(() => {});
  }, []);

  async function createUser(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const u = await api.users.create(newUsername.trim(), newPassword, newName.trim());
      setUsers(prev => [...prev, u]);
      setNewUsername(''); setNewName(''); setNewPassword('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar usuário');
    } finally {
      setLoading(false);
    }
  }

  async function deleteUser(username: string) {
    setError('');
    try {
      await api.users.delete(username);
      setUsers(prev => prev.filter(u => u.username !== username));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao remover usuário');
    }
  }

  return (
    <div className="screen users-screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>← Voltar</button>
        <h2 className="screen-title">Usuários</h2>
      </div>

      {error && <div className="error-msg" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="section">
        <h3 className="section-title">👥 Usuários ({users.length})</h3>
        <div className="users-list">
          {users.map(u => (
            <div key={u.username} className="user-item">
              <div className="user-info">
                <span className="user-name">{u.name}</span>
                <span className="user-username">@{u.username}</span>
              </div>
              {isAdmin && u.username !== 'admin' && (
                <button className="btn-remove-user" onClick={() => deleteUser(u.username)}>🗑</button>
              )}
            </div>
          ))}
        </div>
      </div>

      {isAdmin && (
        <div className="section">
          <h3 className="section-title">+ Novo Usuário</h3>
          <form onSubmit={createUser} className="create-user-form">
            <input className="input" placeholder="Nome completo" value={newName}
              onChange={e => setNewName(e.target.value)} autoComplete="off" />
            <input className="input" placeholder="Nome de usuário (login)" value={newUsername}
              onChange={e => setNewUsername(e.target.value)} autoComplete="off" />
            <input className="input" type="password" placeholder="Senha" value={newPassword}
              onChange={e => setNewPassword(e.target.value)} autoComplete="new-password" />
            <button type="submit" className="btn-login"
              disabled={loading || !newUsername.trim() || !newName.trim() || !newPassword}>
              {loading ? 'Criando...' : 'Criar Usuário'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

// ─── App Root ────────────────────────────────────────────────────────────────

export default function App() {
  const [screen, setScreen] = useState<Screen>('login');
  const [config, setConfig] = useState<MatchConfig>({ mode: 'singles', setsToWin: 3, gamesPerSet: 6, tiebreakAt: 7, tiebreakWinBy: 2 });
  const [selectedCourt, setSelectedCourt] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setToken(token);
      api.auth.me().then(u => {
        setUser(u);
        const hash = window.location.hash;
        if (hash.startsWith('#/match/')) {
          const mid = hash.replace('#/match/', '');
          setSelectedMatch(mid);
          setScreen('match');
        } else {
          setScreen('setup');
        }
      }).catch(() => {
        localStorage.removeItem('token');
      });
    }
  }, []);

  // Hash-based routing for match screen
  useEffect(() => {
    function handleHash() {
      const hash = window.location.hash;
      if (hash.startsWith('#/match/')) {
        const mid = hash.replace('#/match/', '');
        setSelectedMatch(mid);
        setScreen('match');
      }
    }
    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  function handleLogin(username: string, name: string) {
    setUser({ username, name });
    localStorage.setItem('token', getToken() ?? '');
    setScreen('setup');
  }

  function handleLogout() {
    api.auth.logout().catch(() => {});
    setToken('');
    localStorage.removeItem('token');
    setUser(null);
    setScreen('login');
  }

  if (screen === 'login') return <LoginScreen onLogin={handleLogin} />;
  if (screen === 'setup') return <SetupScreen onStart={c => { setConfig(c); setScreen('home'); }} />;
  if (screen === 'home') return (
    <HomeScreen
      config={config}
      user={user}
      onSelectCourt={id => { setSelectedCourt(id); setScreen('court'); }}
      onLogout={handleLogout}
      onBackToSetup={() => setScreen('setup')}
      onManageUsers={() => setScreen('users')}
    />
  );
  if (screen === 'court') return (
    <CourtScreen
      courtId={selectedCourt!}
      config={config}
      onBack={() => setScreen('home')}
    />
  );
  if (screen === 'match') return (
    <MatchScreen
      matchId={selectedMatch!}
      onBack={() => {
        window.location.hash = '';
        setSelectedMatch(null);
        setScreen(selectedCourt ? 'court' : 'home');
      }}
    />
  );
  if (screen === 'users') return (
    <UsersScreen user={user} onBack={() => setScreen('home')} />
  );
  return null;
}
