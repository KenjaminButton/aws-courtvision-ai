#!/usr/bin/env python3
"""
CourtVision AI - Play-by-Play Fetcher
Fetches detailed play-by-play data for Iowa games from ESPN API.

Usage:
    python fetch_playbyplay.py --game-id 401746037
    python fetch_playbyplay.py --from-schedule ./data/iowa_schedule_2025.json
"""

import argparse
import json
import time
import requests
from datetime import datetime
from pathlib import Path


BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"


def fetch_game_summary(game_id: str) -> dict:
    """
    Fetch complete game summary including play-by-play from ESPN.
    
    Args:
        game_id: ESPN game ID (e.g., '401746037')
    
    Returns:
        Raw API response as dictionary
    """
    url = f"{BASE_URL}/summary?event={game_id}"
    print(f"  Fetching game {game_id}...")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_game_data(raw_data: dict, game_id: str) -> dict:
    """
    Parse raw ESPN game summary into structured format for DynamoDB.
    
    Returns:
        Dictionary with game metadata, boxscore, and plays
    """
    game = {
        'game_id': game_id,
        'fetched_at': datetime.utcnow().isoformat() + 'Z',
    }
    
    # Parse header info
    header = raw_data.get('header', {})
    if header:
        game['season'] = header.get('season', {}).get('year')
        game['season_type'] = header.get('season', {}).get('type')
        
        competitions = header.get('competitions', [])
        if competitions:
            comp = competitions[0]
            game['date'] = comp.get('date')
            game['neutral_site'] = comp.get('neutralSite', False)
            game['conference_competition'] = comp.get('conferenceCompetition', False)
            game['attendance'] = comp.get('attendance')
            game['status'] = comp.get('status', {}).get('type', {}).get('description')
            
            # Venue
            venue = comp.get('venue', {})
            game['venue'] = {
                'name': venue.get('fullName'),
                'city': venue.get('address', {}).get('city'),
                'state': venue.get('address', {}).get('state'),
            }
            
            # Teams
            for competitor in comp.get('competitors', []):
                team_info = {
                    'team_id': competitor.get('id'),
                    'name': competitor.get('team', {}).get('displayName'),
                    'abbreviation': competitor.get('team', {}).get('abbreviation'),
                    'score': competitor.get('score'),
                    'winner': competitor.get('winner', False),
                    'home_away': competitor.get('homeAway'),
                    'rank': competitor.get('rank'),
                }
                
                # Line scores by period
                line_scores = competitor.get('linescores', [])
                team_info['period_scores'] = [ls.get('displayValue') for ls in line_scores]
                
                if team_info['abbreviation'] == 'IOWA':
                    game['iowa'] = team_info
                else:
                    game['opponent'] = team_info
    
    # Parse boxscore
    boxscore = raw_data.get('boxscore', {})
    if boxscore:
        game['boxscore'] = {}
        
        for team_box in boxscore.get('teams', []):
            team_stats = team_box.get('statistics', [])
            team_abbrev = None
            
            # Get team abbreviation from display name
            display_name = team_box.get('team', {}).get('displayName', '')
            if 'Iowa' in display_name:
                team_abbrev = 'IOWA'
            else:
                team_abbrev = game.get('opponent', {}).get('abbreviation', 'OPP')
            
            stats_dict = {}
            for stat in team_stats:
                stat_name = stat.get('name', '').lower().replace(' ', '_')
                stats_dict[stat_name] = stat.get('displayValue')
            
            game['boxscore'][team_abbrev] = stats_dict
        
        # Player stats
        players = boxscore.get('players', [])
        game['player_stats'] = {}
        
        for team_players in players:
            team_name = team_players.get('team', {}).get('displayName', '')
            team_key = 'iowa' if 'Iowa' in team_name else 'opponent'
            game['player_stats'][team_key] = []
            
            for stat_section in team_players.get('statistics', []):
                stat_keys = stat_section.get('keys', [])
                
                for athlete in stat_section.get('athletes', []):
                    player = {
                        'player_id': athlete.get('athlete', {}).get('id'),
                        'name': athlete.get('athlete', {}).get('displayName'),
                        'jersey': athlete.get('athlete', {}).get('jersey'),
                        'position': athlete.get('athlete', {}).get('position', {}).get('abbreviation'),
                        'starter': athlete.get('starter', False),
                    }
                    
                    # Map stats
                    stat_values = athlete.get('stats', [])
                    for i, key in enumerate(stat_keys):
                        if i < len(stat_values):
                            player[key.lower()] = stat_values[i]
                    
                    game['player_stats'][team_key].append(player)
    
    # Parse plays (the key data for our analytics!)
    plays = raw_data.get('plays', [])
    game['plays'] = []
    game['play_count'] = len(plays)
    
    for play in plays:
        parsed_play = {
            'play_id': play.get('id'),
            'sequence': play.get('sequenceNumber'),
            'period': play.get('period', {}).get('number'),
            'clock': play.get('clock', {}).get('displayValue'),
            'team_id': play.get('team', {}).get('id'),
            'type': play.get('type', {}).get('text'),
            'type_id': play.get('type', {}).get('id'),
            'text': play.get('text'),
            'scoring_play': play.get('scoringPlay', False),
            'score_value': play.get('scoreValue'),
            'away_score': play.get('awayScore'),
            'home_score': play.get('homeScore'),
            'wallclock': play.get('wallClock'),
        }
        
        # Participants (players involved)
        participants = play.get('participants', [])
        if participants:
            parsed_play['participants'] = [
                {
                    'player_id': p.get('athlete', {}).get('id'),
                    'name': p.get('athlete', {}).get('displayName'),
                }
                for p in participants
            ]
        
        game['plays'].append(parsed_play)
    
    return game


