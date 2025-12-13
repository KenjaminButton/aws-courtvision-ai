import { useState } from 'react';
import { Play, Pause, SkipBack, FastForward, Flame } from 'lucide-react';
import type { Play as PlayType } from '../types';

interface PlayByPlayProps {
  plays: PlayType[];
  currentPlayIndex?: number;
  onPlaySelect?: (index: number) => void;
  isReplayMode?: boolean;
}

export function PlayByPlay({ 
  plays, 
  currentPlayIndex = -1,
  onPlaySelect,
  isReplayMode = false 
}: PlayByPlayProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [scoringOnly, setScoringOnly] = useState(false);

  // Get unique periods
  const periods = [...new Set(plays.map(p => p.period))].sort();

  // Filter plays
  const filteredPlays = plays.filter(play => {
    if (selectedPeriod && play.period !== selectedPeriod) return false;
    if (scoringOnly && !play.scoring_play) return false;
    return true;
  });

  // In replay mode, only show plays up to current index
  const visiblePlays = isReplayMode 
    ? filteredPlays.slice(0, currentPlayIndex + 1)
    : filteredPlays;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Header with filters */}
      <div className="border-b border-zinc-800 p-4">
        <div className="flex items-center justify-between">
          <h3 className="font-athletic text-lg text-white tracking-wide">
            PLAY-BY-PLAY
          </h3>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setScoringOnly(!scoringOnly)}
              className={`
                px-3 py-1.5 rounded text-xs font-medium transition-colors
                ${scoringOnly 
                  ? 'bg-iowa-gold text-iowa-black' 
                  : 'bg-zinc-800 text-zinc-400 hover:text-white'
                }
              `}
            >
              Scoring Only
            </button>
          </div>
        </div>

        {/* Period tabs */}
        <div className="flex items-center gap-1 mt-3 overflow-x-auto">
          <button
            onClick={() => setSelectedPeriod(null)}
            className={`quarter-tab ${!selectedPeriod ? 'quarter-tab-active' : ''}`}
          >
            All
          </button>
          {periods.map(period => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`quarter-tab ${selectedPeriod === period ? 'quarter-tab-active' : ''}`}
            >
              Q{period}
            </button>
          ))}
        </div>
      </div>

      {/* Plays list */}
      <div className="max-h-[500px] overflow-y-auto">
        {visiblePlays.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            No plays to display
          </div>
        ) : (
          visiblePlays.map((play, index) => (
            <PlayItem
              key={`${play.play_id}-${play.sequence}`}
              play={play}
              isActive={isReplayMode && index === currentPlayIndex}
              onClick={() => onPlaySelect?.(plays.indexOf(play))}
            />
          ))
        )}
      </div>

      {/* Play count */}
      <div className="border-t border-zinc-800 px-4 py-2 text-xs text-zinc-500">
        Showing {visiblePlays.length} of {plays.length} plays
      </div>
    </div>
  );
}

interface PlayItemProps {
  play: PlayType;
  isActive?: boolean;
  onClick?: () => void;
}

function PlayItem({ play, isActive, onClick }: PlayItemProps) {
  const isScoringPlay = play.scoring_play;
  
  return (
    <div 
      onClick={onClick}
      className={`
        play-item cursor-pointer
        ${isScoringPlay ? 'play-item-scoring' : ''}
        ${isActive ? 'bg-iowa-gold/10 border-l-2 border-iowa-gold' : ''}
      `}
    >
      {/* Time and period */}
      <div className="flex-shrink-0 w-16 text-center">
        <span className="text-xs text-zinc-500">Q{play.period}</span>
        <p className="font-mono text-sm text-white">{play.clock}</p>
      </div>

      {/* Score */}
      <div className="flex-shrink-0 w-16 text-center">
        <p className={`
          font-mono text-sm
          ${isScoringPlay ? 'text-iowa-gold font-bold' : 'text-zinc-400'}
        `}>
          {play.away_score}-{play.home_score}
        </p>
      </div>

      {/* Description */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">
          {play.text}
        </p>
        <p className="text-xs text-zinc-500">{play.type}</p>
      </div>

      {/* Scoring indicator */}
      {isScoringPlay && (
        <div className="flex-shrink-0">
          <span className="inline-flex items-center gap-1 text-iowa-gold text-xs font-bold">
            <Flame className="w-3.5 h-3.5" />
            +{play.score_value}
          </span>
        </div>
      )}
    </div>
  );
}

// Replay controls component
interface ReplayControlsProps {
  isPlaying: boolean;
  speed: number;
  progress: number;
  onPlay: () => void;
  onPause: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
}

export function ReplayControls({
  isPlaying,
  speed,
  progress,
  onPlay,
  onPause,
  onReset,
  onSpeedChange,
}: ReplayControlsProps) {
  const speeds = [1, 3, 10];

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
      <div className="flex items-center justify-between gap-4">
        {/* Play controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onReset}
            className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors"
            title="Reset"
          >
            <SkipBack className="w-5 h-5 text-white" />
          </button>
          
          <button
            onClick={isPlaying ? onPause : onPlay}
            className="p-3 rounded-full bg-iowa-gold hover:bg-iowa-gold-light transition-colors"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <Pause className="w-6 h-6 text-iowa-black" />
            ) : (
              <Play className="w-6 h-6 text-iowa-black" />
            )}
          </button>
        </div>

        {/* Progress bar */}
        <div className="flex-1">
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-iowa-gold transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Speed controls */}
        <div className="flex items-center gap-1">
          <FastForward className="w-4 h-4 text-zinc-500 mr-1" />
          {speeds.map(s => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              className={`
                px-2 py-1 rounded text-xs font-mono transition-colors
                ${speed === s 
                  ? 'bg-iowa-gold text-iowa-black' 
                  : 'bg-zinc-800 text-zinc-400 hover:text-white'
                }
              `}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
