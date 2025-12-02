import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import LiveScore from '../components/LiveScore';

const GameView: React.FC = () => {
  const { espnGameId } = useParams<{ espnGameId: string }>();
  const [fullGameId, setFullGameId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  
  const { gameState, isConnected, error: wsError } = useWebSocket(fullGameId);

  // Fetch game data from REST API
  useEffect(() => {
    if (!espnGameId) return;

    const fetchGameData = async () => {
      try {
        setLoading(true);
        const apiUrl = process.env.REACT_APP_API_URL;
        const response = await fetch(`${apiUrl}/game/${espnGameId}`);
        
        if (!response.ok) {
          throw new Error(`Game not found: ${espnGameId}`);
        }
        
        const data = await response.json();
        console.log('📡 Game data from API:', data);
        
        // Set the full gameId for WebSocket subscription
        setFullGameId(data.gameId);
        setLoading(false);
      } catch (err) {
        console.error('❌ API Error:', err);
        setApiError(err instanceof Error ? err.message : 'Failed to load game');
        setLoading(false);
      }
    };

    fetchGameData();
  }, [espnGameId]);

  return (
    <div className="min-h-screen bg-cv-navy text-white">
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-cv-teal mb-8">Live Game</h1>

        {/* API Error State */}
        {apiError && (
          <div className="bg-red-900 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">❌ {apiError}</p>
          </div>
        )}

        {/* WebSocket Error State */}
        {wsError && !apiError && (
          <div className="bg-red-900 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">❌ {wsError}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && !apiError && (
          <div className="bg-cv-navy border border-cv-blue rounded-lg p-8 text-center">
            <div className="animate-pulse">
              <div className="w-3 h-3 bg-cv-teal rounded-full mx-auto mb-4"></div>
              <p className="text-gray-400">Loading game data...</p>
            </div>
          </div>
        )}

        {/* Live Score */}
        {gameState && !loading && (
          <LiveScore
            homeTeam={gameState.homeTeam || 'Home'}
            awayTeam={gameState.awayTeam || 'Away'}
            homeScore={gameState.homeScore || 0}
            awayScore={gameState.awayScore || 0}
            quarter={gameState.quarter}
            gameClock={gameState.gameClock}
            status={gameState.status}
            isConnected={isConnected}
          />
        )}

        {/* Debug Info */}
        <div className="mt-8 bg-gray-900 rounded-lg p-4">
          <p className="text-xs text-gray-500 font-mono">ESPN ID: {espnGameId}</p>
          <p className="text-xs text-gray-500 font-mono">Full Game ID: {fullGameId || 'Loading...'}</p>
          <p className="text-xs text-gray-500 font-mono">WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</p>
        </div>
      </div>
    </div>
  );
};

export default GameView;