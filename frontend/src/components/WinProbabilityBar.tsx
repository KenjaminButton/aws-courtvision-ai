import React from 'react';

interface WinProbabilityBarProps {
  homeTeam: string;
  awayTeam: string;
  homeProbability: number;
  awayProbability: number;
}

export const WinProbabilityBar: React.FC<WinProbabilityBarProps> = ({
  homeTeam,
  awayTeam,
  homeProbability,
  awayProbability,
}) => {
  // Convert to percentages
  const homePct = Math.round(homeProbability * 100);
  const awayPct = Math.round(awayProbability * 100);

  return (
    <div className="w-full">
      {/* Team Labels */}
      <div className="flex justify-between text-sm font-semibold mb-2">
        <span className="text-blue-600">{homeTeam}</span>
        <span className="text-red-600">{awayTeam}</span>
      </div>

      {/* Probability Bar */}
      <div className="flex h-10 rounded-full overflow-hidden shadow-md">
        {/* Home Team Side */}
        <div
          className="bg-blue-600 flex items-center justify-end pr-3 transition-all duration-700 ease-in-out"
          style={{ width: `${homePct}%` }}
        >
          <span className="text-white text-base font-bold">
            {homePct}%
          </span>
        </div>

        {/* Away Team Side */}
        <div className="bg-red-600 flex items-center pl-3 flex-1 transition-all duration-700 ease-in-out">
          <span className="text-white text-base font-bold">
            {awayPct}%
          </span>
        </div>
      </div>
    </div>
  );
};