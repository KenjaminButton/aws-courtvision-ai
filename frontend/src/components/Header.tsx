import { Link, useLocation } from 'react-router-dom';
import { Activity, Calendar, Users, BarChart3 } from 'lucide-react';
import { useSeason } from '../contexts/SeasonContext';

export function Header() {
  const location = useLocation();
  const { season, setSeason, availableSeasons } = useSeason();

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
            <div className="w-10 h-10 bg-iowa-gold rounded-lg flex items-center justify-center group-hover:glow-gold-sm transition-all">
              <Activity className="w-6 h-6 text-iowa-black" />
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

          {/* Navigation */}
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

          {/* Season Selector */}
          <div className="flex items-center gap-3">
            <select
              value={season}
              onChange={(e) => setSeason(Number(e.target.value))}
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
