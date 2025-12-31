import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Calendar, Users, BarChart3, Sun, Moon } from 'lucide-react';
import { useSeason } from '../contexts/SeasonContext';
import { useTheme } from '../contexts/ThemeContext';

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { season, setSeason, availableSeasons } = useSeason();
  const { theme, toggleTheme } = useTheme();

  const handleSeasonChange = (newSeason: number) => {
    setSeason(newSeason);
    navigate('/');  // Navigate to games page
  };

  const navItems = [
    { path: '/', label: 'Games', icon: Calendar },
    { path: '/players', label: 'Players', icon: Users },
    { path: '/stats', label: 'Stats', icon: BarChart3 },
  ];

  return (
    <header className="bg-iowa-black border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg overflow-hidden group-hover:glow-gold-sm transition-all">
              <img src="/bluderHerky.png" alt="Herky" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="font-athletic text-xl text-white tracking-wide">
                COURTVISION
              </h1>
              <p className="text-[10px] text-iowa-gold uppercase tracking-widest">
                Iowa Hawkeyes Analytics
              </p>
            </div>
          </Link>

          {/* Navigation - Desktop */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path || 
                (path !== '/' && location.pathname.startsWith(path));
              
              return (
                <Link
                  key={path}
                  to={path}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                    transition-all duration-200
                    ${isActive 
                      ? 'bg-iowa-gold/10 text-iowa-gold' 
                      : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Navigation - Mobile Bottom Bar */}
          <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 z-50">
            <div className="flex justify-around items-center h-16">
              {navItems.map(({ path, label, icon: Icon }) => {
                const isActive = location.pathname === path || 
                  (path !== '/' && location.pathname.startsWith(path));
                
                return (
                  <Link
                    key={path}
                    to={path}
                    className={`
                      flex flex-col items-center gap-1 px-4 py-2
                      ${isActive ? 'text-iowa-gold' : 'text-zinc-500'}
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-xs">{label}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          {/* Theme Toggle + Season Selector */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle Button */}
            <button
              className="p-2 rounded-lg bg-zinc-800 text-iowa-gold hover:bg-zinc-700 transition-colors"
              onClick={toggleTheme}
              title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            >
              {theme === 'light' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <select
              value={season}
              onChange={(e) => handleSeasonChange(Number(e.target.value))}
              className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm
                         text-white focus:border-iowa-gold focus:outline-none cursor-pointer"
            >
              {availableSeasons.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label} {s.current && '(Current)'}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Gold accent line */}
      <div className="h-0.5 bg-gradient-to-r from-transparent via-iowa-gold to-transparent opacity-30" />
    </header>
  );
}