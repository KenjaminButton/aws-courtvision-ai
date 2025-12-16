import { Flame, TrendingUp, Zap, AlertTriangle } from 'lucide-react';
import type { Pattern } from '../types';

interface PatternBadgeProps {
  pattern: Pattern;
  size?: 'sm' | 'md' | 'lg';
}

export function PatternBadge({ pattern, size = 'md' }: PatternBadgeProps) {
  const { icon: Icon, color, bgColor, borderColor } = getPatternStyle(pattern.patternType);
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <span 
      className={`
        inline-flex items-center gap-2 rounded-full font-semibold
        ${sizeClasses[size]}
        ${bgColor} ${color} border ${borderColor}
      `}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
      {pattern.description}
    </span>
  );
}

function getPatternStyle(type: Pattern['patternType']) {
  switch (type) {
    case 'hot_streak':
      return {
        icon: Flame,
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/30',
      };
    case 'scoring_run':
      return {
        icon: TrendingUp,
        color: 'text-iowa-gold',
        bgColor: 'bg-iowa-gold/10',
        borderColor: 'border-iowa-gold/30',
      };
    case 'momentum_shift':
      return {
        icon: Zap,
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/30',
      };
    default:
      return {
        icon: AlertTriangle,
        color: 'text-zinc-400',
        bgColor: 'bg-zinc-500/10',
        borderColor: 'border-zinc-500/30',
      };
  }
}

interface PatternListProps {
  patterns: Pattern[];
  title?: string;
}

export function PatternList({ patterns, title = 'Detected Patterns' }: PatternListProps) {
  if (patterns.length === 0) return null;

  // Group patterns by type
  const scoringRuns = patterns.filter(p => p.patternType === 'scoring_run');
  const hotStreaks = patterns.filter(p => p.patternType === 'hot_streak');
  const other = patterns.filter(p => !['scoring_run', 'hot_streak'].includes(p.patternType));

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      <div className="border-b border-zinc-800 px-4 py-3">
        <h3 className="font-athletic text-lg text-white tracking-wide">
          {title.toUpperCase()}
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Scoring Runs */}
        {scoringRuns.length > 0 && (
          <div>
            <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-2 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Scoring Runs ({scoringRuns.length})
            </h4>
            <div className="space-y-2">
              {scoringRuns.map((pattern, i) => (
                <PatternCard key={`run-${i}`} pattern={pattern} />
              ))}
            </div>
          </div>
        )}

        {/* Hot Streaks */}
        {hotStreaks.length > 0 && (
          <div>
            <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-2 flex items-center gap-2">
              <Flame className="w-4 h-4" />
              Hot Streaks ({hotStreaks.length})
            </h4>
            <div className="space-y-2">
              {hotStreaks.map((pattern, i) => (
                <PatternCard key={`streak-${i}`} pattern={pattern} />
              ))}
            </div>
          </div>
        )}

        {/* Other patterns */}
        {other.length > 0 && (
          <div>
            <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-2">
              Other Patterns
            </h4>
            <div className="space-y-2">
              {other.map((pattern, i) => (
                <PatternCard key={`other-${i}`} pattern={pattern} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PatternCard({ pattern }: { pattern: Pattern }) {
  const { icon: Icon, color, bgColor, borderColor } = getPatternStyle(pattern.patternType);

  return (
    <div className={`
      p-3 rounded-lg border ${borderColor} ${bgColor}
      flex items-start gap-3
    `}>
      <div className={`p-2 rounded-lg ${bgColor} ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`font-semibold ${color}`}>
          {pattern.description}
        </p>
        <div className="flex items-center gap-3 mt-1 text-xs text-zinc-500">
          <span>{pattern.team}</span>
          {pattern.quarter && <span>Q{pattern.quarter}</span>}
          {pattern.pointsFor !== undefined && (
            <span className="text-green-400">+{pattern.pointsFor} pts</span>
          )}
          {pattern.consecutiveMakes && (
            <span className="text-red-400">{pattern.consecutiveMakes} straight</span>
          )}
        </div>
      </div>
    </div>
  );
}

// Alert component for patterns during replay
export function PatternAlert({ pattern, onDismiss }: { 
  pattern: Pattern; 
  onDismiss: () => void;
}) {
  const { icon: Icon, color } = getPatternStyle(pattern.patternType);

  return (
    <div className={`
      fixed top-24 right-4 z-50 animate-slide-up
      bg-zinc-900 border border-iowa-gold/50 rounded-xl p-4 shadow-xl
      max-w-sm
    `}>
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-iowa-gold/20">
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
        <div className="flex-1">
          <h4 className={`font-bold ${color}`}>Pattern Detected!</h4>
          <p className="text-white text-sm mt-1">{pattern.description}</p>
          <p className="text-zinc-500 text-xs mt-1">{pattern.team}</p>
        </div>
        <button 
          onClick={onDismiss}
          className="text-zinc-500 hover:text-white"
        >
          ×
        </button>
      </div>
    </div>
  );
}
