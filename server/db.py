import sqlite3, json, os, secrets, base64
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tennis.db"
USERS_FILE = Path(__file__).parent.parent / "users.json"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    conn.close()
    print("Database initialized")

def verify_user(username: str, password: str) -> dict | None:
    with open(USERS_FILE) as f:
        users = json.load(f)
    for u in users:
        if u["username"] == username and u["password"] == password:
            return {"username": u["username"], "name": u["name"]}
    return None

def create_token(username: str) -> str:
    return secrets.token_hex(24)

TOKENS = {}

def save_token(token: str, user: dict):
    TOKENS[token] = user

def verify_token(token: str) -> dict | None:
    return TOKENS.get(token)

def get_user_from_token(token: str) -> str:
    user = verify_token(token)
    return user["username"] if user else None