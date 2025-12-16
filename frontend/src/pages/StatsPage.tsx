import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Flame, 
  Trophy, 
  Target,
  Home,
  Plane,
  Users,
  Calendar,
  ArrowUp,
  ArrowDown,
  Minus,
} from 'lucide-react';
import { useSeason } from '../contexts/SeasonContext';
import { useSeasonStats } from '../hooks/useApi';
import { LoadingSpinner } from '../components/LoadingStates';

export function StatsPage() {
  const { season } = useSeason();
  const { data: stats, loading, error } = useSeasonStats(season);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <h1 className="font-athletic text-4xl text-white mb-4">SEASON STATS</h1>
        <p className="text-red-400">Failed to load season stats</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="font-athletic text-4xl text-white mb-2">SEASON STATS</h1>
        <p className="text-zinc-500">
          {season === 2026 ? '2025-26' : '2024-25'} Season • {stats.games_played} Games Played
        </p>
      </div>

      {/* Hero Stats */}
      <HeroStats stats={stats} />

      {/* Scoring Trend Chart */}
      <ScoringTrendChart games={stats.games} />

      {/* Splits Table */}
      <SplitsTable splits={stats.splits} />

      {/* Game Results Grid */}
      <GameResultsGrid games={stats.games} />

      {/* Pattern Insights */}
      <PatternInsights patterns={stats.patterns} />
    </div>
  );
}

// Hero Stats Cards
function HeroStats({ stats }: { stats: SeasonStats }) {
  const { record, streak, scoring } = stats;
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {/* Record */}
      <StatCard
        label="Record"
        value={`${record.wins}-${record.losses}`}
        subValue={`${(record.pct * 100).toFixed(1)}%`}
        icon={Trophy}
        color="iowa-gold"
      />
      
      {/* Streak */}
      <StatCard
        label="Streak"
        value={streak.type ? `${streak.type}${streak.count}` : '-'}
        subValue={streak.type === 'W' ? 'Winning' : streak.type === 'L' ? 'Losing' : ''}
        icon={streak.type === 'W' ? TrendingUp : TrendingDown}
        color={streak.type === 'W' ? 'green-400' : 'red-400'}
      />
      
      {/* PPG */}
      <StatCard
        label="Points/Game"
        value={scoring.ppg.toFixed(1)}
        subValue={`#1 offense?`}
        icon={Target}
        color="iowa-gold"
      />
      
      {/* Opp PPG */}
      <StatCard
        label="Opp PPG"
        value={scoring.opp_ppg.toFixed(1)}
        subValue="Allowed"
        icon={Target}
        color="zinc-400"
      />
      
      {/* Margin */}
      <StatCard
        label="Avg Margin"
        value={`${scoring.margin > 0 ? '+' : ''}${scoring.margin.toFixed(1)}`}
        subValue="Per game"
        icon={scoring.margin > 0 ? ArrowUp : ArrowDown}
        color={scoring.margin > 0 ? 'green-400' : 'red-400'}
      />
      
      {/* High Game */}
      <StatCard
        label="High Game"
        value={scoring.high_game?.points.toString() || '-'}
        subValue={`vs ${scoring.high_game?.opponent || ''}`}
        icon={Flame}
        color="orange-400"
      />
    </div>
  );
}

