import { createContext, useContext, useState, ReactNode } from 'react';

// Season configuration - ADD NEW SEASONS HERE
export const AVAILABLE_SEASONS = [
  { value: 2026, label: '2025-26 Season', current: true },  // Current season
  { value: 2025, label: '2024-25 Season', current: false }, // Last season
  // Add future seasons here:
  // { value: 2027, label: '2026-27 Season', current: false },
] as const;

// Default to current season
const CURRENT_SEASON = AVAILABLE_SEASONS.find(s => s.current)?.value || 2026;

interface SeasonContextType {
  season: number;
  setSeason: (season: number) => void;
  seasonLabel: string;
  availableSeasons: typeof AVAILABLE_SEASONS;
}

const SeasonContext = createContext<SeasonContextType | undefined>(undefined);

export function SeasonProvider({ children }: { children: ReactNode }) {
  const [season, setSeason] = useState<number>(CURRENT_SEASON);

  const seasonLabel = AVAILABLE_SEASONS.find(s => s.value === season)?.label || `${season - 1}-${String(season).slice(-2)} Season`;

  return (
    <SeasonContext.Provider value={{ 
      season, 
      setSeason, 
      seasonLabel,
      availableSeasons: AVAILABLE_SEASONS 
    }}>
      {children}
    </SeasonContext.Provider>
  );
}

export function useSeason() {
  const context = useContext(SeasonContext);
  if (context === undefined) {
    throw new Error('useSeason must be used within a SeasonProvider');
  }
  return context;
}

/*
 * ===========================================
 * HOW TO ADD A NEW SEASON (e.g., 2026-27)
 * ===========================================
 * 
 * 1. Update AVAILABLE_SEASONS array above:
 *    - Add new season at the TOP (most recent first)
 *    - Set `current: true` for the new season
 *    - Set `current: false` for all previous seasons
 * 
 * Example for 2026-27 season:
 * 
 * export const AVAILABLE_SEASONS = [
 *   { value: 2027, label: '2026-27 Season', current: true },  // NEW current
 *   { value: 2026, label: '2025-26 Season', current: false }, // Previous
 *   { value: 2025, label: '2024-25 Season', current: false }, // Historical
 * ] as const;
 * 
 * 2. Make sure your API has data for the new season:
 *    - Run your game fetching script for the new season
 *    - Ensure /games?season=2027 returns data
 * 
 * 3. That's it! The frontend will automatically:
 *    - Show the new season in the dropdown
 *    - Default to the current season
 *    - Fetch data for the selected season
 */