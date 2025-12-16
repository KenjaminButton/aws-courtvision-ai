import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { Play } from '../types';

interface ScoreFlowChartProps {
  plays: Play[];
  homeTeam: string;
  awayTeam: string;
  isIowaHome: boolean;
}

interface ChartDataPoint {
  playIndex: number;
  homeScore: number;
  awayScore: number;
  period: number;
  clock: string;
  text: string;
}

export function ScoreFlowChart({ plays, homeTeam, awayTeam, isIowaHome }: ScoreFlowChartProps) {
  // Transform plays into chart data
  const { chartData, periodMarkers, maxScore } = useMemo(() => {
    if (!plays.length) return { chartData: [], periodMarkers: [], maxScore: 0 };

    // Sort plays by period first, then by sequence within each period
    const sortedPlays = [...plays].sort((a, b) => {
      const periodA = a.period || 1;
      const periodB = b.period || 1;
      if (periodA !== periodB) return periodA - periodB;
      
      const seqA = parseInt(String(a.sequence)) || 0;
      const seqB = parseInt(String(b.sequence)) || 0;
      return seqA - seqB;
    });

    const data: ChartDataPoint[] = [];
    const markers: { playIndex: number; period: number }[] = [];
    let currentPeriod = 0;
    let maxScoreVal = 0;

    // Add starting point
    data.push({
      playIndex: 0,
      homeScore: 0,
      awayScore: 0,
      period: 1,
      clock: '10:00',
      text: 'Game Start',
    });

    sortedPlays.forEach((play, index) => {
      const homeScore = play.home_score || 0;
      const awayScore = play.away_score || 0;
      const period = play.period || 1;

      // Track period changes for reference lines
      if (period !== currentPeriod) {
        markers.push({ playIndex: index + 1, period });
        currentPeriod = period;
      }

      // Track max score for Y-axis
      maxScoreVal = Math.max(maxScoreVal, homeScore, awayScore);

      data.push({
        playIndex: index + 1,
        homeScore,
        awayScore,
        period,
        clock: play.clock || '',
        text: play.text || '',
      });
    });

    return { chartData: data, periodMarkers: markers, maxScore: maxScoreVal };
  }, [plays]);

  if (chartData.length <= 1) {
    return (
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-iowa-gold" />
          Score Flow
        </h3>
        <div className="h-64 flex items-center justify-center text-zinc-500">
          No play data available
        </div>
      </div>
    );
  }

  // Format period label (Q1-Q4, then OT, 2OT, etc.)
  const formatPeriodLabel = (period: number): string => {
    if (period <= 4) return `Q${period}`;
    if (period === 5) return 'OT';
    return `${period - 4}OT`;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ChartDataPoint;
      return (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-3 shadow-xl">
          <p className="text-xs text-zinc-400 mb-1">
            {formatPeriodLabel(data.period)} • {data.clock}
          </p>
          <div className="flex items-center gap-4 mb-2">
            <div>
              <span className={`font-bold ${isIowaHome ? 'text-iowa-gold' : 'text-white'}`}>
                {homeTeam}: {data.homeScore}
              </span>
            </div>
            <div>
              <span className={`font-bold ${!isIowaHome ? 'text-iowa-gold' : 'text-white'}`}>
                {awayTeam}: {data.awayScore}
              </span>
            </div>
          </div>
          <p className="text-xs text-zinc-300 max-w-[250px] truncate">
            {data.text}
          </p>
        </div>
      );
    }
    return null;
  };

  // Determine which period markers to show labels for (avoid clutter)
  // Show labels for: Q1, Q3, and any OT periods
  const shouldShowLabel = (period: number, totalPeriods: number): boolean => {
    if (totalPeriods <= 4) return true; // Normal game, show all
    if (period === 1 || period === 3) return true; // Always show Q1 and Q3
    if (period > 4) return true; // Always show OT periods
    return false;
  };

  const totalPeriods = periodMarkers.length > 0 
    ? Math.max(...periodMarkers.map(m => m.period)) 
    : 4;

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-iowa-gold" />
        Score Flow
      </h3>
      
      {/* Legend */}
      <div className="flex items-center gap-6 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isIowaHome ? 'bg-iowa-gold' : 'bg-zinc-400'}`} />
          <span className={isIowaHome ? 'text-iowa-gold' : 'text-zinc-400'}>{homeTeam}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${!isIowaHome ? 'bg-iowa-gold' : 'bg-zinc-400'}`} />
          <span className={!isIowaHome ? 'text-iowa-gold' : 'text-zinc-400'}>{awayTeam}</span>
        </div>
        {totalPeriods > 4 && (
          <span className="text-xs text-zinc-500 ml-auto">
            {totalPeriods - 4}x Overtime
          </span>
        )}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 10, left: -10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis
              dataKey="playIndex"
              tick={false}
              axisLine={{ stroke: '#444' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, Math.ceil((maxScore + 10) / 10) * 10]}
              tick={{ fill: '#888', fontSize: 12 }}
              axisLine={{ stroke: '#444' }}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Period reference lines - skip the first one (Q1 starts at 0) */}
            {periodMarkers.slice(1).map((marker) => (
              <ReferenceLine
                key={`period-${marker.period}-${marker.playIndex}`}
                x={marker.playIndex}
                stroke="#555"
                strokeDasharray="5 5"
                label={
                  shouldShowLabel(marker.period, totalPeriods)
                    ? {
                        value: formatPeriodLabel(marker.period),
                        position: 'top',
                        fill: marker.period > 4 ? '#FFCD00' : '#666',
                        fontSize: 10,
                        fontWeight: marker.period > 4 ? 'bold' : 'normal',
                      }
                    : undefined
                }
              />
            ))}

            {/* Home team line */}
            <Line
              type="stepAfter"
              dataKey="homeScore"
              stroke={isIowaHome ? '#FFCD00' : '#888'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: isIowaHome ? '#FFCD00' : '#888' }}
            />
            
            {/* Away team line */}
            <Line
              type="stepAfter"
              dataKey="awayScore"
              stroke={!isIowaHome ? '#FFCD00' : '#888'}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: !isIowaHome ? '#FFCD00' : '#888' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Final score indicator */}
      {chartData.length > 1 && (
        <div className="mt-4 pt-4 border-t border-zinc-800 flex justify-between text-sm">
          <span className="text-zinc-500">Final Score</span>
          <div className="flex items-center gap-2">
            <span className={`font-bold ${isIowaHome ? 'text-iowa-gold' : 'text-white'}`}>
              {homeTeam} {chartData[chartData.length - 1].homeScore}
            </span>
            <span className="text-zinc-600">-</span>
            <span className={`font-bold ${!isIowaHome ? 'text-iowa-gold' : 'text-white'}`}>
              {chartData[chartData.length - 1].awayScore} {awayTeam}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}