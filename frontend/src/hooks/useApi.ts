import { useState, useEffect, useCallback } from 'react';
import { api, PlayerSeasonStats, PlayersResponse } from '../services/api';
import type { Game, GameDetail, Play } from '../types';

// Generic fetch hook
function useFetch<T>(
  fetchFn: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

// Hook for fetching games list
export function useGames(season: number = 2025) {
  return useFetch<Game[]>(
    () => api.games.getGames(season),
    [season]
  );
}

// Hook for fetching single game detail
export function useGameDetail(gameId: string | undefined) {
  return useFetch<GameDetail | null>(
    async () => {
      if (!gameId) return null;
      return api.games.getGameDetail(gameId);
    },
    [gameId]
  );
}

// Hook for fetching plays
export function usePlays(
  gameId: string | undefined,
  options?: {
    period?: number;
    scoringOnly?: boolean;
    limit?: number;
  }
) {
  return useFetch<Play[]>(
    async () => {
      if (!gameId) return [];
      return api.games.getPlays(gameId, options);
    },
    [gameId, options?.period, options?.scoringOnly, options?.limit]
  );
}

// Hook for fetching players list with season stats
export function usePlayers(season: number = 2026) {
  return useFetch<PlayersResponse>(
    () => api.players.getPlayers(season),
    [season]
  );
}

// Hook for fetching single player detail
export function usePlayerDetail(playerId: string | undefined, season: number = 2026) {
  return useFetch<PlayerSeasonStats | null>(
    async () => {
      if (!playerId) return null;
      return api.players.getPlayerDetail(playerId, season);
    },
    [playerId, season]
  );
}

// Hook for game replay with play-by-play animation
export function useGameReplay(gameId: string | undefined) {
  const { data: plays, loading, error } = usePlays(gameId);
  const [currentPlayIndex, setCurrentPlayIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 1x, 3x, 10x

  const currentPlay = plays?.[currentPlayIndex] || null;
  const progress = plays?.length ? (currentPlayIndex / plays.length) * 100 : 0;

  // Auto-advance plays when playing
  useEffect(() => {
    if (!isPlaying || !plays?.length) return;

    const interval = setInterval(() => {
      setCurrentPlayIndex(prev => {
        if (prev >= plays.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1000 / speed);

    return () => clearInterval(interval);
  }, [isPlaying, plays?.length, speed]);

  const play = () => setIsPlaying(true);
  const pause = () => setIsPlaying(false);
  const reset = () => {
    setCurrentPlayIndex(0);
    setIsPlaying(false);
  };
  const seekTo = (index: number) => setCurrentPlayIndex(index);

  return {
    plays,
    currentPlay,
    currentPlayIndex,
    isPlaying,
    speed,
    progress,
    loading,
    error,
    play,
    pause,
    reset,
    seekTo,
    setSpeed,
  };
}