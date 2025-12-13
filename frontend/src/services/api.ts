import type { Game, GameDetail, Play, Pattern, PlayerStats, GamesListResponse, PlaysResponse } from '../types';

// API Base URL - Update this with your actual API Gateway URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';

// Helper function for API calls
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Games API
export const gamesAPI = {
  // Get all games for a season
  async getGames(season: number = 2025): Promise<Game[]> {
    const data = await fetchAPI<GamesListResponse>(`/games?season=${season}`);
    
    // Extract games array from response
    if (data && Array.isArray(data.games)) {
      return data.games;
    }
    
    console.error('Unexpected API response format:', data);
    return [];
  },

  // Get single game details with boxscore
  async getGameDetail(gameId: string): Promise<GameDetail> {
    const data = await fetchAPI<GameDetail>(`/games/${gameId}`);
    return data;
  },

  // Get plays for a game
  async getPlays(gameId: string, options?: {
    period?: number;
    scoringOnly?: boolean;
    limit?: number;
  }): Promise<Play[]> {
    const params = new URLSearchParams();
    if (options?.period) params.append('period', options.period.toString());
    if (options?.scoringOnly) params.append('scoring_only', 'true');
    if (options?.limit) params.append('limit', options.limit.toString());
    
    const queryString = params.toString();
    const endpoint = `/games/${gameId}/plays${queryString ? `?${queryString}` : ''}`;
    
    const data = await fetchAPI<PlaysResponse>(endpoint);
    
    // Extract plays array from response
    if (data && Array.isArray(data.plays)) {
      return data.plays;
    }
    
    console.error('Unexpected plays response format:', data);
    return [];
  },
};

// Patterns API
export const patternsAPI = {
  async getPatterns(gameId: string): Promise<Pattern[]> {
    try {
      const data = await fetchAPI<{ patterns: Pattern[] } | Pattern[]>(`/games/${gameId}/patterns`);
      
      if (Array.isArray(data)) {
        return data;
      }
      if (data && 'patterns' in data && Array.isArray(data.patterns)) {
        return data.patterns;
      }
      
      return [];
    } catch (error) {
      console.error('Failed to fetch patterns:', error);
      return [];
    }
  },
};

// Players API (if you add this endpoint)
export const playersAPI = {
  async getPlayerStats(playerId: string, season: number = 2025): Promise<PlayerStats> {
    const data = await fetchAPI<PlayerStats>(`/players/${playerId}?season=${season}`);
    return data;
  },
};

// Export all APIs
export const api = {
  games: gamesAPI,
  patterns: patternsAPI,
  players: playersAPI,
};

export default api;