function StatCard({ 
  label, 
  value, 
  subValue, 
  icon: Icon, 
  color 
}: { 
  label: string; 
  value: string; 
  subValue?: string; 
  icon: React.ElementType; 
  color: string;
}) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 text-${color}`} />
        <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className={`text-2xl font-bold text-${color}`}>{value}</p>
      {subValue && <p className="text-xs text-zinc-500 mt-1">{subValue}</p>}
    </div>
  );
}

// Scoring Trend Line Chart
function ScoringTrendChart({ games }: { games: GameResult[] }) {
  const chartData = useMemo(() => {
    return games.map((game, index) => ({
      game: index + 1,
      opponent: game.opponent,
      iowa: game.iowa_score,
      opponent_score: game.opp_score,
      won: game.won,
      date: game.date,
    }));
  }, [games]);

  if (chartData.length === 0) return null;

  const avgIowa = games.reduce((sum, g) => sum + g.iowa_score, 0) / games.length;
  const avgOpp = games.reduce((sum, g) => sum + g.opp_score, 0) / games.length;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-iowa-gold" />
        Scoring Trend
      </h3>
      
      <div className="flex items-center gap-6 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-iowa-gold" />
          <span className="text-iowa-gold">Iowa ({avgIowa.toFixed(1)} avg)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-zinc-500" />
          <span className="text-zinc-400">Opponents ({avgOpp.toFixed(1)} avg)</span>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="game" 
              tick={{ fill: '#888', fontSize: 12 }}
              axisLine={{ stroke: '#444' }}
            />
            <YAxis 
              domain={[30, 'auto']}
              tick={{ fill: '#888', fontSize: 12 }}
              axisLine={{ stroke: '#444' }}
            />
            <Tooltip content={<TrendTooltip />} />
            <ReferenceLine y={avgIowa} stroke="#FFCD00" strokeDasharray="5 5" opacity={0.5} />
            <ReferenceLine y={avgOpp} stroke="#888" strokeDasharray="5 5" opacity={0.5} />
            <Line 
              type="monotone" 
              dataKey="iowa" 
              stroke="#FFCD00" 
              strokeWidth={2}
              dot={{ fill: '#FFCD00', r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="opponent_score" 
              stroke="#888" 
              strokeWidth={2}
              dot={{ fill: '#888', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function TrendTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  
  const data = payload[0].payload;
  return (
    <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-3 shadow-xl">
      <p className="text-xs text-zinc-400 mb-1">Game {data.game} vs {data.opponent}</p>
      <div className="flex items-center gap-4">
        <span className="text-iowa-gold font-bold">Iowa: {data.iowa}</span>
        <span className="text-zinc-400">Opp: {data.opponent_score}</span>
      </div>
      <p className={`text-xs mt-1 ${data.won ? 'text-green-400' : 'text-red-400'}`}>
        {data.won ? 'Win' : 'Loss'} ({data.won ? '+' : ''}{data.iowa - data.opponent_score})
      </p>
    </div>
  );
}

// Splits Table
function SplitsTable({ splits }: { splits: SeasonStats['splits'] }) {
  const splitData = [
    { name: 'Home', icon: Home, ...splits.home },
    { name: 'Away', icon: Plane, ...splits.away },
    { name: 'Conference', icon: Users, ...splits.conference },
    { name: 'Non-Conference', icon: Calendar, ...splits.non_conference },
  ];

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="border-b border-zinc-800 px-4 py-3">
        <h3 className="font-athletic text-lg text-white tracking-wide">SPLITS</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-500 text-xs uppercase">
              <th className="text-left px-4 py-3">Split</th>
              <th className="text-center px-4 py-3">W</th>
              <th className="text-center px-4 py-3">L</th>
              <th className="text-center px-4 py-3">Win%</th>
              <th className="text-center px-4 py-3">PPG</th>
              <th className="text-center px-4 py-3">Opp PPG</th>
              <th className="text-center px-4 py-3">Margin</th>
            </tr>
          </thead>
          <tbody>
            {splitData.map((split) => (
              <tr key={split.name} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <split.icon className="w-4 h-4 text-zinc-500" />
                    <span className="text-white font-medium">{split.name}</span>
                  </div>
                </td>
                <td className="text-center px-4 py-3 text-green-400">{split.wins}</td>
                <td className="text-center px-4 py-3 text-red-400">{split.losses}</td>
                <td className="text-center px-4 py-3 text-white">
                  {(split.win_pct * 100).toFixed(0)}%
                </td>
                <td className="text-center px-4 py-3 text-iowa-gold">{split.ppg}</td>
                <td className="text-center px-4 py-3 text-zinc-400">{split.opp_ppg}</td>
                <td className={`text-center px-4 py-3 ${split.margin > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {split.margin > 0 ? '+' : ''}{split.margin}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Game Results Grid
function GameResultsGrid({ games }: { games: GameResult[] }) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="border-b border-zinc-800 px-4 py-3">
        <h3 className="font-athletic text-lg text-white tracking-wide">GAME RESULTS</h3>
      </div>
      
      <div className="p-4">
        <div className="grid grid-cols-6 md:grid-cols-11 gap-2">
          {games.map((game, index) => (
            <Link
              key={game.game_id}
              to={`/game/${game.game_id}`}
              className={`
                aspect-square rounded-lg flex flex-col items-center justify-center
                text-xs font-medium transition-transform hover:scale-110
                ${game.won 
                  ? 'bg-green-500/20 border border-green-500/30 text-green-400' 
                  : 'bg-red-500/20 border border-red-500/30 text-red-400'
                }
              `}
              title={`${game.won ? 'W' : 'L'} vs ${game.opponent}: ${game.iowa_score}-${game.opp_score}`}
            >
              <span className="font-bold">{game.won ? 'W' : 'L'}</span>
              <span className="text-[10px] opacity-70">{game.opponent}</span>
            </Link>
          ))}
        </div>
        
        <div className="flex items-center gap-4 mt-4 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-500/20 border border-green-500/30" />
            <span>Win</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500/20 border border-red-500/30" />
            <span>Loss</span>
          </div>
          <span className="ml-auto">Click a game for details</span>
        </div>
      </div>
    </div>
  );
}

