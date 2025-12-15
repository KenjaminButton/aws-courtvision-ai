#!/usr/bin/env python3
"""
fetch_season_games.py - Intelligent Iowa Hawkeyes Game Fetcher

This script fetches Iowa Hawkeyes games from ESPN and stores them in DynamoDB.
It's designed to be run repeatedly without creating duplicates.

Features:
- Only fetches games not already in database
- Updates game results when games complete
- Tracks what was added/updated/skipped
- Safe to run daily or before each game

Usage:
    python3 fetch_season_games.py                    # Fetch current season (2025-26)
    python3 fetch_season_games.py --season 2025     # Fetch specific season (2024-25)
    python3 fetch_season_games.py --force           # Re-fetch all games (updates existing)
"""

import boto3
import requests
import json
import argparse
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration
IOWA_TEAM_ID = "2294"
DYNAMODB_TABLE = "courtvision-games"
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)


def get_season_label(season_value: int) -> str:
    """Convert season value to label (e.g., 2026 -> '2025-26')"""
    return f"{season_value - 1}-{str(season_value)[2:]}"


def fetch_espn_schedule(season_value: int) -> list:
    """Fetch schedule from ESPN API"""
    # ESPN uses the starting year for season parameter
    espn_season = season_value  # 2026 -> 2025
    
    url = f"{ESPN_BASE_URL}/teams/{IOWA_TEAM_ID}/schedule?season={espn_season}"
    
    print(f"📡 Fetching from ESPN: {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    events = data.get('events', [])
    games = []
    
    for event in events:
        game = parse_espn_event(event, season_value)
        if game:
            games.append(game)
    
    return games


def parse_espn_event(event: dict, season_value: int) -> dict:
    """Parse an ESPN event into our game format"""
    game_id = event.get('id')
    if not game_id:
        return None
    
    competitions = event.get('competitions', [])
    if not competitions:
        return None
    
    comp = competitions[0]
    competitors = comp.get('competitors', [])
    
    if len(competitors) < 2:
        return None
    
    # Determine home/away
    home_team = None
    away_team = None
    for c in competitors:
        if c.get('homeAway') == 'home':
            home_team = c
        else:
            away_team = c
    
    if not home_team or not away_team:
        home_team = competitors[0]
        away_team = competitors[1]
    
    # Extract team info
    home_name = home_team.get('team', {}).get('displayName', 'Unknown')
    home_abbrev = home_team.get('team', {}).get('abbreviation', 'UNK')
    home_id = home_team.get('team', {}).get('id', '')
    
    away_name = away_team.get('team', {}).get('displayName', 'Unknown')
    away_abbrev = away_team.get('team', {}).get('abbreviation', 'UNK')
    away_id = away_team.get('team', {}).get('id', '')
    
    # Extract scores
    home_score = home_team.get('score', '')
    away_score = away_team.get('score', '')
    
    # Handle score as dict or string
    if isinstance(home_score, dict):
        home_score = home_score.get('value', '')
    if isinstance(away_score, dict):
        away_score = away_score.get('value', '')
    
    home_score = str(home_score) if home_score else ''
    away_score = str(away_score) if away_score else ''
    
    # Normalize scores - remove ".0" from float strings like "91.0"
    if home_score and '.' in home_score:
        try:
            home_score = str(int(float(home_score)))
        except (ValueError, TypeError):
            pass
    if away_score and '.' in away_score:
        try:
            away_score = str(int(float(away_score)))
        except (ValueError, TypeError):
            pass
    
    # Status
    status_info = comp.get('status', {}).get('type', {})
    status = status_info.get('description', 'Scheduled')
    status_completed = status_info.get('completed', False)
    
    # Determine Iowa's perspective
    is_iowa_home = str(home_id) == IOWA_TEAM_ID
    iowa_score = home_score if is_iowa_home else away_score
    opponent_score = away_score if is_iowa_home else home_score
    opponent_name = away_name if is_iowa_home else home_name
    opponent_abbrev = away_abbrev if is_iowa_home else home_abbrev
    
    # Determine winner
    iowa_won = False
    if status_completed and iowa_score and opponent_score:
        try:
            # Handle scores that might be floats like "91.0"
            iowa_pts = int(float(iowa_score))
            opp_pts = int(float(opponent_score))
            iowa_won = iowa_pts > opp_pts
        except (ValueError, TypeError):
            iowa_won = False
    
    # Date
    date_str = event.get('date', '')
    
    # Short name (e.g., "NIU @ IOWA")
    short_name = event.get('shortName', f"{away_abbrev} @ {home_abbrev}")
    
    # Season type
    season_type = event.get('seasonType', {}).get('name', 'Regular Season')
    
    return {
        'game_id': game_id,
        'date': date_str,
        'short_name': short_name,
        'season_type': season_type,
        'season_value': season_value,
        'status': status,
        'status_completed': status_completed,
        'iowa_score': iowa_score,
        'iowa_won': iowa_won,
        'iowa_home': is_iowa_home,
        'opponent_name': opponent_name,
        'opponent_abbrev': opponent_abbrev,
        'opponent_score': opponent_score,
        'home_team': home_name,
        'away_team': away_name,
        'home_score': home_score,
        'away_score': away_score,
        'tournament_round': event.get('competitions', [{}])[0].get('notes', [{}])[0].get('headline') if event.get('competitions', [{}])[0].get('notes') else None
    }


def get_existing_games(season_value: int) -> dict:
    """Get all games already in DynamoDB for this season"""
    existing = {}
    
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f"SEASON#{season_value}"}
        )
        
        for item in response.get('Items', []):
            game_id = item.get('game_id')
            if game_id:
                existing[game_id] = item
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': f"SEASON#{season_value}"},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                game_id = item.get('game_id')
                if game_id:
                    existing[game_id] = item
                    
    except ClientError as e:
        print(f"⚠️  Error querying DynamoDB: {e}")
    
    return existing


