from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from server.db import (
    init_db, get_db, verify_user, create_token, save_token, delete_token,
    get_user_from_token, list_users as db_list_users, get_user_by_username,
    create_user as db_create_user, delete_user as db_delete_user,
)

app = FastAPI(title="Tennis Scorer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic models ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    username: str
    name: str

class PlayerCreate(BaseModel):
    name: str
    seed: Optional[int] = None
    photo: Optional[str] = None

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    seed: Optional[int] = None
    photo: Optional[str] = None

class PlayerResponse(BaseModel):
    id: str
    name: str
    seed: Optional[int]
    photo: Optional[str] = None

class CourtCreate(BaseModel):
    name: str

class CourtResponse(BaseModel):
    id: str
    name: str
    match_count: int

class MatchCreate(BaseModel):
    court_id: Optional[str] = None
    mode: str = "singles"
    sets_to_win: int = 3
    games_per_set: int = 6
    tiebreak_at: int = 7
    tiebreak_win_by: int = 2
    player1_id: Optional[str] = None
    player2_id: Optional[str] = None
    player1b_id: Optional[str] = None
    player2b_id: Optional[str] = None

class MatchResponse(BaseModel):
    id: str
    court_id: str
    mode: str
    sets_to_win: int
    games_per_set: int
    tiebreak_at: int
    tiebreak_win_by: int
    server: int
    status: str
    winner: Optional[int]
    player1: Optional[PlayerResponse]
    player2: Optional[PlayerResponse]
    player1b: Optional[PlayerResponse]
    player2b: Optional[PlayerResponse]
    sets: list
    current_game: dict

class PointScore(BaseModel):
    match_id: str
    winner: int  # 1 or 2

class PhotoCreate(BaseModel):
    match_id: str
    photo: str  # base64
    caption: Optional[str] = None

class PhotoResponse(BaseModel):
    id: int
    match_id: str
    photo: str
    caption: Optional[str]

class UserCreate(BaseModel):
    username: str
    password: str
    name: str

class UserResponse(BaseModel):
    username: str
    name: str

# ─── Auth helper ─────────────────────────────────────────────────────────────

def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    return user

def require_admin(authorization: str) -> str:
    username = get_current_user(authorization)
    if username != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin pode realizar esta ação")
    return username

# ─── Auth endpoints ─────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = verify_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    token = create_token(data.username)
    save_token(token, user)
    return TokenResponse(token=token, username=user["username"], name=user["name"])

@app.post("/api/auth/logout")
def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        delete_token(token)
    return {"ok": True}

@app.get("/api/auth/me")
def me(authorization: str = Header(None)):
    username = get_current_user(authorization)
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404)
    return user

# ─── User management ─────────────────────────────────────────────────────────

@app.get("/api/users", response_model=list[UserResponse])
def list_users_endpoint(authorization: str = Header(None)):
    get_current_user(authorization)
    return db_list_users()

@app.post("/api/users", response_model=UserResponse)
def create_user_endpoint(data: UserCreate, authorization: str = Header(None)):
    require_admin(authorization)
    if not data.username.strip() or not data.name.strip() or not data.password:
        raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios")
    try:
        db_create_user(data.username.strip(), data.password, data.name.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"username": data.username.strip(), "name": data.name.strip()}

@app.delete("/api/users/{uname}")
def delete_user_endpoint(uname: str, authorization: str = Header(None)):
    username = require_admin(authorization)
    if uname == username:
        raise HTTPException(status_code=400, detail="Não é possível remover seu próprio usuário")
    if uname == "admin":
        raise HTTPException(status_code=400, detail="Não é possível remover o usuário admin")
    db_delete_user(uname)
    return {"ok": True}

# ─── Players ─────────────────────────────────────────────────────────────────

