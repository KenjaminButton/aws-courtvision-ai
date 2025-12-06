import React from 'react';
import { Link } from 'react-router-dom';

interface GameCardProps {
  espnGameId: string;
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  status: string;
}

export const GameCard: React.FC<GameCardProps> = ({
  espnGameId,
  homeTeam,
  awayTeam,
  homeScore,
  awayScore,
  status,
}) => {
  const isLive = status === 'STATUS_IN_PROGRESS' || status === 'STATUS_HALFTIME';
  const isFinal = status === 'STATUS_FINAL';

  return (
    <Link
      to={`/game/${espnGameId}`}
      className="block bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
    >
      {/* Status Badge */}
      <div className="mb-4">
        {isLive && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse"></span>
            LIVE
          </span>
        )}
        {isFinal && (
          <span className="inline-flex px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
            FINAL
          </span>
        )}
        {!isLive && !isFinal && (
          <span className="inline-flex px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            UPCOMING
          </span>
        )}
      </div>

      {/* Teams and Scores */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-gray-900">{awayTeam}</span>
          <span className="text-2xl font-bold text-gray-900">{awayScore}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-gray-900">{homeTeam}</span>
          <span className="text-2xl font-bold text-gray-900">{homeScore}</span>
        </div>
      </div>
    </Link>
  );
};