// Pattern Insights
function PatternInsights({ patterns }: { patterns: SeasonStats['patterns'] }) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="border-b border-zinc-800 px-4 py-3">
        <h3 className="font-athletic text-lg text-white tracking-wide">
          AI PATTERN INSIGHTS
        </h3>
      </div>
      
      <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Scoring Runs */}
        <div className="bg-zinc-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-iowa-gold" />
            <span className="text-xs text-zinc-500 uppercase">Scoring Runs</span>
          </div>
          <p className="text-2xl font-bold text-white">{patterns.total_scoring_runs}</p>
          <p className="text-xs text-zinc-500 mt-1">
            <span className="text-iowa-gold">{patterns.iowa_runs} Iowa</span>
            {' • '}
            <span className="text-zinc-400">{patterns.opponent_runs} Opp</span>
          </p>
        </div>
        
        {/* Hot Streaks */}
        <div className="bg-zinc-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Flame className="w-4 h-4 text-red-400" />
            <span className="text-xs text-zinc-500 uppercase">Hot Streaks</span>
          </div>
          <p className="text-2xl font-bold text-white">{patterns.total_hot_streaks}</p>
          <p className="text-xs text-zinc-500 mt-1">
            <span className="text-red-400">{patterns.iowa_hot_streaks} Iowa</span>
            {' • '}
            {patterns.total_hot_streaks - patterns.iowa_hot_streaks} Opp
          </p>
        </div>
        
        {/* Hottest Player */}
        {patterns.hottest_player && (
          <div className="bg-zinc-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-4 h-4 text-orange-400" />
              <span className="text-xs text-zinc-500 uppercase">Hottest Player</span>
            </div>
            <p className="text-lg font-bold text-white truncate">
              {patterns.hottest_player.name}
            </p>
            <p className="text-xs text-orange-400 mt-1">
              {patterns.hottest_player.count} hot streaks
            </p>
          </div>
        )}
        
        {/* Best Quarter */}
        {patterns.best_quarter_for_runs && (
          <div className="bg-zinc-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-green-400" />
              <span className="text-xs text-zinc-500 uppercase">Best Quarter</span>
            </div>
            <p className="text-2xl font-bold text-white">
              Q{patterns.best_quarter_for_runs.quarter}
            </p>
            <p className="text-xs text-green-400 mt-1">
              {patterns.best_quarter_for_runs.count} scoring runs
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// Types
interface SeasonStats {
  season: string;
  games_played: number;
  record: {
    wins: number;
    losses: number;
    pct: number;
  };
  streak: {
    type: 'W' | 'L' | null;
    count: number;
  };
  scoring: {
    ppg: number;
    opp_ppg: number;
    margin: number;
    total_points: number;
    total_opp_points: number;
    high_game: {
      points: number;
      opponent: string;
      game_id: string;
      date: string;
    } | null;
    low_game: {
      points: number;
      opponent: string;
      game_id: string;
      date: string;
    } | null;
  };
  splits: {
    home: SplitData;
    away: SplitData;
    conference: SplitData;
    non_conference: SplitData;
  };
  games: GameResult[];
  patterns: PatternInsightsData;
}

interface SplitData {
  wins: number;
  losses: number;
  games: number;
  iowa_points: number;
  opp_points: number;
  ppg: number;
  opp_ppg: number;
  margin: number;
  win_pct: number;
}

interface GameResult {
  game_id: string;
  date: string;
  opponent: string;
  iowa_score: number;
  opp_score: number;
  won: boolean;
  home: boolean;
  conference: boolean;
}

interface PatternInsightsData {
  total_scoring_runs: number;
  iowa_runs: number;
  opponent_runs: number;
  total_hot_streaks: number;
  iowa_hot_streaks: number;
  hottest_player: {
    player_id: string;
    name: string;
    count: number;
  } | null;
  best_quarter_for_runs: {
    quarter: number;
    count: number;
  } | null;
}