def store_game(game: dict, season_value: int) -> bool:
    """Store a single game in DynamoDB"""
    try:
        # Create sort key from date and game_id
        date_part = game['date'].split('T')[0] if 'T' in game['date'] else game['date']
        
        item = {
            'pk': f"SEASON#{season_value}",
            'sk': f"GAME#{date_part}#{game['game_id']}",
            'game_id': game['game_id'],
            'date': game['date'],
            'short_name': game['short_name'],
            'season_type': game['season_type'],
            'status': game['status'],
            'status_completed': game['status_completed'],
            'iowa_score': game['iowa_score'],
            'iowa_won': game['iowa_won'],
            'opponent_abbrev': game['opponent_abbrev'],
            'opponent_score': game['opponent_score'],
            'tournament_round': game.get('tournament_round'),
            'updated_at': datetime.now().isoformat(),
        }
        
        table.put_item(Item=item)
        return True
        
    except ClientError as e:
        print(f"⚠️  Error storing game {game['game_id']}: {e}")
        return False


def games_are_different(new_game: dict, existing_game: dict) -> bool:
    """Check if game data has changed (e.g., game completed)"""
    # Key fields that indicate a meaningful change
    if new_game.get('status_completed') != existing_game.get('status_completed'):
        return True
    if new_game.get('iowa_score') != existing_game.get('iowa_score'):
        return True
    if new_game.get('opponent_score') != existing_game.get('opponent_score'):
        return True
    if new_game.get('status') != existing_game.get('status'):
        return True
    return False