def fetch_games_from_schedule(schedule_file: Path, output_dir: Path, delay: float = 1.0) -> list[dict]:
    """
    Fetch play-by-play for all completed games in a schedule file.
    
    Args:
        schedule_file: Path to schedule JSON file
        output_dir: Directory to save individual game files
        delay: Seconds to wait between API calls (be nice to ESPN)
    
    Returns:
        List of parsed game data
    """
    with open(schedule_file) as f:
        schedule = json.load(f)
    
    games_data = []
    completed_games = [g for g in schedule['games'] if g.get('status_completed')]
    
    print(f"\nFetching play-by-play for {len(completed_games)} completed games...")
    print("-" * 60)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, game in enumerate(completed_games, 1):
        game_id = game['game_id']
        
        # Check if we already have this game
        game_file = output_dir / f"game_{game_id}.json"
        if game_file.exists():
            print(f"  [{i}/{len(completed_games)}] Game {game_id} already fetched, skipping...")
            with open(game_file) as f:
                games_data.append(json.load(f))
            continue
        
        try:
            raw_data = fetch_game_summary(game_id)
            parsed_data = parse_game_data(raw_data, game_id)
            
            # Save individual game file
            with open(game_file, 'w') as f:
                json.dump(parsed_data, f, indent=2)
            
            games_data.append(parsed_data)
            
            date = game.get('date', '')[:10]
            plays = parsed_data.get('play_count', 0)
            opp = game.get('opponent', {}).get('abbreviation', 'OPP')
            print(f"  [{i}/{len(completed_games)}] {date} vs {opp}: {plays} plays fetched")
            
            # Be nice to the API
            if i < len(completed_games):
                time.sleep(delay)
                
        except Exception as e:
            print(f"  [{i}/{len(completed_games)}] ERROR fetching {game_id}: {e}")
    
    return games_data


def main():
    parser = argparse.ArgumentParser(description='Fetch play-by-play data from ESPN API')
    parser.add_argument('--game-id', type=str, help='Single game ID to fetch')
    parser.add_argument('--from-schedule', type=str, 
                       help='Schedule JSON file to fetch all games from')
    parser.add_argument('--output-dir', type=str, default='./data/games',
                       help='Output directory for game JSON files')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between API calls in seconds')
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    if args.game_id:
        # Fetch single game
        print(f"CourtVision AI - Fetching game {args.game_id}")
        raw_data = fetch_game_summary(args.game_id)
        parsed_data = parse_game_data(raw_data, args.game_id)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"game_{args.game_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(parsed_data, f, indent=2)
        
        print(f"\n✓ Game saved to: {output_file}")
        print(f"  Plays: {parsed_data.get('play_count', 0)}")
        
    elif args.from_schedule:
        # Fetch all games from schedule
        schedule_path = Path(args.from_schedule)
        if not schedule_path.exists():
            print(f"ERROR: Schedule file not found: {schedule_path}")
            return
        
        print(f"CourtVision AI - Batch Play-by-Play Fetcher")
        games = fetch_games_from_schedule(schedule_path, output_dir, args.delay)
        
        total_plays = sum(g.get('play_count', 0) for g in games)
        print(f"\n" + "=" * 60)
        print(f"✓ Fetched {len(games)} games with {total_plays:,} total plays")
        print(f"  Data saved to: {output_dir}")
        
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python fetch_playbyplay.py --game-id 401746037")
        print("  python fetch_playbyplay.py --from-schedule ./data/iowa_schedule_2025.json")


if __name__ == '__main__':
    main()