import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Play as PlayIcon, BarChart2, Flame, Clock } from 'lucide-react';
import { useGameDetail, usePlays, useGameReplay } from '../hooks/useApi';
import { ScoreBoard, LiveScore } from '../components/ScoreBoard';
import { PlayByPlay, ReplayControls } from '../components/PlayByPlay';
import { PatternList } from '../components/PatternBadge';
import { BoxScore } from '../components/BoxScore';
import { ScoreFlowChart } from '../components/ScoreFlowChart';
import { LoadingSpinner, ErrorDisplay } from '../components/LoadingStates';
import type { GameDetail, Play, Pattern } from '../types';

type TabType = 'overview' | 'plays' | 'replay' | 'stats';

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  
  const { data: game, loading: gameLoading, error: gameError } = useGameDetail(gameId);
  const { data: plays, loading: playsLoading } = usePlays(gameId);

  const tabs: { key: TabType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { key: 'overview', label: 'Overview', icon: BarChart2 },
    { key: 'plays', label: 'Play-by-Play', icon: Clock },
    { key: 'replay', label: 'Replay', icon: PlayIcon },
    { key: 'stats', label: 'Box Score', icon: Flame },
  ];

  if (gameLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <LoadingSpinner message="Loading game data..." />
      </div>
    );
  }

  if (gameError || !game) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <ErrorDisplay
          title="Game not found"
          message="We couldn't find this game. It may have been moved or deleted."
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back navigation */}
      <Link 
        to="/"
        className="inline-flex items-center gap-2 text-zinc-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Games
      </Link>

      {/* Score header */}
      <div className="mb-8">
        <ScoreBoard game={game} />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-zinc-800 mb-6 overflow-x-auto">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`
              flex items-center gap-2 px-4 py-3 text-sm font-medium
              transition-colors relative whitespace-nowrap
              ${activeTab === key 
                ? 'text-iowa-gold' 
                : 'text-zinc-500 hover:text-white'
              }
            `}
          >
            <Icon className="w-4 h-4" />
            {label}
            {activeTab === key && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-iowa-gold" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <OverviewTab game={game} plays={plays || []} playsLoading={playsLoading} />
        )}
        {activeTab === 'plays' && (
          <PlaysTab plays={plays || []} loading={playsLoading} />
        )}
        {activeTab === 'replay' && (
          <ReplayTab gameId={gameId!} game={game} />
        )}
        {activeTab === 'stats' && (
          <StatsTab game={game} />
        )}
      </div>
    </div>
  );
}

// Overview tab showing score flow, patterns, and key stats
function OverviewTab({ game, plays, playsLoading }: { game: GameDetail; plays: Play[]; playsLoading: boolean }) {
  // Use real patterns from the API! (no more mock data)
  // Transform API pattern format to what PatternList expects
  const patterns: Pattern[] = (game.patterns || []).map((p, index) => ({
    PK: game.game_id,
    SK: `PATTERN#${p.pattern_type}#${index}`,
    patternType: p.pattern_type as 'scoring_run' | 'hot_streak' | 'momentum_shift',
    team: p.team,
    description: p.description,
    pointsFor: p.points_for,
    pointsAgainst: p.points_against,
    playerName: p.player_name,
    playerId: p.player_id,
    consecutiveMakes: p.consecutive_makes,
    quarter: p.period,
    detectedAt: new Date().toISOString(),
  }));

  // Calculate quick stats from plays
  const scoringPlays = plays.filter(p => p.scoring_play);
  const iowaScoring = scoringPlays.filter(p => p.team_id === game.iowa.team_id);

  // Determine team names for chart
  const isIowaHome = game.iowa.home_away === 'home';
  const homeTeam = isIowaHome ? game.iowa.name : game.opponent.name;
  const awayTeam = isIowaHome ? game.opponent.name : game.iowa.name;
  
  return (
    <div className="space-y-6">
      {/* Score Flow Chart - Full Width */}
      {playsLoading ? (
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
          <div className="h-64 flex items-center justify-center">
            <LoadingSpinner message="Loading score data..." />
          </div>
        </div>
      ) : (
        <ScoreFlowChart
          plays={plays}
          homeTeam={homeTeam}
          awayTeam={awayTeam}
          isIowaHome={isIowaHome}
        />
      )}

      {/* Patterns and Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patterns */}
        <div className="lg:col-span-2">
          <PatternList patterns={patterns} />
        </div>

        {/* Quick stats sidebar */}
        <div className="space-y-4">
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <h3 className="font-semibold text-white mb-4">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Total Plays</span>
                <span className="text-white font-mono">{plays.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Scoring Plays</span>
                <span className="text-white font-mono">{scoringPlays.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Iowa Scoring</span>
                <span className="text-iowa-gold font-mono">{iowaScoring.length}</span>
              </div>
            </div>
          </div>

          {/* Game info */}
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <h3 className="font-semibold text-white mb-4">Game Info</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Date</span>
                <span className="text-white">
                  {new Date(game.date).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Location</span>
                <span className="text-white">
                  {game.iowa.home_away === 'home' ? 'Home' : 'Away'}
                </span>
              </div>
              {game.venue && (
                <div className="flex justify-between items-center">
                  <span className="text-zinc-400">Venue</span>
                  <span className="text-white">{game.venue.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Plays tab with full play-by-play
function PlaysTab({ plays, loading }: { plays: Play[]; loading: boolean }) {
  if (loading) {
    return <LoadingSpinner message="Loading plays..." />;
  }

  return <PlayByPlay plays={plays} />;
}

// Replay tab with interactive replay
function ReplayTab({ gameId, game }: { gameId: string; game: GameDetail }) {
  const {
    plays,
    currentPlay,
    currentPlayIndex,
    isPlaying,
    speed,
    progress,
    loading,
    play,
    pause,
    reset,
    setSpeed,
  } = useGameReplay(gameId);

  // Determine team names based on home/away
  const homeTeam = game.iowa.home_away === 'home' ? game.iowa.name : game.opponent.name;
  const awayTeam = game.iowa.home_away === 'away' ? game.iowa.name : game.opponent.name;

  if (loading) {
    return <LoadingSpinner message="Loading replay data..." />;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Live score and controls */}
      <div className="lg:col-span-1 space-y-4">
        {currentPlay && (
          <LiveScore
            homeScore={currentPlay.home_score}
            awayScore={currentPlay.away_score}
            homeTeam={homeTeam}
            awayTeam={awayTeam}
            period={currentPlay.period}
            clock={currentPlay.clock}
          />
        )}

        <ReplayControls
          isPlaying={isPlaying}
          speed={speed}
          progress={progress}
          onPlay={play}
          onPause={pause}
          onReset={reset}
          onSpeedChange={setSpeed}
        />

        {/* Current play info */}
        {currentPlay && (
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <h4 className="text-sm text-zinc-500 uppercase tracking-wider mb-2">
              Current Play
            </h4>
            <p className="text-white">
              {currentPlay.text}
            </p>
            {currentPlay.scoring_play && (
              <span className="inline-flex items-center gap-1 mt-2 text-iowa-gold text-sm font-bold">
                <Flame className="w-4 h-4" />
                +{currentPlay.score_value} PTS
              </span>
            )}
          </div>
        )}
      </div>

      {/* Play-by-play list */}
      <div className="lg:col-span-2">
        <PlayByPlay
          plays={plays || []}
          currentPlayIndex={currentPlayIndex}
          isReplayMode={true}
        />
      </div>
    </div>
  );
}

// Stats tab with box score
function StatsTab({ game }: { game: GameDetail }) {
  // Handle incomplete game data
  if (!game?.iowa || !game?.opponent) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-8 text-center">
        <p className="text-zinc-500">Game data is still loading...</p>
      </div>
    );
  }

  // Transform API player stats to BoxScore format
  const transformPlayer = (p: any) => {
    // Parse "5-10" format into made/attempted
    const parseShotStat = (stat: string) => {
      if (!stat || stat === '--') return { made: 0, attempted: 0 };
      const [made, attempted] = stat.split('-').map(Number);
      return { made: made || 0, attempted: attempted || 0 };
    };

    const fg = parseShotStat(p['fieldgoalsmade-fieldgoalsattempted'] || p.field_goals);
    const threes = parseShotStat(p['threepointfieldgoalsmade-threepointfieldgoalsattempted'] || p.three_pointers);
    const ft = parseShotStat(p['freethrowsmade-freethrowsattempted'] || p.free_throws);

    return {
      playerId: p.player_id || p.playerId || '',
      playerName: p.name || p.player_name || p.playerName || 'Unknown',
      minutes: p.minutes || '0',
      points: parseInt(p.points) || 0,
      fieldGoalsMade: fg.made,
      fieldGoalsAttempted: fg.attempted,
      threePointersMade: threes.made,
      threePointersAttempted: threes.attempted,
      freeThrowsMade: ft.made,
      freeThrowsAttempted: ft.attempted,
      rebounds: parseInt(p.rebounds) || 0,
      assists: parseInt(p.assists) || 0,
      steals: parseInt(p.steals) || 0,
      blocks: parseInt(p.blocks) || 0,
      turnovers: parseInt(p.turnovers) || 0,
      fouls: parseInt(p.fouls) || 0,
    };
  };

  // Get and transform player stats
  const iowaStats = (game.player_stats?.iowa || []).map(transformPlayer);
  const opponentStats = (game.player_stats?.opponent || []).map(transformPlayer);

  // Calculate totals
  const calculateTotals = (players: any[], teamName: string) => {
    const totals = players.reduce((acc, p) => ({
      points: acc.points + p.points,
      fieldGoalsMade: acc.fieldGoalsMade + p.fieldGoalsMade,
      fieldGoalsAttempted: acc.fieldGoalsAttempted + p.fieldGoalsAttempted,
      threePointersMade: acc.threePointersMade + p.threePointersMade,
      threePointersAttempted: acc.threePointersAttempted + p.threePointersAttempted,
      freeThrowsMade: acc.freeThrowsMade + p.freeThrowsMade,
      freeThrowsAttempted: acc.freeThrowsAttempted + p.freeThrowsAttempted,
      rebounds: acc.rebounds + p.rebounds,
      assists: acc.assists + p.assists,
      steals: acc.steals + p.steals,
      blocks: acc.blocks + p.blocks,
      turnovers: acc.turnovers + p.turnovers,
      fouls: acc.fouls + p.fouls,
    }), {
      points: 0, fieldGoalsMade: 0, fieldGoalsAttempted: 0,
      threePointersMade: 0, threePointersAttempted: 0,
      freeThrowsMade: 0, freeThrowsAttempted: 0,
      rebounds: 0, assists: 0, steals: 0, blocks: 0, turnovers: 0, fouls: 0,
    });

    return {
      playerId: 'totals',
      playerName: 'TOTALS',
      team: teamName,
      ...totals,
    };
  };

  const isIowaHome = game.iowa.home_away === 'home';

  const boxscore = {
    homeTeam: {
      name: isIowaHome ? game.iowa.name : game.opponent.name,
      players: isIowaHome ? iowaStats : opponentStats,
      totals: calculateTotals(
        isIowaHome ? iowaStats : opponentStats,
        isIowaHome ? game.iowa.name : game.opponent.name
      ),
    },
    awayTeam: {
      name: !isIowaHome ? game.iowa.name : game.opponent.name,
      players: !isIowaHome ? iowaStats : opponentStats,
      totals: calculateTotals(
        !isIowaHome ? iowaStats : opponentStats,
        !isIowaHome ? game.iowa.name : game.opponent.name
      ),
    },
  };

  return (
    <BoxScore 
      boxscore={boxscore} 
      highlightIowa={true} 
    />
  );
}