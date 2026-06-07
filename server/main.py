from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid, json
from datetime import datetime

from server.db import init_db, get_db, verify_user, create_token, save_token, get_user_from_token
from pathlib import Path

app = FastAPI(title="Tennis Scorer API", version="1.0.0")

# CORS — allow mobile apps and web
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
    photo: Optional[str] = None  # base64 encoded image

class PlayerResponse(BaseModel):
    id: str
    name: str
    seed: Optional[int]

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

class SetScoreModel(BaseModel):
    p1: int
    p2: int

class PhotoCreate(BaseModel):
    match_id: str
    photo: str  # base64
    caption: Optional[str] = None

class PhotoResponse(BaseModel):
    id: int
    match_id: str
    photo: str
    caption: Optional[str]

# ─── Auth helper ─────────────────────────────────────────────────────────────

def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# ─── Auth endpoints ─────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = verify_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(data.username)
    save_token(token, user)
    return TokenResponse(token=token, username=user["username"], name=user["name"])

@app.post("/api/auth/logout")
def logout(authorization: str = Header(None)):
    return {"ok": True}

@app.get("/api/auth/me")
def me(authorization: str = Header(None)):
    username = get_current_user(authorization)
    with open(Path(__file__).parent / "users.json") as f:
        users = json.load(f)
    for u in users:
        if u["username"] == username:
            return {"username": u["username"], "name": u["name"]}
    raise HTTPException(status_code=404)

# ─── Players ─────────────────────────────────────────────────────────────────

@app.get("/api/players", response_model=list[PlayerResponse])
def list_players(authorization: str = Header(None)):
    username = get_current_user(authorization)
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

@app.delete("/api/players/{pid}")
def delete_player(pid: str, authorization: str = Header(None)):
    username = get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM players WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Courts ──────────────────────────────────────────────────────────────────

