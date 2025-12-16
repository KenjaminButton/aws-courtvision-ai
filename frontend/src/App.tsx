import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { HomePage } from './pages/HomePage';
import { GamePage } from './pages/GamePage';
import { PlayersPage } from './pages/PlayersPage';
import { PlayerDetailPage } from './pages/PlayerDetailPage';
import { SeasonProvider } from './contexts/SeasonContext';
import { StatsPage } from './pages/StatsPage';


function App() {
  return (
    <BrowserRouter>
      <SeasonProvider>
        <div className="min-h-screen bg-iowa-black bg-athletic-stripes">
          <Header />
          <main className="pb-20 md:pb-0">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/game/:gameId" element={<GamePage />} />
              <Route path="/players" element={<PlayersPage />} />
              <Route path="/players/:playerId" element={<PlayerDetailPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </SeasonProvider>
    </BrowserRouter>
  );
}

// Simple placeholder for future pages
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-16 text-center">
      <h1 className="font-athletic text-4xl text-white mb-4">{title.toUpperCase()}</h1>
      <p className="text-zinc-500">Coming soon...</p>
    </div>
  );
}

// Footer component
function Footer() {
  return (
    <footer className="border-t border-zinc-800 mt-16">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-iowa-gold rounded-lg flex items-center justify-center">
              <span className="font-athletic text-iowa-black text-sm">CV</span>
            </div>
            <div>
              <p className="text-white font-semibold">CourtVision AI</p>
              <p className="text-xs text-zinc-500">Iowa Hawkeyes Analytics</p>
            </div>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-zinc-500">
            <span>Data from ESPN</span>
            <span>•</span>
            <span>Built with AWS</span>
            <span>•</span>
            <span className="text-iowa-gold">Go Hawks! 🏀</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default App;