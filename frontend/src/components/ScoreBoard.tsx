import type { GameDetail } from '../types';

interface ScoreBoardProps {
  game: GameDetail;
  animated?: boolean;
}

export function ScoreBoard({ game, animated = false }: ScoreBoardProps) {
  const iowaScore = parseInt(game.iowa.score) || 0;
  const opponentScore = parseInt(game.opponent.score) || 0;
  const isWin = game.iowa.winner;
  const isIowaHome = game.iowa.home_away === 'home';

  // Check if venue has actual data (not just empty object)
  const hasVenue = game.venue?.name || game.venue?.city || game.venue?.state;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-iowa-gold/20 via-iowa-gold/10 to-iowa-gold/20 px-6 py-3 border-b border-zinc-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-iowa-gold font-medium">
            Final
          </span>
          <span className="text-zinc-400">
            {new Date(game.date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>
      </div>

      {/* Score Display */}
      <div className="p-6">
        <div className="flex items-center justify-center gap-8 md:gap-16">
          {/* Iowa */}
          <div className="text-center flex-1">
            <div className="mb-2">
              <span className="inline-block w-8 h-8 bg-iowa-gold rounded-full mb-2" />
            </div>
            <h3 className="font-athletic text-xl text-white mb-1">IOWA</h3>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Hawkeyes</p>
            <div className={`
              score-display mt-4
              ${animated ? 'animate-score-pop' : ''}
              ${isWin ? 'text-iowa-gold' : 'text-white'}
            `}>
              {iowaScore}
            </div>
          </div>

          {/* VS Divider */}
          <div className="flex flex-col items-center">
            <div className="w-px h-16 bg-zinc-700" />
            <span className="text-zinc-600 text-sm font-medium py-2">VS</span>
            <div className="w-px h-16 bg-zinc-700" />
          </div>

          {/* Opponent */}
          <div className="text-center flex-1">
            <div className="mb-2">
              <span className="inline-block w-8 h-8 bg-zinc-600 rounded-full mb-2" />
            </div>
            <h3 className="font-athletic text-xl text-white mb-1">
              {game.opponent.name?.toUpperCase() || 'OPPONENT'}
            </h3>
            <p className="text-xs text-zinc-500 uppercase tracking-wider">
              {isIowaHome ? 'Away' : 'Home'}
            </p>
            <div className={`
              score-display mt-4
              ${!isWin ? 'text-white' : 'text-zinc-400'}
            `}>
              {opponentScore}
            </div>
          </div>
        </div>

        {/* Result Badge */}
        <div className="flex justify-center mt-6">
          <span className={`
            inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold uppercase
            ${isWin 
              ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
              : 'bg-red-500/10 text-red-400 border border-red-500/20'
            }
          `}>
            {isWin ? '🎉 Victory' : 'Defeat'}
          </span>
        </div>
      </div>

      {/* Venue Info - Only show if venue has actual data */}
      {hasVenue && (
        <div className="border-t border-zinc-800 px-6 py-4">
          <div className="text-center text-sm text-zinc-400">
            📍 {[game.venue.name, game.venue.city, game.venue.state].filter(Boolean).join(', ')}
          </div>
        </div>
      )}
    </div>
  );
}

// Live score component for replay
interface LiveScoreProps {
  homeScore: number;
  awayScore: number;
  homeTeam: string;
  awayTeam: string;
  period: number;
  clock: string;
}

export function LiveScore({ homeScore, awayScore, homeTeam, awayTeam, period, clock }: LiveScoreProps) {
  return (
    <div className="bg-iowa-black border border-iowa-gold/30 rounded-lg p-4">
      <div className="flex items-center justify-between text-sm text-iowa-gold mb-3">
        <span className="uppercase tracking-wider">Q{period}</span>
        <span className="font-mono">{clock}</span>
      </div>
      
      <div className="flex items-center justify-between gap-4">
        <div className="text-center flex-1">
          <p className="text-xs text-zinc-400 mb-1">{awayTeam}</p>
          <p className="font-athletic text-3xl text-white">{awayScore}</p>
        </div>
        
        <div className="text-zinc-600 text-lg">-</div>
        
        <div className="text-center flex-1">
          <p className="text-xs text-zinc-400 mb-1">{homeTeam}</p>
          <p className="font-athletic text-3xl text-white">{homeScore}</p>
        </div>
      </div>
    </div>
  );
}