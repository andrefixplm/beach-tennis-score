Task: Fix Beach Tennis Score Bordon player selection bug

PROBLEM:
When user selects a player from dropdown in CourtScreen, the selected player's name doesn't appear in the dropdown - it stays blank even after selection.

APP INFO:
- Frontend: React + TypeScript + Vite (port 5175)
- Backend: FastAPI + SQLite (port 8002)
- Location: /root/tennis-scorer/
- URL: http://100.118.169.20:5175

FILES TO READ:
1. /root/tennis-scorer/src/App.tsx - Main React component
2. /root/tennis-scorer/src/api.ts - API client
3. /root/tennis-scorer/server/main.py - FastAPI backend

WHAT I KNOW:
- Backend PATCH /api/matches/{mid}/players works correctly (tested via curl)
- updateMatchPlayers was changed to use PATCH response directly instead of loadMatches()
- The select uses value={m.player1?.id ?? ''}

YOUR TASK:
1. Read all three files thoroughly
2. Find why the select doesn't show selected player after selection
3. Fix the bug
4. Run: cd /root/tennis-scorer && npm run build

CRITICAL: After fixing and building, verify the app works by checking the built JS contains the updated code.