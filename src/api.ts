const API_BASE = '/api';

let authToken: string | null = null;

export function setToken(t: string) { authToken = t; }
export function getToken() { return authToken; }

async function request(method: string, path: string, body?: unknown) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    authToken = null;
    sessionStorage.removeItem('token');
    window.location.reload();
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  auth: {
    login: (u: string, p: string) => request('POST', '/auth/login', { username: u, password: p }),
    logout: () => request('POST', '/auth/logout'),
    me: () => request('GET', '/auth/me'),
  },
  players: {
    list: () => request('GET', '/players'),
    create: (name: string, seed?: number, photo?: string) => request('POST', '/players', { name, seed, photo }),
    delete: (id: string) => request('DELETE', `/players/${id}`),
  },
  courts: {
    list: () => request('GET', '/courts'),
    create: (name: string) => request('POST', '/courts', { name }),
    delete: (id: string) => request('DELETE', `/courts/${id}`),
    matches: (cid: string) => request('GET', `/courts/${cid}/matches`),
    createMatch: (cid: string, data: any) => request('POST', `/courts/${cid}/matches`, data),
    deleteMatch: (cid: string, mid: string) => request('DELETE', `/courts/${cid}/matches/${mid}`),
  },
  matches: {
    updatePlayers: (mid: string, p1: string | null, p2: string | null, p1b: string | null, p2b: string | null) =>
      request('PATCH', `/matches/${mid}/players`, { player1_id: p1, player2_id: p2, player1b_id: p1b, player2b_id: p2b }),
    scorePoint: (mid: string, winner: 1 | 2) => request('POST', `/matches/${mid}/point`, { match_id: mid, winner }),
    reset: (mid: string) => request('POST', `/matches/${mid}/reset`),
    listPhotos: (mid: string) => request('GET', `/matches/${mid}/photos`),
    addPhoto: (mid: string, photo: string, caption?: string) => request('POST', `/matches/${mid}/photos`, { match_id: mid, photo, caption }),
    deletePhoto: (mid: string, photoid: number) => request('DELETE', `/matches/${mid}/photos/${photoid}`),
  },
};

export function ptLabel(p: number): string {
  const m: Record<number, string> = { 0: '0', 15: '15', 30: '30', 40: '40', 50: 'AD', 60: 'GAME' };
  return m[p] ?? String(p);
}

export function setsWon(sets: { p1: number; p2: number }[], player: 1 | 2): number {
  return sets.filter(s => player === 1 ? s.p1 > s.p2 : s.p2 > s.p1).length;
}