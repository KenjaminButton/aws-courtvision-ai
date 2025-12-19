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

// API Pattern format (from get_game_detail Lambda)
export interface APIPattern {
  pattern_type: 'scoring_run' | 'hot_streak';
  team: string;
  team_id: string;
  is_iowa: boolean;
  description: string;
  period: number;
  // Scoring run specific
  points_for?: number;
  points_against?: number;
  start_sequence?: number;
  end_sequence?: number;
  // Hot streak specific
  player_id?: string;
  player_name?: string;
  consecutive_makes?: number;
}

// Game detail types (from /games/{gameId} endpoint)
export interface GameDetail {
  game_id: string;
  date: string;
  season?: number;
  season_type?: string;
  status?: string;
  neutral_site?: boolean;
  conference_competition?: boolean;
  iowa: {
    team_id: string;
    name: string;
    score: string;
    winner: boolean;
    home_away: 'home' | 'away';
    period_scores?: string[];
  };
  opponent: {
    team_id: string;
    name: string;
    score: string;
    winner?: boolean;
    home_away?: 'home' | 'away';
    period_scores?: string[];
  };
  venue?: {
    id?: string;
    name: string;
    city: string;
    state: string;
    attendance?: number;
  };
  boxscore?: BoxScore;
  player_stats?: {
    iowa: PlayerStats[];
    opponent: PlayerStats[];
  };
  play_count?: string;
  // Patterns from the API!
  patterns?: APIPattern[];
  // Media URLs
  reddit_thread_url?: string;
  youtube_highlights_url?: string;
  youtube_postgame_url?: string;
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
  player_id?: string;
  player_name?: string;
  coordinate_x?: number;
  coordinate_y?: number;
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

// Pattern types (for PatternList component display)
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

// Player season types (from /players endpoint)
export interface PlayerSeasonStats {
  player_id: string;
  player_name: string;
  jersey: string;
  position: string;
  games_played: number;
  minutes_per_game: number;
  points_per_game: number;
  rebounds_per_game: number;
  assists_per_game: number;
  steals_per_game: number;
  blocks_per_game: number;
  turnovers_per_game: number;
  fouls_per_game: number;
  field_goal_pct: number;
  three_point_pct: number;
  free_throw_pct: number;
  totals: {
    points: number;
    rebounds: number;
    assists: number;
    steals: number;
    blocks: number;
  };
  game_highs: {
    points: number;
    rebounds: number;
    assists: number;
  };
  game_log: GameLogEntry[];
  bio?: PlayerBio;
}

export interface GameLogEntry {
  game_id: string;
  date: string;
  opponent: string;
  result: 'W' | 'L';
  score: string;
  minutes: number;
  points: number;
  rebounds: number;
  assists: number;
  steals: number;
  blocks: number;
  turnovers: number;
  fouls: number;
  fg: string;
  three_pt: string;
  ft: string;
}

export interface PlayerBio {
  height: string;
  hometown: string;
  high_school: string;
  previous_school?: string;
  class_year: string;
  major?: string;
  bio_summary?: string;
  accolades?: string[];
}

// Players response
export interface PlayersResponse {
  season: string;
  player_count: number;
  players: PlayerSeasonStats[];
}

// AI Summary response (from /games/{gameId}/summary endpoint)
export interface AISummaryResponse {
  summary: string;
  generated_at: string;
  cached: boolean;
}