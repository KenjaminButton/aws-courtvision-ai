// Game types (from /games endpoint)
export interface Game {
  game_id: string;
  date: string;
  short_name: string;
  season_type: string;
  status_completed: boolean;
  iowa_score: string;
  iowa_won: boolean;
  opponent_abbrev: string;
  opponent_score: string;
  tournament_round: string | null;
}

// Games list response
export interface GamesListResponse {
  season: string;
  metadata: {
    season_year: number;
    total_games: number;
    fetched_at: string;
  };
  games: Game[];
  count: number;
}

// Game detail types (from /games/{gameId} endpoint)
export interface GameDetail {
  game_id: string;
  date: string;
  iowa: {
    team_id: string;
    name: string;
    score: string;
    winner: boolean;
    home_away: 'home' | 'away';
  };
  opponent: {
    team_id: string;
    name: string;
    score: string;
  };
  venue: {
    name: string;
    city: string;
    state: string;
  };
  boxscore?: BoxScore;
  player_stats?: {
    iowa: PlayerStats[];
    opponent: PlayerStats[];
  };
  patterns?: Pattern[];
}

// Play types (from /games/{gameId}/plays endpoint)
export interface Play {
  play_id: string;
  sequence: number;
  period: number;
  clock: string;
  team_id: string;
  type: string;
  text: string;
  scoring_play: boolean;
  score_value: number;
  away_score: number;
  home_score: number;
}

// Plays response
export interface PlaysResponse {
  game_id: string;
  plays: Play[];
  count: number;
}

// Player stats types
export interface PlayerStats {
  playerId: string;
  playerName: string;
  team: string;
  points: number;
  fieldGoalsMade: number;
  fieldGoalsAttempted: number;
  threePointersMade: number;
  threePointersAttempted: number;
  freeThrowsMade: number;
  freeThrowsAttempted: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fouls: number;
  minutes?: string;
}

export interface BoxScore {
  homeTeam: {
    name: string;
    players: PlayerStats[];
    totals: PlayerStats;
  };
  awayTeam: {
    name: string;
    players: PlayerStats[];
    totals: PlayerStats;
  };
}

// Pattern types
export interface Pattern {
  PK: string;
  SK: string;
  patternType: 'scoring_run' | 'hot_streak' | 'momentum_shift';
  team: string;
  description: string;
  pointsFor?: number;
  pointsAgainst?: number;
  playerName?: string;
  playerId?: string;
  consecutiveMakes?: number;
  quarter?: number;
  detectedAt: string;
}

// Season types
export interface SeasonSummary {
  season: string;
  wins: number;
  losses: number;
  gamesPlayed: number;
  pointsPerGame: number;
  pointsAllowedPerGame: number;
}

// Player season types
export interface PlayerSeasonStats {
  playerId: string;
  playerName: string;
  team: string;
  season: string;
  gamesPlayed: number;
  totalPoints: number;
  avgPoints: number;
  totalFGMade: number;
  totalFGAttempted: number;
  fgPct: number;
  totalThreeMade: number;
  totalThreeAttempted: number;
  threePct: number;
  totalRebounds: number;
  avgRebounds: number;
  totalAssists: number;
  avgAssists: number;
}

// API Response types (removed duplicates - using types above)
