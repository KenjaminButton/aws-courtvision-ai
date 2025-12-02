import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import GameView from './pages/GameView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/game/:gameId" element={<GameView />} />
      </Routes>
    </Router>
  );
}

export default App;