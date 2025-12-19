import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Target, Award, Calendar, User, GraduationCap, MapPin, Trophy } from 'lucide-react';
import { useSeason } from '../contexts/SeasonContext';
import { usePlayerDetail } from '../hooks/useApi';
import { LoadingSpinner, ErrorDisplay } from '../components/LoadingStates';

type TabType = 'overview' | 'gamelog' | 'splits';

export function PlayerDetailPage() {
  const { playerId } = useParams<{ playerId: string }>();
  const { season, seasonLabel } = useSeason();
  const { data: player, loading, error } = usePlayerDetail(playerId, season);
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <LoadingSpinner message="Loading player data..." />
      </div>
    );
  }

  if (error || !player) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <ErrorDisplay 
          title="Player not found" 
          message="Could not find this player's statistics."
        />
      </div>
    );
  }

  const tabs = [
    { key: 'overview' as TabType, label: 'Overview' },
    { key: 'gamelog' as TabType, label: 'Game Log' },
    { key: 'splits' as TabType, label: 'Splits' },
  ];

  // Build the player info line with bio data
  const infoItems = [
    player.jersey ? `#${player.jersey}` : null,
    player.position,
    player.bio?.height,
    player.bio?.class_year,
  ].filter(Boolean);

  const locationItems = [
    player.bio?.hometown,
    player.bio?.high_school ? `${player.bio.high_school} HS` : null,
  ].filter(Boolean);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back navigation */}
      <Link 
        to="/players"
        className="inline-flex items-center gap-2 text-zinc-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Players
      </Link>

      {/* Player Header */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center gap-6">
          {/* Player Avatar */}
          <div className="w-24 h-24 rounded-full overflow-hidden bg-zinc-800 shrink-0">
            <img 
              src={`https://a.espncdn.com/i/headshots/womens-college-basketball/players/full/${player.player_id}.png`}
              alt={player.player_name}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement!.innerHTML = `<span class="flex items-center justify-center w-full h-full text-iowa-gold font-bold text-3xl">${player.jersey || '?'}</span>`;
              }}
            />
          </div>

          {/* Player Info */}
          <div className="flex-1">
            <h1 className="text-3xl font-athletic text-white mb-1">
              {player.player_name}
            </h1>
            
            {/* Primary info line: Jersey, Position, Height, Class */}
            <p className="text-zinc-400 mb-1">
              {infoItems.join(' • ')} • Iowa Hawkeyes
            </p>
            
            {/* Location line: Hometown, High School */}
            {locationItems.length > 0 && (
              <p className="text-zinc-500 text-sm mb-2 flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {locationItems.join(' • ')}
              </p>
            )}
            
            {/* Transfer badge */}
            {player.bio?.previous_school && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-900/30 text-blue-400 text-xs rounded-full">
                Transfer from {player.bio.previous_school}
              </span>
            )}
            
            <p className="text-sm text-zinc-500 mt-2">{seasonLabel}</p>
          </div>

          {/* Key Stats */}
          <div className="flex gap-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-iowa-gold">{player.points_per_game}</p>
              <p className="text-xs text-zinc-500 uppercase">PPG</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{player.rebounds_per_game}</p>
              <p className="text-xs text-zinc-500 uppercase">RPG</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{player.assists_per_game}</p>
              <p className="text-xs text-zinc-500 uppercase">APG</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-zinc-800 mb-6">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`
              px-4 py-3 text-sm font-medium transition-colors relative
              ${activeTab === key 
                ? 'text-iowa-gold' 
                : 'text-zinc-500 hover:text-white'
              }
            `}
          >
            {label}
            {activeTab === key && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-iowa-gold" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab player={player} />}
      {activeTab === 'gamelog' && <GameLogTab player={player} />}
      {activeTab === 'splits' && <SplitsTab player={player} />}
    </div>
  );
}

function OverviewTab({ player }: { player: any }) {
  const hasBio = player.bio?.bio_summary || (player.bio?.accolades?.length > 0);

  return (
    <div className="space-y-6">
      {/* Bio Section - Full width at top if bio exists */}
      {hasBio && (
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <User className="w-5 h-5 text-iowa-gold" />
            About
          </h3>
          
          {/* Bio Summary */}
          {player.bio?.bio_summary && (
            <p className="text-zinc-300 leading-relaxed mb-4">
              {player.bio.bio_summary}
            </p>
          )}
          
          {/* Quick Facts */}
          <div className="flex flex-wrap gap-4 mb-4 text-sm">
            {player.bio?.major && (
              <div className="flex items-center gap-2 text-zinc-400">
                <GraduationCap className="w-4 h-4 text-iowa-gold" />
                <span>{player.bio.major}</span>
              </div>
            )}
            {player.bio?.high_school && (
              <div className="flex items-center gap-2 text-zinc-400">
                <MapPin className="w-4 h-4 text-zinc-500" />
                <span>{player.bio.high_school} ({player.bio.hometown})</span>
              </div>
            )}
          </div>
          
          {/* Accolades */}
          {player.bio?.accolades?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-2">
                <Trophy className="w-4 h-4 text-iowa-gold" />
                Accolades
              </h4>
              <div className="flex flex-wrap gap-2">
                {player.bio.accolades.map((accolade: string, index: number) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-iowa-gold/10 text-iowa-gold text-xs rounded-full border border-iowa-gold/20"
                  >
                    {accolade}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Season Averages */}
        <div className="lg:col-span-2 bg-zinc-900 rounded-xl border border-zinc-800 p-6">
          <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-iowa-gold" />
            Season Averages
          </h3>
          
          <div className="grid grid-cols-4 sm:grid-cols-5 gap-4">
            <StatDisplay label="PPG" value={player.points_per_game} highlight />
            <StatDisplay label="RPG" value={player.rebounds_per_game} />
            <StatDisplay label="APG" value={player.assists_per_game} />
            <StatDisplay label="SPG" value={player.steals_per_game} />
            <StatDisplay label="BPG" value={player.blocks_per_game} />
            <StatDisplay label="MPG" value={player.minutes_per_game} />
            <StatDisplay label="FG%" value={`${player.field_goal_pct}%`} />
            <StatDisplay label="3P%" value={`${player.three_point_pct}%`} />
            <StatDisplay label="FT%" value={`${player.free_throw_pct}%`} />
            <StatDisplay label="TO" value={player.turnovers_per_game} />
          </div>
        </div>

        {/* Season Totals & Highs */}
        <div className="space-y-6">
          {/* Games Played */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-iowa-gold" />
              Games Played
            </h3>
            <p className="text-4xl font-bold text-white">{player.games_played}</p>
          </div>

          {/* Season Highs */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-iowa-gold" />
              Season Highs
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Points</span>
                <span className="text-xl font-bold text-iowa-gold">
                  {player.game_highs?.points || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Rebounds</span>
                <span className="text-xl font-bold text-white">
                  {player.game_highs?.rebounds || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Assists</span>
                <span className="text-xl font-bold text-white">
                  {player.game_highs?.assists || 0}
                </span>
              </div>
            </div>
          </div>

          {/* Season Totals */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-iowa-gold" />
              Season Totals
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">Total Points</span>
                <span className="text-white font-medium">{player.totals?.points || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Total Rebounds</span>
                <span className="text-white font-medium">{player.totals?.rebounds || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Total Assists</span>
                <span className="text-white font-medium">{player.totals?.assists || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Total Steals</span>
                <span className="text-white font-medium">{player.totals?.steals || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Total Blocks</span>
                <span className="text-white font-medium">{player.totals?.blocks || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function GameLogTab({ player }: { player: any }) {
  const gameLog = player.game_log || [];

  if (gameLog.length === 0) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-8 text-center">
        <Calendar className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <p className="text-zinc-500">No games played yet</p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-zinc-800 text-zinc-400 uppercase text-xs">
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Opponent</th>
              <th className="px-4 py-3 text-center">Result</th>
              <th className="px-4 py-3 text-center">MIN</th>
              <th className="px-4 py-3 text-center">PTS</th>
              <th className="px-4 py-3 text-center">REB</th>
              <th className="px-4 py-3 text-center">AST</th>
              <th className="px-4 py-3 text-center">STL</th>
              <th className="px-4 py-3 text-center">BLK</th>
              <th className="px-4 py-3 text-center">FG</th>
              <th className="px-4 py-3 text-center">3PT</th>
              <th className="px-4 py-3 text-center">FT</th>
            </tr>
          </thead>
          <tbody>
            {gameLog.map((game: any, index: number) => (
              <tr key={index} className="border-t border-zinc-800 hover:bg-zinc-800/50">
                <td className="px-4 py-3 text-zinc-400">
                  {new Date(game.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </td>
                <td className="px-4 py-3 text-white font-medium">
                  vs {game.opponent}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`font-medium ${game.result === 'W' ? 'text-green-500' : 'text-red-500'}`}>
                    {game.result}
                  </span>
                  <span className="text-zinc-500 text-xs ml-1">({game.score})</span>
                </td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.minutes}</td>
                <td className={`px-4 py-3 text-center font-semibold ${game.points >= 20 ? 'text-iowa-gold' : 'text-white'}`}>
                  {game.points}
                </td>
                <td className="px-4 py-3 text-center text-zinc-300">{game.rebounds}</td>
                <td className="px-4 py-3 text-center text-zinc-300">{game.assists}</td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.steals}</td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.blocks}</td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.fg}</td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.three_pt}</td>
                <td className="px-4 py-3 text-center text-zinc-400">{game.ft}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Replace the SplitsTab function in PlayerDetailPage.tsx (around line 380-389)
// with this implementation:

function SplitsTab({ player }: { player: any }) {
  const splits = player.splits;
  
  // Check if splits data exists
  if (!splits) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-8 text-center">
        <Target className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <p className="text-zinc-500">No splits data available</p>
      </div>
    );
  }

  const splitRows = [
    { label: 'Home', icon: '🏠', data: splits.home },
    { label: 'Away', icon: '✈️', data: splits.away },
    { label: 'Conference', icon: '🏆', data: splits.conference },
    { label: 'Non-Conference', icon: '📋', data: splits.non_conference },
  ];

  // Filter out splits with no games
  const activeSplits = splitRows.filter(row => row.data?.games > 0);

  if (activeSplits.length === 0) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-8 text-center">
        <Target className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <p className="text-zinc-500">No games played yet</p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-zinc-800 text-zinc-400 uppercase text-xs">
              <th className="px-4 py-3 text-left">Split</th>
              <th className="px-4 py-3 text-center">GP</th>
              <th className="px-4 py-3 text-center">MPG</th>
              <th className="px-4 py-3 text-center">PPG</th>
              <th className="px-4 py-3 text-center">RPG</th>
              <th className="px-4 py-3 text-center">APG</th>
              <th className="px-4 py-3 text-center">SPG</th>
              <th className="px-4 py-3 text-center">BPG</th>
              <th className="px-4 py-3 text-center">FG%</th>
              <th className="px-4 py-3 text-center">3P%</th>
              <th className="px-4 py-3 text-center">FT%</th>
            </tr>
          </thead>
          <tbody>
            {/* Overall row */}
            <tr className="border-t border-zinc-800 bg-zinc-800/30">
              <td className="px-4 py-3 text-white font-semibold">
                📊 Overall
              </td>
              <td className="px-4 py-3 text-center text-white">{player.games_played}</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.minutes_per_game}</td>
              <td className="px-4 py-3 text-center text-iowa-gold font-semibold">{player.points_per_game}</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.rebounds_per_game}</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.assists_per_game}</td>
              <td className="px-4 py-3 text-center text-zinc-400">{player.steals_per_game}</td>
              <td className="px-4 py-3 text-center text-zinc-400">{player.blocks_per_game}</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.field_goal_pct}%</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.three_point_pct}%</td>
              <td className="px-4 py-3 text-center text-zinc-300">{player.free_throw_pct}%</td>
            </tr>
            
            {/* Individual splits */}
            {activeSplits.map(({ label, icon, data }) => {
              // Highlight if better than overall
              const ppgBetter = data.ppg > player.points_per_game;
              const fgBetter = data.fg_pct > player.field_goal_pct;
              
              return (
                <tr key={label} className="border-t border-zinc-800 hover:bg-zinc-800/50">
                  <td className="px-4 py-3 text-white font-medium">
                    {icon} {label}
                  </td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.games}</td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.mpg}</td>
                  <td className={`px-4 py-3 text-center font-semibold ${ppgBetter ? 'text-green-400' : 'text-zinc-300'}`}>
                    {data.ppg}
                  </td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.rpg}</td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.apg}</td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.spg}</td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.bpg}</td>
                  <td className={`px-4 py-3 text-center ${fgBetter ? 'text-green-400' : 'text-zinc-400'}`}>
                    {data.fg_pct}%
                  </td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.three_pct}%</td>
                  <td className="px-4 py-3 text-center text-zinc-400">{data.ft_pct}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {/* Legend */}
      <div className="px-4 py-3 border-t border-zinc-800 text-xs text-zinc-500">
        <span className="text-green-400">●</span> Better than season average
      </div>
    </div>
  );
}

function StatDisplay({ label, value, highlight = false }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
      <p className={`text-xl font-bold ${highlight ? 'text-iowa-gold' : 'text-white'}`}>
        {value}
      </p>
      <p className="text-xs text-zinc-500 uppercase">{label}</p>
    </div>
  );
}