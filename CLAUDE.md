# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Beach Tênis Score Bordon** — mobile-first web app for scoring beach tennis matches. React + TypeScript frontend, FastAPI + SQLite backend.

## Running the app

**Development** — two processes needed (Vite has no proxy config, so run backend first):

```powershell
# Terminal 1 — FastAPI backend on :5176
cd beach-tennis-score
uvicorn server.main:app --host 0.0.0.0 --port 5176 --reload

# Terminal 2 — Vite dev server
cd beach-tennis-score
npm run dev
```

> In dev, `api.ts` uses `API_BASE = '/api'` (relative), so Vite's dev server must proxy `/api` to `:5176`. **This proxy is NOT configured in `vite.config.ts`** — add it or test against the built app.

**Production** — build then run the Python proxy:

```powershell
npm run build                  # outputs to dist/
python proxy.py                # serves dist/ on :5175, proxies /api/* → :5176
# separately: uvicorn server.main:app --port 5176
```

**Lint / typecheck:**

```powershell
npm run lint
npm run build   # tsc -b catches type errors
```

## Architecture

```
beach-tennis-score/
├── src/
│   ├── App.tsx       # All UI: LoginScreen, SetupScreen, HomeScreen, CourtScreen, MatchScreen
│   ├── api.ts        # Typed fetch wrapper + ptLabel/setsWon helpers
│   └── types.ts      # Shared TS types
├── server/
│   ├── main.py       # All FastAPI routes + scoring logic (apply_point)
│   └── db.py         # SQLite init, user auth (users.json), in-memory token store
├── proxy.py          # Production: static file server + /api proxy (port 5175)
├── tennis.db         # SQLite DB (committed, pre-seeded)
└── users.json        # Users with plaintext passwords (admin/rafael/andre)
```

**Navigation**: Hash-based routing (`#/match/<id>`). App state flows: `login → setup → home → court → match`.

**DB tables**: `players`, `courts`, `matches`, `match_sets`, `current_games`, `match_points`, `match_photos`, `users` (unused — auth reads `users.json`).

## Scoring logic

All in `server/main.py:apply_point()`. Points use integers: `0→15→30→40→50(AD)→60(GAME)`. Value `60` triggers game-won logic; `50` = advantage. Set completion checked via `set_done()` nested function respecting `tiebreak_at` and `tiebreak_win_by` config.

## Auth

- Users defined in `users.json` (plaintext passwords, no bcrypt).
- Tokens are random hex stored in **in-memory `TOKENS` dict** — lost on server restart.
- `Authorization: Bearer <token>` header required on all endpoints except `/api/health`.

## Key constraints

- `tennis.db` and `users.json` are committed — do not `.gitignore` them, they seed the app.
- Photos stored as base64 in SQLite (`photo TEXT` column) — no file system uploads.
- Vite proxy is missing for dev: either add `server.proxy` to `vite.config.ts` or use `proxy.py` after building.
