import React from 'react';

const GameView: React.FC = () => {
  const wsUrl = process.env.REACT_APP_WEBSOCKET_URL;
  
  return (
    <div className="min-h-screen bg-cv-navy text-white">
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-cv-teal mb-4">Live Game</h1>
        <p className="text-gray-400">Game view - Live score and stats will go here</p>
        <p className="text-xs text-gray-600 mt-4">WebSocket: {wsUrl}</p>
      </div>
    </div>
  );
};

export default GameView;