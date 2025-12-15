import { useState } from 'react';
import type { PlayerStats, BoxScore as BoxScoreType } from '../types';

interface BoxScoreProps {
  boxscore?: BoxScoreType | null;
  highlightIowa?: boolean;
}

export function BoxScore({ boxscore, highlightIowa = true }: BoxScoreProps) {
  const [activeTeam, setActiveTeam] = useState<'home' | 'away'>('home');

  // Handle missing or incomplete boxscore data
  if (!boxscore || !boxscore.homeTeam || !boxscore.awayTeam) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-8 text-center">
        <p className="text-zinc-500">Box score data not available yet.</p>
        <p className="text-zinc-600 text-sm mt-2">
          Player statistics will appear here once the game data is processed.
        </p>
      </div>
    );
  }

  const teams = [
    { key: 'home' as const, data: boxscore.homeTeam },
    { key: 'away' as const, data: boxscore.awayTeam },
  ];

  const isIowaHome = boxscore.homeTeam.name?.toLowerCase().includes('iowa') || false;
  const activeData = activeTeam === 'home' ? boxscore.homeTeam : boxscore.awayTeam;
  const isIowaActive = activeData?.name?.toLowerCase().includes('iowa') || false;

  // Check if we have any player data
  const hasPlayerData = activeData?.players && activeData.players.length > 0;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
      {/* Team tabs */}
      <div className="flex border-b border-zinc-800">
        {teams.map(({ key, data }) => {
          const isIowa = data?.name?.toLowerCase().includes('iowa') || false;
          const isActive = activeTeam === key;
          
          return (
            <button
              key={key}
              onClick={() => setActiveTeam(key)}
              className={`
                flex-1 px-4 py-3 font-semibold text-sm uppercase tracking-wider
                transition-colors relative
                ${isActive 
                  ? isIowa 
                    ? 'text-iowa-gold bg-iowa-gold/10' 
                    : 'text-white bg-zinc-800'
                  : 'text-zinc-500 hover:text-white hover:bg-zinc-800/50'
                }
              `}
            >
              {data?.name || (key === 'home' ? 'Home Team' : 'Away Team')}
              {isActive && (
                <div className={`
                  absolute bottom-0 left-0 right-0 h-0.5
                  ${isIowa ? 'bg-iowa-gold' : 'bg-white'}
                `} />
              )}
            </button>
          );
        })}
      </div>

      {/* Stats table */}
      <div className="overflow-x-auto">
        {hasPlayerData ? (
          <table className="stats-table">
            <thead>
              <tr className={isIowaActive ? 'bg-iowa-gold/5' : 'bg-zinc-800/30'}>
                <th className="sticky left-0 bg-zinc-900 z-10">Player</th>
                <th className="text-center">MIN</th>
                <th className="text-center">PTS</th>
                <th className="text-center">FG</th>
                <th className="text-center">3PT</th>
                <th className="text-center">FT</th>
                <th className="text-center">REB</th>
                <th className="text-center">AST</th>
                <th className="text-center">STL</th>
                <th className="text-center">BLK</th>
                <th className="text-center">TO</th>
                <th className="text-center">PF</th>
              </tr>
            </thead>
            <tbody>
              {activeData.players.map((player, index) => (
                <PlayerRow 
                  key={player.playerId || index} 
                  player={player} 
                  isIowa={isIowaActive}
                />
              ))}
            </tbody>
            {activeData.totals && (
              <tfoot>
                <tr className={`
                  font-semibold
                  ${isIowaActive ? 'bg-iowa-gold/10' : 'bg-zinc-800/50'}
                `}>
                  <td className={`
                    sticky left-0 z-10
                    ${isIowaActive ? 'bg-iowa-gold/10' : 'bg-zinc-800/50'}
                  `}>
                    TOTALS
                  </td>
                  <td className="text-center">-</td>
                  <td className="text-center text-white">{activeData.totals.points}</td>
                  <td className="text-center">
                    {activeData.totals.fieldGoalsMade}-{activeData.totals.fieldGoalsAttempted}
                  </td>
                  <td className="text-center">
                    {activeData.totals.threePointersMade}-{activeData.totals.threePointersAttempted}
                  </td>
                  <td className="text-center">
                    {activeData.totals.freeThrowsMade}-{activeData.totals.freeThrowsAttempted}
                  </td>
                  <td className="text-center">{activeData.totals.rebounds}</td>
                  <td className="text-center">{activeData.totals.assists}</td>
                  <td className="text-center">{activeData.totals.steals}</td>
                  <td className="text-center">{activeData.totals.blocks}</td>
                  <td className="text-center">{activeData.totals.turnovers}</td>
                  <td className="text-center">{activeData.totals.fouls}</td>
                </tr>
              </tfoot>
            )}
          </table>
        ) : (
          <div className="p-8 text-center">
            <p className="text-zinc-500">No player statistics available for {activeData?.name || 'this team'}.</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface PlayerRowProps {
  player: PlayerStats;
  isIowa: boolean;
}

function PlayerRow({ player, isIowa }: PlayerRowProps) {
  const fgPct = player.fieldGoalsAttempted > 0 
    ? ((player.fieldGoalsMade / player.fieldGoalsAttempted) * 100).toFixed(0)
    : '-';
  
  const threePct = player.threePointersAttempted > 0
    ? ((player.threePointersMade / player.threePointersAttempted) * 100).toFixed(0)
    : '-';

  // Highlight high performers
  const isHighScorer = player.points >= 15;
  const isDoubleDouble = (
    (player.points >= 10 ? 1 : 0) +
    (player.rebounds >= 10 ? 1 : 0) +
    (player.assists >= 10 ? 1 : 0)
  ) >= 2;

  return (
    <tr className={`
      ${isHighScorer && isIowa ? 'bg-iowa-gold/5' : ''}
      hover:bg-zinc-800/50
    `}>
      <td className="sticky left-0 bg-zinc-900 z-10">
        <div className="flex items-center gap-2">
          <span className={`
            font-medium
            ${isIowa ? 'text-white' : 'text-zinc-300'}
          `}>
            {player.playerName}
          </span>
          {isDoubleDouble && (
            <span className="text-[10px] bg-iowa-gold/20 text-iowa-gold px-1.5 py-0.5 rounded font-bold">
              DD
            </span>
          )}
        </div>
      </td>
      <td className="text-center text-zinc-500">{player.minutes || '-'}</td>
      <td className={`
        text-center font-semibold
        ${isHighScorer ? (isIowa ? 'text-iowa-gold' : 'text-white') : 'text-zinc-300'}
      `}>
        {player.points}
      </td>
      <td className="text-center text-zinc-400">
        <span className="text-zinc-300">{player.fieldGoalsMade}</span>
        -{player.fieldGoalsAttempted}
        <span className="text-zinc-600 text-xs ml-1">({fgPct}%)</span>
      </td>
      <td className="text-center text-zinc-400">
        <span className="text-zinc-300">{player.threePointersMade}</span>
        -{player.threePointersAttempted}
        <span className="text-zinc-600 text-xs ml-1">({threePct}%)</span>
      </td>
      <td className="text-center text-zinc-400">
        <span className="text-zinc-300">{player.freeThrowsMade}</span>
        -{player.freeThrowsAttempted}
      </td>
      <td className="text-center text-zinc-300">{player.rebounds}</td>
      <td className="text-center text-zinc-300">{player.assists}</td>
      <td className="text-center text-zinc-300">{player.steals}</td>
      <td className="text-center text-zinc-300">{player.blocks}</td>
      <td className="text-center text-zinc-300">{player.turnovers}</td>
      <td className="text-center text-zinc-300">{player.fouls}</td>
    </tr>
  );
}

// Simple stats card for quick view
interface QuickStatsProps {
  label: string;
  value: string | number;
  subvalue?: string;
  highlight?: boolean;
}

export function QuickStats({ label, value, subvalue, highlight }: QuickStatsProps) {
  return (
    <div className={`
      p-4 rounded-lg
      ${highlight ? 'bg-iowa-gold/10 border border-iowa-gold/30' : 'bg-zinc-800/50'}
    `}>
      <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">
        {label}
      </p>
      <p className={`
        text-2xl font-bold
        ${highlight ? 'text-iowa-gold' : 'text-white'}
      `}>
        {value}
      </p>
      {subvalue && (
        <p className="text-xs text-zinc-500 mt-1">{subvalue}</p>
      )}
    </div>
  );
}
