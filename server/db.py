import sqlite3, json, os, secrets, base64, hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tennis.db"
USERS_FILE = Path(__file__).parent.parent / "users.json"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + dk).decode()


def _verify_password(password: str, stored: str) -> bool:
    try:
        data = base64.b64decode(stored)
        salt, dk = data[:16], data[16:]
        new_dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return secrets.compare_digest(dk, new_dk)
    except Exception:
        return False


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tokens (
        token TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        seed INTEGER,
        photo TEXT,
        created_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS matches (
        id TEXT PRIMARY KEY,
        court_id TEXT NOT NULL,
        player1_id TEXT,
        player2_id TEXT,
        player1b_id TEXT,
        player2b_id TEXT,
        mode TEXT DEFAULT 'singles',
        sets_to_win INTEGER DEFAULT 3,
        games_per_set INTEGER DEFAULT 6,
        tiebreak_at INTEGER DEFAULT 7,
        tiebreak_win_by INTEGER DEFAULT 2,
        server INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        winner INTEGER,
        created_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS match_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        photo TEXT NOT NULL,
        caption TEXT,
        scored_by TEXT,
        scored_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS match_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        set_index INTEGER NOT NULL,
        p1_games INTEGER DEFAULT 0,
        p2_games INTEGER DEFAULT 0,
        in_tiebreak INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS match_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT NOT NULL,
        set_index INTEGER NOT NULL,
        point_index INTEGER NOT NULL,
        winner INTEGER NOT NULL,
        scored_by TEXT NOT NULL,
        scored_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS current_games (
        match_id TEXT PRIMARY KEY,
        p1_points INTEGER DEFAULT 0,
        p2_points INTEGER DEFAULT 0,
        set_index INTEGER DEFAULT 0
    );
    """)

    conn.commit()

    # Seed users from users.json into DB if table is empty
    count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    if count == 0 and USERS_FILE.exists():
        try:
            with open(USERS_FILE) as f:
                users = json.load(f)
            for u in users:
                pwd_hash = _hash_password(u["password"])
                try:
                    conn.execute(
                        "INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                        (u["username"], pwd_hash, u["name"])
                    )
                except Exception:
                    pass
            conn.commit()
        except Exception as e:
            print(f"Warning: could not seed users from users.json: {e}")

    conn.close()
    print("Database initialized")


# ─── Auth ─────────────────────────────────────────────────────────────────────

def verify_user(username: str, password: str) -> dict | None:
    conn = get_db()
    cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if not _verify_password(password, row["password_hash"]):
        return None
    return {"username": row["username"], "name": row["name"]}


def create_token(username: str) -> str:
    return secrets.token_hex(24)


def save_token(token: str, user: dict):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO tokens (token, username) VALUES (?, ?)",
        (token, user["username"])
    )
    conn.commit()
    conn.close()


def delete_token(token: str):
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def get_user_from_token(token: str) -> str | None:
    conn = get_db()
    cur = conn.execute("SELECT username FROM tokens WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    return row["username"] if row else None


# ─── User management ──────────────────────────────────────────────────────────

def list_users() -> list[dict]:
    conn = get_db()
    cur = conn.execute("SELECT username, name FROM users ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_user_by_username(username: str) -> dict | None:
    conn = get_db()
    cur = conn.execute("SELECT username, name FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username: str, password: str, name: str) -> None:
    pwd_hash = _hash_password(password)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
            (username, pwd_hash, name)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Usuário '{username}' já existe")
    conn.close()


def delete_user(username: str) -> None:
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE username = ?", (username,))
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