def sync_season(season_value: int, force: bool = False) -> dict:
    """
    Sync games for a season.
    
    Returns dict with counts: added, updated, skipped, errors
    """
    season_label = get_season_label(season_value)
    print(f"\n🏀 Syncing Iowa Hawkeyes {season_label} Season (value: {season_value})")
    print("=" * 60)
    
    # Fetch from ESPN
    espn_games = fetch_espn_schedule(season_value)
    print(f"📊 Found {len(espn_games)} games on ESPN schedule")
    
    # Get existing games
    existing_games = get_existing_games(season_value)
    print(f"💾 Found {len(existing_games)} games already in database")
    
    # Track results
    results = {
        'added': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'games_added': [],
        'games_updated': [],
    }
    
    print("\n📝 Processing games...")
    print("-" * 60)
    
    for game in espn_games:
        game_id = game['game_id']
        date_str = game['date'].split('T')[0] if 'T' in game['date'] else game['date']
        opponent = game['opponent_abbrev']
        status = "✅" if game['status_completed'] else "📅"
        
        if game_id in existing_games:
            existing = existing_games[game_id]
            
            if force or games_are_different(game, existing):
                # Game changed (e.g., completed), update it
                if store_game(game, season_value):
                    results['updated'] += 1
                    results['games_updated'].append(game)
                    
                    # Show what changed
                    if not existing.get('status_completed') and game['status_completed']:
                        score = f"{game['iowa_score']}-{game['opponent_score']}"
                        result = "W" if game['iowa_won'] else "L"
                        print(f"   🔄 UPDATED: {date_str} vs {opponent} → {result} {score}")
                    else:
                        print(f"   🔄 UPDATED: {date_str} vs {opponent}")
                else:
                    results['errors'] += 1
            else:
                # No changes, skip
                results['skipped'] += 1
                print(f"   ⏭️  SKIPPED: {date_str} vs {opponent} (no changes)")
        else:
            # New game, add it
            if store_game(game, season_value):
                results['added'] += 1
                results['games_added'].append(game)
                
                if game['status_completed']:
                    score = f"{game['iowa_score']}-{game['opponent_score']}"
                    result = "W" if game['iowa_won'] else "L"
                    print(f"   ✨ ADDED:   {date_str} vs {opponent} → {result} {score}")
                else:
                    print(f"   ✨ ADDED:   {date_str} vs {opponent} (scheduled)")
            else:
                results['errors'] += 1
    
    return results


def print_summary(results: dict, season_value: int):
    """Print a summary of the sync operation"""
    season_label = get_season_label(season_value)
    
    print("\n" + "=" * 60)
    print(f"📊 SYNC SUMMARY - {season_label} Season")
    print("=" * 60)
    print(f"   ✨ Games added:   {results['added']}")
    print(f"   🔄 Games updated: {results['updated']}")
    print(f"   ⏭️  Games skipped: {results['skipped']}")
    if results['errors'] > 0:
        print(f"   ❌ Errors:        {results['errors']}")
    
    total_processed = results['added'] + results['updated'] + results['skipped']
    print(f"\n   Total games in season: {total_processed}")
    
    # Show upcoming games
    upcoming = [g for g in results.get('games_added', []) if not g['status_completed']]
    if upcoming:
        print(f"\n📅 Upcoming games added:")
        for game in upcoming[:5]:  # Show next 5
            date_str = game['date'].split('T')[0]
            print(f"      {date_str} vs {game['opponent_abbrev']}")
    
    print("\n✅ Sync complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch Iowa Hawkeyes games from ESPN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 fetch_season_games.py                  # Current season (2025-26)
  python3 fetch_season_games.py --season 2025   # 2024-25 season
  python3 fetch_season_games.py --force         # Update all games
  python3 fetch_season_games.py --season 2025 --force
        """
    )
    
    parser.add_argument(
        '--season',
        type=int,
        default=2026,  # Current season: 2025-26
        help='Season ending year (e.g., 2026 for 2025-26 season). Default: 2026'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update all games, even if unchanged'
    )
    
    args = parser.parse_args()
    
    # Validate season
    current_year = datetime.now().year
    if args.season < 2020 or args.season > current_year + 2:
        print(f"❌ Invalid season: {args.season}")
        print(f"   Valid range: 2020 - {current_year + 2}")
        return 1
    
    try:
        results = sync_season(args.season, force=args.force)
        print_summary(results, args.season)
        return 0
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == '__main__':
    exit(main())