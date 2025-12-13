import { useMemo, useState } from 'react';
import { Calendar, Trophy, TrendingUp, Filter } from 'lucide-react';
import { useGames } from '../hooks/useApi';
import { GameCard, GameCardCompact } from '../components/GameCard';
import { LoadingSpinner, LoadingSkeleton, ErrorDisplay, EmptyState } from '../components/LoadingStates';
import type { Game } from '../types';

export function HomePage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterResult, setFilterResult] = useState<'all' | 'W' | 'L'>('all');
  const { data: games, loading, error, refetch } = useGames(2025);

  // Calculate season stats
  const seasonStats = useMemo(() => {
    if (!games?.length) return null;
    
    // Only count completed games
    const completedGames = games.filter(g => g.status_completed);
    const wins = completedGames.filter(g => g.iowa_won).length;
    const losses = completedGames.filter(g => !g.iowa_won).length;
    const totalPoints = completedGames.reduce((sum, g) => sum + (parseInt(g.iowa_score) || 0), 0);
    const avgPoints = completedGames.length ? (totalPoints / completedGames.length).toFixed(1) : '0.0';

    return { wins, losses, avgPoints, gamesPlayed: completedGames.length };
  }, [games]);

  // Filter games
  const filteredGames = useMemo(() => {
    if (!games) return [];
    if (filterResult === 'all') return games;
    
    // Filter by win/loss
    if (filterResult === 'W') return games.filter(g => g.iowa_won);
    if (filterResult === 'L') return games.filter(g => g.status_completed && !g.iowa_won);
    return games;
  }, [games, filterResult]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <ErrorDisplay
          message="Failed to load games. Please try again."
          onRetry={refetch}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Hero section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-2 h-8 bg-iowa-gold rounded-full" />
          <h1 className="font-athletic text-4xl md:text-5xl text-white tracking-wide">
            2024-25 SEASON
          </h1>
        </div>
        <p className="text-zinc-400 text-lg">
          Iowa Hawkeyes Women's Basketball
        </p>
      </div>

      {/* Season stats cards */}
      {seasonStats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 md:p-6">
            <div className="flex items-center gap-3 mb-2">
              <Trophy className="w-5 h-5 text-iowa-gold" />
              <span className="text-sm text-zinc-500 uppercase tracking-wider">Record</span>
            </div>
            <p className="font-athletic text-3xl md:text-4xl text-white">
              <span className="text-green-400">{seasonStats.wins}</span>
              <span className="text-zinc-600 mx-2">-</span>
              <span className="text-red-400">{seasonStats.losses}</span>
            </p>
          </div>

          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 md:p-6">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-iowa-gold" />
              <span className="text-sm text-zinc-500 uppercase tracking-wider">PPG</span>
            </div>
            <p className="font-athletic text-3xl md:text-4xl text-iowa-gold">
              {seasonStats.avgPoints}
            </p>
          </div>

          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 md:p-6">
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="w-5 h-5 text-iowa-gold" />
              <span className="text-sm text-zinc-500 uppercase tracking-wider">Games</span>
            </div>
            <p className="font-athletic text-3xl md:text-4xl text-white">
              {games?.length || 0}
            </p>
          </div>
        </div>
      )}

      {/* Filters and view toggle */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-zinc-500" />
          <div className="flex rounded-lg overflow-hidden border border-zinc-700">
            {(['all', 'W', 'L'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setFilterResult(filter)}
                className={`
                  px-3 py-1.5 text-xs font-medium uppercase transition-colors
                  ${filterResult === filter
                    ? 'bg-iowa-gold text-iowa-black'
                    : 'bg-zinc-900 text-zinc-400 hover:text-white'
                  }
                `}
              >
                {filter === 'all' ? 'All' : filter === 'W' ? 'Wins' : 'Losses'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex rounded-lg overflow-hidden border border-zinc-700">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1.5 ${viewMode === 'grid' ? 'bg-zinc-700' : 'bg-zinc-900'}`}
            title="Grid view"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 ${viewMode === 'list' ? 'bg-zinc-700' : 'bg-zinc-900'}`}
            title="List view"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Games display */}
      {filteredGames.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No games found"
          message={filterResult !== 'all' 
            ? `No ${filterResult === 'W' ? 'wins' : 'losses'} to display.`
            : 'No games have been loaded yet.'
          }
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredGames.map((game) => (
            <GameCard key={game.game_id} game={game} />
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredGames.map((game) => (
            <GameCardCompact key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </div>
  );
}
