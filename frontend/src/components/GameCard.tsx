import { Link } from 'react-router-dom';
import { MapPin, Calendar, ChevronRight, Flame, TrendingUp } from 'lucide-react';
import type { Game } from '../types';

interface GameCardProps {
  game: Game;
}

export function GameCard({ game }: GameCardProps) {
  const isWin = game.iowa_won;
  // Parse short_name format: "NIU @ IOWA" means Iowa is home, "IOWA @ TCU" means Iowa is away
  const isHome = game.short_name.endsWith('IOWA') || game.short_name.includes('@ IOWA');
  const isCompleted = game.status_completed;
  
  // Format date nicely
  const gameDate = new Date(game.date);
  const formattedDate = gameDate.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });

  return (
    <Link to={`/game/${game.game_id}`} className="block">
      <div className="game-card group">
        {/* Result banner */}
        <div className={`
          h-1 w-full
          ${!isCompleted ? 'bg-zinc-600' : isWin ? 'bg-green-500' : 'bg-red-500'}
        `} />

        <div className="p-4">
          {/* Date and location */}
          <div className="flex items-center justify-between text-xs text-zinc-500 mb-3">
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              {formattedDate}
            </div>
            <div className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {isHome ? 'Home' : 'Away'}
            </div>
          </div>

          {/* Matchup */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <p className="text-zinc-400 text-xs uppercase tracking-wider mb-1">
                {isHome ? 'vs' : '@'}
              </p>
              <h3 className="text-lg font-semibold text-white group-hover:text-iowa-gold transition-colors">
                {game.opponent_abbrev}
              </h3>
            </div>

            {/* Score */}
            {isCompleted && (
              <div className="text-right">
                <div className={`
                  font-athletic text-3xl tracking-tight
                  ${isWin ? 'text-white' : 'text-zinc-400'}
                `}>
                  {game.iowa_score}
                </div>
                <div className="text-zinc-500 text-lg font-light">
                  {game.opponent_score}
                </div>
              </div>
            )}
          </div>

          {/* Result badge */}
          <div className="flex items-center justify-between">
            {isCompleted ? (
              <span className={`
                inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-bold uppercase
                ${isWin 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/20'
                }
              `}>
                {isWin ? <TrendingUp className="w-3.5 h-3.5" /> : null}
                {isWin ? 'Win' : 'Loss'}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-bold uppercase bg-zinc-700/50 text-zinc-400 border border-zinc-600/20">
                Upcoming
              </span>
            )}

            <div className="flex items-center gap-1 text-zinc-400 group-hover:text-iowa-gold transition-colors">
              <span className="text-xs">View Details</span>
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

// Compact version for lists
export function GameCardCompact({ game }: GameCardProps) {
  const isWin = game.iowa_won;
  const isHome = game.short_name.endsWith('IOWA') || game.short_name.includes('@ IOWA');
  const isCompleted = game.status_completed;
  
  const gameDate = new Date(game.date);
  const formattedDate = gameDate.toLocaleDateString('en-US', {
    month: 'numeric',
    day: 'numeric',
  });

  return (
    <Link to={`/game/${game.game_id}`}>
      <div className={`
        flex items-center justify-between p-3 rounded-lg
        bg-zinc-900/50 hover:bg-zinc-800 transition-colors
        border-l-2 ${!isCompleted ? 'border-zinc-600' : isWin ? 'border-green-500' : 'border-red-500'}
      `}>
        <div className="flex items-center gap-4">
          <span className="text-zinc-500 text-sm w-12">{formattedDate}</span>
          <span className="text-zinc-400 text-xs">{isHome ? 'vs' : '@'}</span>
          <span className="text-white font-medium">{game.opponent_abbrev}</span>
        </div>
        
        <div className="flex items-center gap-4">
          {isCompleted ? (
            <>
              <span className={`font-mono ${isWin ? 'text-white' : 'text-zinc-400'}`}>
                {game.iowa_score}-{game.opponent_score}
              </span>
              <span className={`
                text-xs font-bold uppercase w-6
                ${isWin ? 'text-green-400' : 'text-red-400'}
              `}>
                {isWin ? 'W' : 'L'}
              </span>
            </>
          ) : (
            <span className="text-xs text-zinc-500 uppercase">Upcoming</span>
          )}
        </div>
      </div>
    </Link>
  );
}