@app.get("/api/courts", response_model=list[CourtResponse])
def list_courts(authorization: str = Header(None)):
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
    conn = get_db()
    conn.execute("DELETE FROM match_points WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM current_games WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM match_sets WHERE match_id = ?", (mid,))
    conn.execute("DELETE FROM matches WHERE id = ?", (mid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ─── Scoring ─────────────────────────────────────────────────────────────────

POINT_ORDER = [0, 15, 30, 40, 60]

def next_point(p: int) -> int:
    i = POINT_ORDER.index(p) if p in POINT_ORDER else -1
    return POINT_ORDER[i + 1] if i >= 0 and i + 1 < len(POINT_ORDER) else 60

def apply_point(conn, match_id: str, winner: int, scored_by: str):
    cur = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    m = cur.fetchone()
    if not m or m["status"] == "complete":
        return

    cfg = {
        "sets_to_win": m["sets_to_win"],
        "games_per_set": m["games_per_set"],
        "tiebreak_at": m["tiebreak_at"],
        "tiebreak_win_by": m["tiebreak_win_by"],
    }

    cur = conn.execute("SELECT * FROM current_games WHERE match_id = ?", (match_id,))
    cg = cur.fetchone()
    if not cg:
        conn.execute("INSERT INTO current_games (match_id, p1_points, p2_points, set_index) VALUES (?, 0, 0, 0)", (match_id,))
        conn.commit()
        cur = conn.execute("SELECT * FROM current_games WHERE match_id = ?", (match_id,))
        cg = cur.fetchone()

    p1_pts = cg["p1_points"]
    p2_pts = cg["p2_points"]
    set_idx = cg["set_index"]

    win_pt = p1_pts if winner == 1 else p2_pts
    lose_pt = p2_pts if winner == 1 else p1_pts

    # Game won
    if win_pt == 60:
        # Get current set
        cur = conn.execute("SELECT * FROM match_sets WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
        cs = cur.fetchone()
        if not cs:
            conn.execute("INSERT INTO match_sets (match_id, set_index, p1_games, p2_games) VALUES (?, ?, 0, 0)", (match_id, set_idx))
            conn.commit()
            cur = conn.execute("SELECT * FROM match_sets WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
            cs = cur.fetchone()

        # Increment winner games
        if winner == 1:
            conn.execute("UPDATE match_sets SET p1_games = p1_games + 1 WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
        else:
            conn.execute("UPDATE match_sets SET p2_games = p2_games + 1 WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
        conn.commit()

        # Reset game
        conn.execute("UPDATE current_games SET p1_points = 0, p2_points = 0 WHERE match_id = ?", (match_id,))

        # Switch server
        conn.execute("UPDATE matches SET server = CASE server WHEN 1 THEN 2 ELSE 1 END WHERE id = ?", (match_id,))

        # Check set win
        cur = conn.execute("SELECT * FROM match_sets WHERE match_id = ? AND set_index = ?", (match_id, set_idx))
        s = cur.fetchone()
        p1_games = s["p1_games"]
        p2_games = s["p2_games"]

        p1_sets = conn.execute("SELECT COUNT(*) as c FROM match_sets WHERE match_id = ? AND p1_games > p2_games", (match_id,)).fetchone()["c"]
        p2_sets = conn.execute("SELECT COUNT(*) as c FROM match_sets WHERE match_id = ? AND p2_games > p1_games", (match_id,)).fetchone()["c"]

        # Set done?
        tb = cfg["tiebreak_at"]
        win_by_2 = cfg["tiebreak_win_by"]

        def set_done(p1, p2):
            if p1 >= tb or p2 >= tb:
                leader = max(p1, p2)
                trailer = min(p1, p2)
                return leader >= tb and leader - trailer >= win_by_2
            gw = cfg["games_per_set"]
            if p1 >= gw or p2 >= gw:
                if p1 >= gw and p1 - p2 >= 2: return True
                if p2 >= gw and p2 - p1 >= 2: return True
            return False

        if set_done(p1_games, p2_games):
            # Match won?
            if p1_sets >= cfg["sets_to_win"]:
                conn.execute("UPDATE matches SET status = 'complete', winner = 1 WHERE id = ?", (match_id,))
                conn.commit()
                return
            if p2_sets >= cfg["sets_to_win"]:
                conn.execute("UPDATE matches SET status = 'complete', winner = 2 WHERE id = ?", (match_id,))
                conn.commit()
                return
            # New set
            conn.execute("UPDATE current_games SET set_index = set_index + 1 WHERE match_id = ?", (match_id,))
            conn.commit()
        return

    # Advance point
    new_p1 = p1_pts
    new_p2 = p2_pts

    if lose_pt == 40 and new_p1 == 40 and new_p2 == 40:
        new_p1 = 50 if winner == 1 else 40
        new_p2 = 50 if winner == 2 else 40
    elif (new_p1 == 50 or new_p2 == 50) and win_pt != 50:
        new_p1 = 40; new_p2 = 40
    elif win_pt == 50:
        new_p1 = 60; new_p2 = 0
    else:
        nxt = next_point(win_pt)
        if winner == 1: new_p1 = nxt
        else: new_p2 = nxt

    conn.execute("UPDATE current_games SET p1_points = ?, p2_points = ? WHERE match_id = ?", (new_p1, new_p2, match_id))
    conn.commit()

    # Log point
    cur = conn.execute("SELECT set_index FROM current_games WHERE match_id = ?", (match_id,))
    si = cur.fetchone()["set_index"]
    cur = conn.execute("SELECT COUNT(*) as c FROM match_points WHERE match_id = ?", (match_id,))
    pi = cur.fetchone()["c"]
    conn.execute(
        "INSERT INTO match_points (match_id, set_index, point_index, winner, scored_by) VALUES (?, ?, ?, ?, ?)",
        (match_id, si, pi, winner, scored_by)
    )
    conn.commit()

@app.post("/api/matches/{mid}/point")
def score_point(mid: str, data: PointScore, authorization: str = Header(None)):
    username = get_current_user(authorization)
    conn = get_db()
    apply_point(conn, mid, data.winner, username)
    cur = conn.execute("SELECT * FROM matches WHERE id = ?", (mid,))
    match = get_match_response(conn, cur.fetchone())
    conn.close()
    return match

@app.post("/api/matches/{mid}/reset")
def reset_match(mid: str, authorization: str = Header(None)):
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
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
    username = get_current_user(authorization)
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