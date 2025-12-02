import React from 'react';

interface LiveScoreProps {
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  quarter?: string | null;
  gameClock?: string;
  status?: string;
  isConnected: boolean;
}

const LiveScore: React.FC<LiveScoreProps> = ({
  homeTeam,
  awayTeam,
  homeScore,
  awayScore,
  quarter,
  gameClock,
  status,
  isConnected,
}) => {
  return (
    <div className="bg-cv-navy border-2 border-cv-blue rounded-lg p-6 shadow-lg">
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-400">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
        {quarter && (
          <span className="text-sm text-cv-teal font-semibold">
            Q{quarter} {gameClock && `• ${gameClock}`}
          </span>
        )}
      </div>

      {/* Score Display */}
      <div className="grid grid-cols-3 gap-4 items-center">
        {/* Away Team */}
        <div className="text-right">
          <p className="text-sm text-gray-400 mb-1">Away</p>
          <p className="text-2xl font-bold text-white truncate">{awayTeam}</p>
        </div>

        {/* Scores */}
        <div className="flex items-center justify-center gap-4">
          <div className="text-center">
            <p className="text-4xl font-bold text-cv-teal">{awayScore}</p>
          </div>
          <div className="text-2xl text-gray-600">-</div>
          <div className="text-center">
            <p className="text-4xl font-bold text-cv-teal">{homeScore}</p>
          </div>
        </div>

        {/* Home Team */}
        <div className="text-left">
          <p className="text-sm text-gray-400 mb-1">Home</p>
          <p className="text-2xl font-bold text-white truncate">{homeTeam}</p>
        </div>
      </div>

      {/* Status */}
      {status && (
        <div className="mt-4 text-center">
          <span className="text-xs text-gray-500 uppercase tracking-wide">{status}</span>
        </div>
      )}
    </div>
  );
};

export default LiveScore;