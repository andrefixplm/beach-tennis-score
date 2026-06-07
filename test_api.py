#!/usr/bin/env python3
"""
Beach Tênis Score Bordon - API Tests
Tests the backend API for player selection and match management
"""

import requests, json, sys

BASE = "http://100.118.169.20:8002"

def login():
    """Login and return auth token"""
    r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "tennis123"})
    if r.status_code != 200:
        print(f"❌ Login failed: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["token"]
    print(f"✅ Logged in as admin")
    return token

def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def test_players(token):
    """Test player CRUD"""
    print("\n=== PLAYERS ===")
    
    # List players
    r = requests.get(f"{BASE}/api/players", headers=headers(token))
    print(f"GET /api/players → {r.status_code}, {len(r.json())} players")
    
    # Create player
    r = requests.post(f"{BASE}/api/players", headers=headers(token), json={"name": "Ana Test", "seed": 1})
    if r.status_code == 200:
        p1 = r.json()
        print(f"✅ Created player: {p1['id']} - {p1['name']}")
    else:
        print(f"❌ Create player failed: {r.status_code} {r.text}")
        return None
    
    r = requests.post(f"{BASE}/api/players", headers=headers(token), json={"name": "Bia Test", "seed": 2})
    p2 = r.json() if r.status_code == 200 else None
    print(f"✅ Created player: {p2['id']} - {p2['name']}" if p2 else f"❌ Create player 2 failed")
    
    r = requests.post(f"{BASE}/api/players", headers=headers(token), json={"name": "Clara Test", "seed": 3})
    p3 = r.json() if r.status_code == 200 else None
    
    r = requests.post(f"{BASE}/api/players", headers=headers(token), json={"name": "Diana Test", "seed": 4})
    p4 = r.json() if r.status_code == 200 else None
    
    return [p1, p2, p3, p4]

def test_courts(token):
    """Test court CRUD"""
    print("\n=== COURTS ===")
    r = requests.get(f"{BASE}/api/courts", headers=headers(token))
    print(f"GET /api/courts → {r.status_code}, {len(r.json())} courts")
    
    r = requests.post(f"{BASE}/api/courts", headers=headers(token), json={"name": "Quadra Teste"})
    if r.status_code == 200:
        court = r.json()
        print(f"✅ Created court: {court['id']} - {court['name']}")
        return court
    print(f"❌ Create court failed: {r.status_code} {r.text}")
    return None

def test_match_creation(token, court_id, players):
    """Test match creation with players"""
    print("\n=== MATCH CREATION ===")
    
    if len(players) < 4:
        print("⚠️ Not enough players for doubles test")
        return None
    
    # Create doubles match
    r = requests.post(f"{BASE}/api/courts/{court_id}/matches", 
        headers=headers(token),
        json={
            "court_id": court_id,
            "mode": "doubles",
            "sets_to_win": 2,
            "games_per_set": 6,
            "tiebreak_at": 7,
            "tiebreak_win_by": 2,
            "player1_id": players[0]["id"],
            "player2_id": players[2]["id"],
            "player1b_id": players[1]["id"],
            "player2b_id": players[3]["id"]
        })
    
    if r.status_code == 200:
        match = r.json()
        print(f"✅ Created doubles match: {match['id']}")
        print(f"   Player1: {match['player1']}")
        print(f"   Player1b: {match['player1b']}")
        print(f"   Player2: {match['player2']}")
        print(f"   Player2b: {match['player2b']}")
        return match
    else:
        print(f"❌ Create match failed: {r.status_code} {r.text}")
        return None

def test_update_players(token, match_id, players):
    """Test PATCH /api/matches/{mid}/players"""
    print("\n=== UPDATE PLAYERS (PATCH) ===")
    
    # Update only player1
    r = requests.patch(f"{BASE}/api/matches/{match_id}/players",
        headers=headers(token),
        json={
            "player1_id": players[1]["id"],  # Change to different player
            "player2_id": players[2]["id"],
            "player1b_id": players[0]["id"],
            "player2b_id": players[3]["id"]
        })
    
    if r.status_code == 200:
        match = r.json()
        print(f"✅ PATCH /api/matches/{match_id}/players → 200")
        print(f"   Player1 after update: {match['player1']}")
        print(f"   Player1b after update: {match['player1b']}")
        return match
    else:
        print(f"❌ PATCH failed: {r.status_code} {r.text}")
        return None

def test_list_matches(token, court_id, expected_players=None):
    """Test GET /api/courts/{cid}/matches and verify player fields"""
    print("\n=== LIST MATCHES ===")
    
    r = requests.get(f"{BASE}/api/courts/{court_id}/matches", headers=headers(token))
    if r.status_code == 200:
        matches = r.json()
        print(f"✅ GET /api/courts/{court_id}/matches → {len(matches)} matches")
        for m in matches:
            print(f"   Match {m['id']}: status={m['status']}")
            print(f"     player1: {m.get('player1')} (expected: {expected_players[0] if expected_players else '?'})")
            print(f"     player1b: {m.get('player1b')}")
            print(f"     player2: {m.get('player2')}")
            print(f"     player2b: {m.get('player2b')}")
        return matches
    else:
        print(f"❌ List matches failed: {r.status_code} {r.text}")
        return []

def cleanup(token, court_id, match_id, player_ids):
    """Clean up test data"""
    print("\n=== CLEANUP ===")
    if match_id:
        r = requests.delete(f"{BASE}/api/courts/{court_id}/matches/{match_id}", headers=headers(token))
        print(f"DELETE match → {r.status_code}")
    for pid in player_ids:
        r = requests.delete(f"{BASE}/api/players/{pid}", headers=headers(token))
        print(f"DELETE player {pid} → {r.status_code}")
    if court_id:
        r = requests.delete(f"{BASE}/api/courts/{court_id}", headers=headers(token))
        print(f"DELETE court → {r.status_code}")

def main():
    token = login()
    
    # Test players
    players = test_players(token)
    if not players or len(players) < 4:
        print("❌ Not enough players created, aborting")
        return
    
    # Test court
    court = test_courts(token)
    if not court:
        print("❌ Court creation failed, aborting")
        return
    
    # Create match with all 4 players
    match = test_match_creation(token, court["id"], players)
    if not match:
        print("❌ Match creation failed, aborting")
        return
    
    match_id = match["id"]
    
    # Verify list returns correct player data
    test_list_matches(token, court["id"], expected_players=[players[0]["id"]])
    
    # Test PATCH update players
    updated = test_update_players(token, match_id, players)
    if updated:
        # Verify the update persisted
        matches = test_list_matches(token, court["id"])
    
    # Cleanup
    cleanup(token, court["id"], match_id, [p["id"] for p in players])
    
    print("\n✅ All tests completed")

if __name__ == "__main__":
    main()