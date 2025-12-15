import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Users, TrendingUp, Award, ChevronRight, Search } from 'lucide-react';
import { useSeason } from '../contexts/SeasonContext';
import { usePlayers } from '../hooks/useApi';
import { LoadingSpinner, ErrorDisplay } from '../components/LoadingStates';

type SortField = 'points' | 'rebounds' | 'assists' | 'fg_pct' | 'minutes';

export function PlayersPage() {
  const { season, seasonLabel } = useSeason();
  const { data, loading, error } = usePlayers(season);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortField>('points');

  const players = data?.players || [];

  // Filter and sort players
  const filteredPlayers = useMemo(() => {
    let result = [...players];

    // Filter by search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(p => 
        p.player_name.toLowerCase().includes(term) ||
        p.position?.toLowerCase().includes(term) ||
        p.jersey?.includes(term)
      );
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'points':
          return b.points_per_game - a.points_per_game;
        case 'rebounds':
          return b.rebounds_per_game - a.rebounds_per_game;
        case 'assists':
          return b.assists_per_game - a.assists_per_game;
        case 'fg_pct':
          return b.field_goal_pct - a.field_goal_pct;
        case 'minutes':
          return b.minutes_per_game - a.minutes_per_game;
        default:
          return 0;
      }
    });

    return result;
  }, [players, searchTerm, sortBy]);

  // Team totals
  const teamStats = useMemo(() => {
    if (!players.length) return null;
    
    const totalPoints = players.reduce((sum, p) => sum + (p.totals?.points || 0), 0);
    const totalRebounds = players.reduce((sum, p) => sum + (p.totals?.rebounds || 0), 0);
    const totalAssists = players.reduce((sum, p) => sum + (p.totals?.assists || 0), 0);
    
    return { totalPoints, totalRebounds, totalAssists };
  }, [players]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <LoadingSpinner message="Loading player statistics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <ErrorDisplay 
          title="Failed to load players" 
          message="Could not fetch player statistics. Please try again."
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-8 h-8 text-iowa-gold" />
          <h1 className="text-3xl font-athletic text-white">
            IOWA HAWKEYES ROSTER
          </h1>
        </div>
        <p className="text-zinc-400">{seasonLabel} • {players.length} Players</p>
      </div>

      {/* Team Stats Summary */}
      {teamStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <div className="flex items-center gap-2 text-zinc-500 mb-1">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">TOTAL POINTS</span>
            </div>
            <p className="text-2xl font-bold text-iowa-gold">{teamStats.totalPoints.toLocaleString()}</p>
          </div>
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <div className="flex items-center gap-2 text-zinc-500 mb-1">
              <Award className="w-4 h-4" />
              <span className="text-sm">TOTAL REBOUNDS</span>
            </div>
            <p className="text-2xl font-bold text-white">{teamStats.totalRebounds.toLocaleString()}</p>
          </div>
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <div className="flex items-center gap-2 text-zinc-500 mb-1">
              <Award className="w-4 h-4" />
              <span className="text-sm">TOTAL ASSISTS</span>
            </div>
            <p className="text-2xl font-bold text-white">{teamStats.totalAssists.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Search and Sort Controls */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            placeholder="Search players..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg
                       text-white placeholder-zinc-500 focus:border-iowa-gold focus:outline-none"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortField)}
          className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg
                     text-white focus:border-iowa-gold focus:outline-none cursor-pointer"
        >
          <option value="points">Sort by Points</option>
          <option value="rebounds">Sort by Rebounds</option>
          <option value="assists">Sort by Assists</option>
          <option value="fg_pct">Sort by FG%</option>
          <option value="minutes">Sort by Minutes</option>
        </select>
      </div>

      {/* Players Grid */}
      {filteredPlayers.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
          <p className="text-zinc-500">No players found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPlayers.map((player) => (
            <PlayerCard key={player.player_id} player={player} />
          ))}
        </div>
      )}
    </div>
  );
}

interface PlayerCardProps {
  player: {
    player_id: string;
    player_name: string;
    jersey: string;
    position: string;
    games_played: number;
    minutes_per_game: number;
    points_per_game: number;
    rebounds_per_game: number;
    assists_per_game: number;
    field_goal_pct: number;
    three_point_pct: number;
    game_highs: {
      points: number;
      rebounds: number;
      assists: number;
    };
  };
}

function PlayerCard({ player }: PlayerCardProps) {
  return (
    <Link
      to={`/players/${player.player_id}`}
      className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 
                 hover:border-iowa-gold/50 transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Player avatar placeholder */}
          <div className="w-12 h-12 bg-zinc-800 rounded-full flex items-center justify-center
                          text-iowa-gold font-bold text-lg">
            {player.jersey || '?'}
          </div>
          <div>
            <h3 className="font-semibold text-white group-hover:text-iowa-gold transition-colors">
              {player.player_name}
            </h3>
            <p className="text-sm text-zinc-500">
              {player.position || 'N/A'} • #{player.jersey || 'N/A'}
            </p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-iowa-gold transition-colors" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <StatBox label="PPG" value={player.points_per_game} highlight />
        <StatBox label="RPG" value={player.rebounds_per_game} />
        <StatBox label="APG" value={player.assists_per_game} />
        <StatBox label="MPG" value={player.minutes_per_game} />
      </div>

      {/* Shooting */}
      <div className="flex items-center gap-4 text-sm">
        <div>
          <span className="text-zinc-500">FG:</span>
          <span className="text-white ml-1">{player.field_goal_pct}%</span>
        </div>
        <div>
          <span className="text-zinc-500">3PT:</span>
          <span className="text-white ml-1">{player.three_point_pct}%</span>
        </div>
        <div className="ml-auto text-zinc-500">
          {player.games_played} GP
        </div>
      </div>

      {/* Game High */}
      {player.game_highs.points > 0 && (
        <div className="mt-3 pt-3 border-t border-zinc-800">
          <span className="text-xs text-zinc-500">Season High: </span>
          <span className="text-xs text-iowa-gold font-medium">
            {player.game_highs.points} PTS
          </span>
        </div>
      )}
    </Link>
  );
}

function StatBox({ label, value, highlight = false }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className="text-center">
      <p className={`text-lg font-bold ${highlight ? 'text-iowa-gold' : 'text-white'}`}>
        {value}
      </p>
      <p className="text-xs text-zinc-500">{label}</p>
    </div>
  );
}