@app.get("/api/players", response_model=list[PlayerResponse])
def list_players(authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    cur = conn.execute("SELECT * FROM players ORDER BY seed NULLS LAST, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/players", response_model=PlayerResponse)
def create_player(data: PlayerCreate, authorization: str = Header(None)):
    username = get_current_user(authorization)
    pid = uuid.uuid4().hex[:8]
    conn = get_db()
    conn.execute(
        "INSERT INTO players (id, name, seed, photo, created_by) VALUES (?, ?, ?, ?, ?)",
        (pid, data.name, data.seed, data.photo, username)
    )
    conn.commit()
    conn.close()
    return {"id": pid, "name": data.name, "seed": data.seed, "photo": data.photo}

@app.patch("/api/players/{pid}", response_model=PlayerResponse)
def update_player(pid: str, data: PlayerUpdate, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    updates = []
    values = []
    if data.name is not None:
        updates.append("name = ?")
        values.append(data.name)
    if data.seed is not None:
        updates.append("seed = ?")
        values.append(data.seed)
    if data.photo is not None:
        updates.append("photo = ?")
        values.append(data.photo)
    if updates:
        values.append(pid)
        conn.execute(f"UPDATE players SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    cur = conn.execute("SELECT * FROM players WHERE id = ?", (pid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return dict(row)

@app.delete("/api/players/{pid}")
def delete_player(pid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM players WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Courts ──────────────────────────────────────────────────────────────────

@app.get("/api/courts", response_model=list[CourtResponse])
def list_courts(authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    cur = conn.execute("""
        SELECT c.*, COUNT(m.id) as match_count
        FROM courts c
        LEFT JOIN matches m ON m.court_id = c.id
        GROUP BY c.id
        ORDER BY c.created_at
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/courts", response_model=CourtResponse)
def create_court(data: CourtCreate, authorization: str = Header(None)):
    username = get_current_user(authorization)
    cid = uuid.uuid4().hex[:8]
    conn = get_db()
    conn.execute(
        "INSERT INTO courts (id, name, created_by) VALUES (?, ?, ?)",
        (cid, data.name, username)
    )
    conn.commit()
    conn.close()
    return {"id": cid, "name": data.name, "match_count": 0}

@app.delete("/api/courts/{cid}")
def delete_court(cid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM match_points WHERE match_id IN (SELECT id FROM matches WHERE court_id = ?)", (cid,))
    conn.execute("DELETE FROM current_games WHERE match_id IN (SELECT id FROM matches WHERE court_id = ?)", (cid,))
    conn.execute("DELETE FROM match_sets WHERE match_id IN (SELECT id FROM matches WHERE court_id = ?)", (cid,))
    conn.execute("DELETE FROM matches WHERE court_id = ?", (cid,))
    conn.execute("DELETE FROM courts WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Matches ─────────────────────────────────────────────────────────────────

def get_player(conn, pid: str):
    if not pid:
        return None
    cur = conn.execute("SELECT * FROM players WHERE id = ?", (pid,))
    r = cur.fetchone()
    return dict(r) if r else None

def get_match_response(conn, match_row) -> dict:
    m = dict(match_row)
    p1 = get_player(conn, m["player1_id"])
    p2 = get_player(conn, m["player2_id"])
    p1b = get_player(conn, m.get("player1b_id"))
    p2b = get_player(conn, m.get("player2b_id"))

    cur = conn.execute("SELECT * FROM match_sets WHERE match_id = ? ORDER BY set_index", (m["id"],))
    sets = [{"p1": r["p1_games"], "p2": r["p2_games"]} for r in cur.fetchall()]

    cur = conn.execute("SELECT * FROM current_games WHERE match_id = ?", (m["id"],))
    cg = cur.fetchone()
    current_game = dict(cg) if cg else {"p1_points": 0, "p2_points": 0}

    return {
        "id": m["id"],
        "court_id": m["court_id"],
        "mode": m["mode"],
        "sets_to_win": m["sets_to_win"],
        "games_per_set": m["games_per_set"],
        "tiebreak_at": m["tiebreak_at"],
        "tiebreak_win_by": m["tiebreak_win_by"],
        "server": m["server"],
        "status": m["status"],
        "winner": m["winner"],
        "player1": p1,
        "player2": p2,
        "player1b": p1b,
        "player2b": p2b,
        "sets": sets,
        "current_game": current_game,
    }

@app.get("/api/courts/{cid}/matches", response_model=list[MatchResponse])
def list_matches(cid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    cur = conn.execute("SELECT * FROM matches WHERE court_id = ? ORDER BY created_at", (cid,))
    matches = [get_match_response(conn, r) for r in cur.fetchall()]
    conn.close()
    return matches

@app.post("/api/courts/{cid}/matches", response_model=MatchResponse)
def create_match(cid: str, data: MatchCreate, authorization: str = Header(None)):
    username = get_current_user(authorization)
    mid = uuid.uuid4().hex[:8]
    conn = get_db()
    conn.execute("""
        INSERT INTO matches (id, court_id, mode, sets_to_win, games_per_set, tiebreak_at, tiebreak_win_by,
                             player1_id, player2_id, player1b_id, player2b_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (mid, cid, data.mode, data.sets_to_win, data.games_per_set, data.tiebreak_at, data.tiebreak_win_by,
          data.player1_id, data.player2_id, data.player1b_id, data.player2b_id, username))
    conn.execute("INSERT INTO current_games (match_id, p1_points, p2_points, set_index) VALUES (?, 0, 0, 0)", (mid,))
    conn.commit()
    cur = conn.execute("SELECT * FROM matches WHERE id = ?", (mid,))
    match = get_match_response(conn, cur.fetchone())
    conn.close()
    return match

@app.patch("/api/matches/{mid}/players")
def update_match_players(mid: str, data: MatchCreate, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("""
        UPDATE matches SET player1_id = ?, player2_id = ?, player1b_id = ?, player2b_id = ?
        WHERE id = ?
    """, (data.player1_id, data.player2_id, data.player1b_id, data.player2b_id, mid))
    conn.commit()
    cur = conn.execute("SELECT * FROM matches WHERE id = ?", (mid,))
    match = get_match_response(conn, cur.fetchone())
    conn.close()
    return match

@app.delete("/api/courts/{cid}/matches/{mid}")
def delete_match(cid: str, mid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM match_points WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM current_games WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM match_sets WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM matches WHERE id = ?", (mid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Scoring ─────────────────────────────────────────────────────────────────

POINT_ORDER = [0, 15, 30, 40]

def next_point(p: int) -> int:
    i = POINT_ORDER.index(p) if p in POINT_ORDER else -1
    return POINT_ORDER[i + 1] if i >= 0 and i + 1 < len(POINT_ORDER) else 40

def _process_game_win(conn, match_id: str, game_winner: int, set_idx: int, cfg: dict):
    """Award a game to game_winner, update set/match state, switch server."""
    cs = conn.execute(
        "SELECT * FROM match_sets WHERE match_id = ? AND set_index = ?", (match_id, set_idx)
    ).fetchone()
    if not cs:
        conn.execute(
            "INSERT INTO match_sets (match_id, set_index, p1_games, p2_games) VALUES (?, ?, 0, 0)",
            (match_id, set_idx)
        )
        conn.commit()

    if game_winner == 1:
        conn.execute("UPDATE match_sets SET p1_games = p1_games + 1 WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
    else:
        conn.execute("UPDATE match_sets SET p2_games = p2_games + 1 WHERE match_id = ? AND set_index = ?", (match_id, set_idx))

    conn.execute("UPDATE current_games SET p1_points = 0, p2_points = 0 WHERE match_id = ?", (match_id,))
    conn.execute("UPDATE matches SET server = CASE server WHEN 1 THEN 2 ELSE 1 END WHERE id = ?", (match_id,))
    conn.commit()

    s = conn.execute(
        "SELECT * FROM match_sets WHERE match_id = ? AND set_index = ?", (match_id, set_idx)
    ).fetchone()
    p1_games = s["p1_games"]
    p2_games = s["p2_games"]

    p1_sets = conn.execute(
        "SELECT COUNT(*) as c FROM match_sets WHERE match_id = ? AND p1_games > p2_games", (match_id,)
    ).fetchone()["c"]
    p2_sets = conn.execute(
        "SELECT COUNT(*) as c FROM match_sets WHERE match_id = ? AND p2_games > p1_games", (match_id,)
    ).fetchone()["c"]

    tb = cfg["tiebreak_at"]
    win_by_2 = cfg["tiebreak_win_by"]
    gw = cfg["games_per_set"]

    def set_done(p1: int, p2: int) -> bool:
        if tb > 0 and (p1 >= tb or p2 >= tb):
            leader, trailer = max(p1, p2), min(p1, p2)
            return leader >= tb and leader - trailer >= win_by_2
        if p1 >= gw or p2 >= gw:
            return (p1 >= gw and p1 - p2 >= 2) or (p2 >= gw and p2 - p1 >= 2)
        return False

    if set_done(p1_games, p2_games):
        if p1_sets >= cfg["sets_to_win"]:
            conn.execute("UPDATE matches SET status = 'complete', winner = 1 WHERE id = ?", (match_id,))
        elif p2_sets >= cfg["sets_to_win"]:
            conn.execute("UPDATE matches SET status = 'complete', winner = 2 WHERE id = ?", (match_id,))
        else:
            conn.execute("UPDATE current_games SET set_index = set_index + 1 WHERE match_id = ?", (match_id,))
        conn.commit()

def apply_point(conn, match_id: str, winner: int, scored_by: str):
    m = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    if not m or m["status"] == "complete":
        return

    cfg = {
        "sets_to_win": m["sets_to_win"],
        "games_per_set": m["games_per_set"],
        "tiebreak_at": m["tiebreak_at"],
        "tiebreak_win_by": m["tiebreak_win_by"],
    }

    cg = conn.execute("SELECT * FROM current_games WHERE match_id = ?", (match_id,)).fetchone()
    if not cg:
        conn.execute(
            "INSERT INTO current_games (match_id, p1_points, p2_points, set_index) VALUES (?, 0, 0, 0)",
            (match_id,)
        )
        conn.commit()
        cg = conn.execute("SELECT * FROM current_games WHERE match_id = ?", (match_id,)).fetchone()

    p1_pts = cg["p1_points"]
    p2_pts = cg["p2_points"]
    set_idx = cg["set_index"]
    win_pt = p1_pts if winner == 1 else p2_pts

    # Compute new point state
    new_p1, new_p2 = p1_pts, p2_pts
    game_won = False

    if p1_pts == 40 and p2_pts == 40:
        # Deuce: give advantage (represented as 50)
        if winner == 1: new_p1 = 50
        else: new_p2 = 50
    elif p1_pts == 50 or p2_pts == 50:
        # One player has advantage
        if win_pt == 50:
            # Advantage player wins the game
            game_won = True
        else:
            # Advantage lost → back to deuce
            new_p1 = 40
            new_p2 = 40
    else:
        # Normal progression: 0→15→30→40→game
        if win_pt == 40:
            game_won = True
        else:
            nxt = next_point(win_pt)
            if winner == 1: new_p1 = nxt
            else: new_p2 = nxt

    # Log point before any state changes (use current set_idx)
    pi = conn.execute("SELECT COUNT(*) as c FROM match_points WHERE match_id = ?", (match_id,)).fetchone()["c"]
    conn.execute(
        "INSERT INTO match_points (match_id, set_index, point_index, winner, scored_by) VALUES (?, ?, ?, ?, ?)",
        (match_id, set_idx, pi, winner, scored_by)
    )
    conn.commit()

    if game_won:
        _process_game_win(conn, match_id, winner, set_idx, cfg)
    else:
        conn.execute(
            "UPDATE current_games SET p1_points = ?, p2_points = ? WHERE match_id = ?",
            (new_p1, new_p2, match_id)
        )
        conn.commit()

@app.post("/api/matches/{mid}/point")
def score_point(mid: str, data: PointScore, authorization: str = Header(None)):
    username = get_current_user(authorization)
    if data.winner not in (1, 2):
        raise HTTPException(status_code=422, detail="winner deve ser 1 ou 2")
    conn = get_db()
    apply_point(conn, mid, data.winner, username)
    cur = conn.execute("SELECT * FROM matches WHERE id = ?", (mid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    match = get_match_response(conn, row)
    conn.close()
    return match

@app.post("/api/matches/{mid}/reset")
def reset_match(mid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM match_points WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM match_sets WHERE match_id = ?", (mid,))
    conn.execute("UPDATE current_games SET p1_points = 0, p2_points = 0, set_index = 0 WHERE match_id = ?", (mid,))
    conn.execute("UPDATE matches SET status = 'pending', winner = NULL, server = 1 WHERE id = ?", (mid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Match Photos ─────────────────────────────────────────────────────────────

@app.get("/api/matches/{mid}/photos", response_model=list[PhotoResponse])
def list_match_photos(mid: str, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    cur = conn.execute(
        "SELECT id, match_id, photo, caption FROM match_photos WHERE match_id = ? ORDER BY scored_at",
        (mid,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/matches/{mid}/photos", response_model=PhotoResponse)
def add_match_photo(mid: str, data: PhotoCreate, authorization: str = Header(None)):
    username = get_current_user(authorization)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO match_photos (match_id, photo, caption, scored_by) VALUES (?, ?, ?, ?)",
        (mid, data.photo, data.caption, username)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": pid, "match_id": mid, "photo": data.photo, "caption": data.caption}

@app.delete("/api/matches/{mid}/photos/{photoid}")
def delete_match_photo(mid: str, photoid: int, authorization: str = Header(None)):
    get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM match_photos WHERE id = ? AND match_id = ?", (photoid, mid))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ─── Init ─────────────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5176)
