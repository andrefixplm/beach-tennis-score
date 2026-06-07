export type Player = {
  id: string;
  name: string;
  seed?: number;
};

export type MatchConfig = {
  mode: 'singles' | 'doubles';
  setsToWin: number;
  gamesPerSet: number;
  tiebreakAt: number;
  tiebreakWinBy: number;
};

export type Match = {
  id: string;
  player1: Player | null;
  player2: Player | null;
  player1b?: Player | null; // doubles partner 1
  player2b?: Player | null; // doubles partner 2
  score: { p1: number; p2: number }[];
  currentGame: { p1: number; p2: number };
  server: 1 | 2;
  status: 'pending' | 'live' | 'complete';
  winner: 1 | 2 | null;
  config: MatchConfig;
};

export type Court = {
  id: string;
  name: string;
  matches: Match[];
};