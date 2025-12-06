import React, { useState, useEffect } from 'react';
import { GameCard } from '../components/GameCard';

interface Game {
  gameId: string;
  espnGameId: string;
  homeTeam: string;
  awayTeam: string;
  status: string;
  homeScore: number;
  awayScore: number;
}

const Dashboard: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL;
        const response = await fetch(`${apiUrl}/games`);
        const data = await response.json();
        setGames(data.games);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching games:', error);
        setLoading(false);
      }
    };

    fetchGames();
    const interval = setInterval(fetchGames, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const liveGames = games.filter(g => 
    g.status !== 'STATUS_SCHEDULED' && g.status !== 'STATUS_FINAL'
  );
  const upcomingGames = games.filter(g => g.status === 'STATUS_SCHEDULED');
  const completedGames = games.filter(g => {
  if (g.status !== 'STATUS_FINAL') return false;
  
  // Only show finals from today (extract date from gameId)
  // gameId format: "GAME#2025-12-05#TEAM1-TEAM2"
  const gameDate = g.gameId.split('#')[1]; // "2025-12-05"
  const today = new Date().toISOString().split('T')[0]; // "2025-12-05"
  
  return gameDate === today;
  });

  if (loading) {
    return <div className="min-h-screen bg-cv-navy text-white p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-cv-navy text-white p-8">
      <h1 className="text-4xl font-bold text-cv-teal mb-8">Today's Games</h1>

      {/* Live Games */}
      {liveGames.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Live Now</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {liveGames.map(game => (
              <GameCard key={game.espnGameId} {...game} />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Games */}
      {upcomingGames.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Upcoming</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {upcomingGames.map(game => (
              <GameCard key={game.espnGameId} {...game} />
            ))}
          </div>
        </div>
      )}

      {/* Completed Games */}
      {completedGames.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Final</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedGames.map(game => (
              <GameCard key={game.espnGameId} {...game} />
            ))}
          </div>
        </div>
      )}

      {games.length === 0 && (
        <p className="text-gray-400">No games today</p>
      )}
    </div>
  );
};

export default Dashboard;