Beach Tênis Score Bordon - Review Request

APP: http://100.118.169.20:5175
API: http://100.118.169.20:8002

STACK:
- Frontend: React + TypeScript + Vite (port 5175)
- Backend: FastAPI + SQLite (port 8002)
- Location: /root/tennis-scorer/

KEY FILES:
- /root/tennis-scorer/src/App.tsx (main component)
- /root/tennis-scorer/src/api.ts (API client)
- /root/tennis-scorer/server/main.py (FastAPI backend)
- /root/tennis-scorer/server/db.py (SQLite setup)

BUGS REPORTED:
1. Player selection dropdowns don't show the selected player - stays blank after selection
2. When clicking to score points, it creates new matches instead of updating existing one

ALREADY FIXED:
- PATCH /api/matches/{mid}/players endpoint added
- court_id made optional in MatchCreate model
- Backend tests pass (players, courts, matches, PATCH all work)

THE FLOW:
1. User goes to HomeScreen → adds players + creates courts
2. User selects a court → CourtScreen shows matches
3. User adds a match (addMatch button) → creates empty match
4. User selects players via dropdowns → calls updateMatchPlayers()
5. updateMatchPlayers calls PATCH /api/matches/{mid}/players → should update player fields
6. loadMatches() called after PATCH → should refresh state with updated data
7. Selects should show selected player names

WHAT I SUSPECT:
- The loadMatches() after PATCH might not be updating state correctly
- Or the match mode (singles/doubles) might not be stored correctly in the match
- Or the onChange handlers are not correctly preserving other player values when updating one

YOUR TASK:
1. Read ALL the code files thoroughly
2. Find the bug(s) causing:
   a) Selects not showing selected player name
   b) Any other issues in player selection flow
3. Fix the bugs
4. Rebuild: cd /root/tennis-scorer && npm run build
5. Restart backend: pkill -f "uvicorn.*8002"; cd /root/tennis-scorer && python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8002

IMPORTANT: Make sure the app works for BOTH singles and doubles modes. The doubles mode should show 4 selects (Dupla 1: P1+P2 | Dupla 2: P1+P2).