import { useState, useEffect, useRef } from 'react';

interface CommentaryItem {
  commentary: string;
  excitement: number;
  timestamp: string;
  playId: string;
}

interface GameState {
  type: string;
  gameId: string;
  homeTeam?: string;
  awayTeam?: string;
  homeScore?: number;
  awayScore?: number;
  quarter?: string | null;
  gameClock?: string;
  status?: string;
  lastUpdated?: string;
  winProbability?: {
    homeProbability: number;
    awayProbability: number;
    reasoning: string;
    calculatedAt: string;
  };
}

export function useWebSocket(gameId: string | undefined, initialCommentary: CommentaryItem[] = []) {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [commentary, setCommentary] = useState<CommentaryItem[]>(initialCommentary);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update commentary when initialCommentary changes
  useEffect(() => {
    setCommentary(initialCommentary);
  }, [initialCommentary]);

  useEffect(() => {
    if (!gameId) return;

    const wsUrl = process.env.REACT_APP_WEBSOCKET_URL;
    if (!wsUrl) {
      setError('WebSocket URL not configured');
      return;
    }

    const connect = () => {
      console.log('🔌 Connecting to WebSocket...');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);

        // Subscribe to game updates
        ws.send(JSON.stringify({ action: 'subscribe', gameId }));
        console.log(`📡 Subscribed to ${gameId}`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Received:', data);

          if (data.type === 'game_state' || data.type === 'score_update') {
            setGameState(data);
          }
          
          // Handle win probability updates
          if (data.type === 'win_probability') {
            setGameState((prev) => ({
              ...prev!,
              winProbability: {
                homeProbability: data.homeProbability,
                awayProbability: data.awayProbability,
                reasoning: data.reasoning,
                calculatedAt: data.calculatedAt,
              }
            }));
          }

          // Handle AI commentary updates
          if (data.type === 'commentary') {
            const newCommentary: CommentaryItem = {
              commentary: data.data.commentary,
              excitement: data.data.excitement,
              timestamp: data.data.generatedAt || new Date().toISOString(),
              playId: data.data.playId || `commentary-${Date.now()}`,
            };
            
            // Add to the beginning (newest first)
            setCommentary((prev) => {
              // Avoid duplicates
              if (prev.some(c => c.playId === newCommentary.playId)) {
                return prev;
              }
              return [newCommentary, ...prev];
            });
            
            console.log('🎙️ New commentary:', newCommentary.commentary);
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);

        // Attempt reconnection after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect...');
          connect();
        }, 3000);
      };
    };

    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [gameId]);

  return { gameState, commentary, isConnected, error };
}