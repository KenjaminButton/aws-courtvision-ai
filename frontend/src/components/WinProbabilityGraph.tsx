import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

interface WinProbabilityGraphProps {
  espnGameId: string;
}

interface HistoryPoint {
  timestamp: string;
  homeWinProbability: number;
  awayWinProbability: number;
  homeScore: number;
  awayScore: number;
  quarter: number;
}

export const WinProbabilityGraph: React.FC<WinProbabilityGraphProps> = ({ espnGameId }) => {
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL;
        const response = await fetch(`${apiUrl}/game/${espnGameId}/win-probability`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch win probability history');
        }
        
        const data = await response.json();
        setHistory(data.history);
        setLoading(false);
      } catch (err) {
        console.error('❌ Error fetching win prob history:', err);
        setLoading(false);
      }
    };

    if (espnGameId) {
      fetchHistory();
    }
  }, [espnGameId]);

  if (loading) {
    return (
      <div className="text-gray-400 text-center py-8">
        Loading probability timeline...
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-gray-400 text-center py-8">
        No historical data available yet
      </div>
    );
  }

  // Format data for Recharts (add index for X-axis)
  const chartData = history.map((point, index) => ({
    index: index + 1,
    homePct: (point.homeWinProbability * 100).toFixed(1),
    awayPct: (point.awayWinProbability * 100).toFixed(1),
    score: `${point.homeScore}-${point.awayScore}`,
    quarter: `Q${point.quarter}`,
  }));

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold text-cv-teal mb-4">Win Probability Timeline</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="index" 
            stroke="#94a3b8"
            label={{ value: 'Game Progression', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
          />
          <YAxis 
            stroke="#94a3b8"
            domain={[0, 100]}
            label={{ value: 'Win Probability (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Legend />
          <ReferenceLine y={50} stroke="#64748b" strokeDasharray="5 5" />
          <Line 
            type="monotone" 
            dataKey="homePct" 
            stroke="#3b82f6" 
            strokeWidth={3}
            name="Home Win %"
            dot={false}
          />
          <Line 
            type="monotone" 
            dataKey="awayPct" 
            stroke="#ef4444" 
            strokeWidth={3}
            name="Away Win %"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-500 text-center mt-2">
        {history.length} probability calculations during game
      </p>
    </div>
  );
};