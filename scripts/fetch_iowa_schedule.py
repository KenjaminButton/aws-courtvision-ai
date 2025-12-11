#!/usr/bin/env python3
"""
CourtVision AI - Iowa Hawkeyes Schedule Fetcher
Fetches complete season schedule including March Madness games from ESPN API.

Usage:
    python fetch_iowa_schedule.py [--season YEAR]
    
Example:
    python fetch_iowa_schedule.py --season 2025  # Gets 2024-25 season
"""

import argparse
import json
import requests
from datetime import datetime
from pathlib import Path


# ESPN API Configuration
IOWA_TEAM_ID = "2294"
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"


def fetch_schedule(season_year: int) -> dict:
    """
    Fetch Iowa's schedule for a given season.
    
    Args:
        season_year: The ending year of the season (e.g., 2025 for 2024-25 season)
    
    Returns:
        Raw API response as dictionary
    """
    url = f"{BASE_URL}/teams/{IOWA_TEAM_ID}/schedule?season={season_year}"
    print(f"Fetching: {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_schedule(raw_data: dict) -> list[dict]:
    """
    Parse raw ESPN schedule data into clean game records.
    
    Returns:
        List of game dictionaries with essential info
    """
    games = []
    events = raw_data.get('events', [])
    
    for event in events:
        game = {
            'game_id': event.get('id'),
            'date': event.get('date'),
            'name': event.get('name'),
            'short_name': event.get('shortName'),
            'season_year': event.get('season', {}).get('year'),
            'season_type_id': event.get('seasonType', {}).get('id'),
            'season_type': event.get('seasonType', {}).get('name'),
        }
        
        # Parse competition details
        competitions = event.get('competitions', [])
        if competitions:
            comp = competitions[0]
            game['venue'] = comp.get('venue', {}).get('fullName', 'Unknown')
            game['attendance'] = comp.get('attendance')
            game['neutral_site'] = comp.get('neutralSite', False)
            game['status'] = comp.get('status', {}).get('type', {}).get('description', 'Unknown')
            game['status_completed'] = comp.get('status', {}).get('type', {}).get('completed', False)
            
            # Tournament round info
            notes = comp.get('notes', [])
            if notes:
                game['tournament_round'] = notes[0].get('headline', '')
            
            # Parse competitors
            for competitor in comp.get('competitors', []):
                team_abbrev = competitor.get('team', {}).get('abbreviation')
                team_data = {
                    'team_id': competitor.get('team', {}).get('id'),
                    'name': competitor.get('team', {}).get('displayName'),
                    'abbreviation': team_abbrev,
                    'score': competitor.get('score', {}).get('displayValue'),
                    'winner': competitor.get('winner', False),
                    'home_away': competitor.get('homeAway'),
                }
                
                # Get game leaders
                leaders = {}
                for leader_cat in competitor.get('leaders', []):
                    cat_name = leader_cat.get('abbreviation', '').lower()
                    leader_list = leader_cat.get('leaders', [])
                    if leader_list:
                        leaders[cat_name] = {
                            'player': leader_list[0].get('athlete', {}).get('displayName'),
                            'value': leader_list[0].get('displayValue')
                        }
                team_data['leaders'] = leaders
                
                if team_abbrev == 'IOWA':
                    game['iowa'] = team_data
                else:
                    game['opponent'] = team_data
        
        games.append(game)
    
    return games


def print_schedule_summary(games: list[dict]) -> None:
    """Print a formatted summary of the schedule."""
    regular = [g for g in games if g.get('season_type_id') == '2']
    postseason = [g for g in games if g.get('season_type_id') == '3']
    completed = [g for g in games if g.get('status_completed')]
    
    print("\n" + "=" * 70)
    print("IOWA HAWKEYES SCHEDULE SUMMARY")
    print("=" * 70)
    print(f"Total Games: {len(games)}")
    print(f"  Regular Season: {len(regular)}")
    print(f"  Postseason (NCAA Tournament): {len(postseason)}")
    print(f"  Completed: {len(completed)}")
    
    # Win/Loss record for completed games
    wins = sum(1 for g in completed if g.get('iowa', {}).get('winner'))
    losses = len(completed) - wins
    print(f"  Record: {wins}-{losses}")
    
    print("\n" + "-" * 70)
    print("COMPLETED GAMES")
    print("-" * 70)
    for game in completed:
        date = game['date'][:10]
        iowa_score = game.get('iowa', {}).get('score', '?')
        opp = game.get('opponent', {})
        opp_abbrev = opp.get('abbreviation', 'OPP')
        opp_score = opp.get('score', '?')
        result = 'W' if game.get('iowa', {}).get('winner') else 'L'
        home_away = game.get('iowa', {}).get('home_away', '?')
        location = '@' if home_away == 'away' else 'vs'
        
        tournament = game.get('tournament_round', '')
        if tournament:
            tournament = f" [{tournament[:40]}]"
        
        print(f"  {date} | {location} {opp_abbrev:5} | Iowa {iowa_score:3} - {opp_score:3} ({result}){tournament}")
    
    print("\n" + "-" * 70)
    print("GAME IDs FOR PLAY-BY-PLAY FETCHING")
    print("-" * 70)
    print("Completed game IDs:")
    for game in completed:
        print(f"  {game['game_id']}")


def save_schedule(games: list[dict], output_dir: Path, season_year: int) -> Path:
    """Save parsed schedule to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"iowa_schedule_{season_year}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
            'team_id': IOWA_TEAM_ID,
            'season_year': season_year,
            'total_games': len(games),
            'games': games
        }, f, indent=2)
    
    print(f"\nSchedule saved to: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Fetch Iowa Hawkeyes schedule from ESPN API')
    parser.add_argument('--season', type=int, default=2025,
                       help='Season ending year (e.g., 2025 for 2024-25 season)')
    parser.add_argument('--output-dir', type=str, default='./data',
                       help='Output directory for JSON files')
    args = parser.parse_args()
    
    print(f"CourtVision AI - Schedule Fetcher")
    print(f"Fetching Iowa Hawkeyes {args.season-1}-{str(args.season)[2:]} season...")
    
    # Fetch and parse
    raw_data = fetch_schedule(args.season)
    games = parse_schedule(raw_data)
    
    # Display summary
    print_schedule_summary(games)
    
    # Save to file
    output_dir = Path(args.output_dir)
    save_schedule(games, output_dir, args.season)
    
    # Return completed game IDs for next step
    completed_ids = [g['game_id'] for g in games if g.get('status_completed')]
    print(f"\n✓ Found {len(completed_ids)} completed games ready for play-by-play fetching")
    
    return completed_ids


if __name__ == '__main__':
    main()