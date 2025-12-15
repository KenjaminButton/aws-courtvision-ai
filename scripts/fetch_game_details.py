#!/usr/bin/env python3
"""
fetch_game_details.py - Fetch detailed game data (plays, box score) from ESPN

This script fetches play-by-play and box score data for completed games
and stores it in DynamoDB. It only fetches details for games that:
1. Are completed
2. Don't already have detailed data

Usage:
    python3 fetch_game_details.py                    # Process all pending games
    python3 fetch_game_details.py --game 401713556  # Fetch specific game
    python3 fetch_game_details.py --season 2026     # Specific season
    python3 fetch_game_details.py --force           # Re-fetch all details
"""

import boto3
import requests
import json
import argparse
import time
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration
DYNAMODB_TABLE = "courtvision-games"
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"
IOWA_TEAM_ID = "2294"

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types for JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_pending_games(season_value: int) -> list:
    """Get completed games that don't have detailed data yet"""
    games = []
    
    try:
        response = table.query(
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': f"SEASON#{season_value}"}
        )
        
        for item in response.get('Items', []):
            # Only get completed games without details
            if item.get('status_completed') and not item.get('details_fetched'):
                games.append(item)
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': f"SEASON#{season_value}"},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                if item.get('status_completed') and not item.get('details_fetched'):
                    games.append(item)
                    
    except ClientError as e:
        print(f"⚠️  Error querying DynamoDB: {e}")
    
    return games


def fetch_game_summary(game_id: str) -> dict:
    """Fetch full game summary from ESPN"""
    url = f"{ESPN_BASE_URL}/summary?event={game_id}"
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    return response.json()


def parse_plays(summary: dict, game_id: str) -> list:
    """Extract plays from game summary"""
    plays = []
    raw_plays = summary.get('plays', [])
    
    for i, play in enumerate(raw_plays):
        parsed = {
            'game_id': game_id,
            'play_id': play.get('id', f"{game_id}_{i}"),
            'sequence': play.get('sequenceNumber', i),
            'period': play.get('period', {}).get('number', 1),
            'clock': play.get('clock', {}).get('displayValue', ''),
            'type': play.get('type', {}).get('text', ''),
            'text': play.get('text', ''),
            'scoring_play': play.get('scoringPlay', False),
            'score_value': play.get('scoreValue', 0),
            'home_score': play.get('homeScore', 0),
            'away_score': play.get('awayScore', 0),
            'team_id': play.get('team', {}).get('id', ''),
            'wallclock': play.get('wallclock', ''),
        }
        
        # Extract coordinates if available
        if 'coordinate' in play:
            parsed['coordinate_x'] = play['coordinate'].get('x')
            parsed['coordinate_y'] = play['coordinate'].get('y')
        
        # Extract player info if available
        participants = play.get('participants', [])
        if participants and 'athlete' in participants[0]:
            athlete = participants[0]['athlete']
            parsed['player_id'] = athlete.get('id', '')
            parsed['player_name'] = athlete.get('displayName', '')
        
        plays.append(parsed)
    
    return plays


def parse_boxscore(summary: dict) -> dict:
    """Extract box score from game summary"""
    boxscore = summary.get('boxscore', {})
    
    result = {
        'teams': [],
        'players': {}
    }
    
    # Get team info from teams array
    teams = boxscore.get('teams', [])
    for team in teams:
        team_data = team.get('team', {})
        team_id = team_data.get('id', '')
        
        result['teams'].append({
            'team_id': team_id,
            'name': team_data.get('displayName', ''),
            'abbreviation': team_data.get('abbreviation', ''),
            'home_away': team.get('homeAway', ''),
        })
        result['players'][team_id] = []
    
    # Get player stats from players array (separate from teams!)
    player_groups = boxscore.get('players', [])
    for group in player_groups:
        team_data = group.get('team', {})
        team_id = team_data.get('id', '')
        
        if team_id not in result['players']:
            result['players'][team_id] = []
        
        # Get the statistics categories
        statistics = group.get('statistics', [])
        if statistics:
            stat_cat = statistics[0]  # Usually just one category
            athletes = stat_cat.get('athletes', [])
            
            for athlete in athletes:
                player_stats = parse_player_stats(athlete)
                if player_stats:
                    result['players'][team_id].append(player_stats)
    
    return result


def parse_player_stats(athlete: dict) -> dict:
    """Parse individual player statistics"""
    athlete_info = athlete.get('athlete', {})
    stats = athlete.get('stats', [])
    
    # ESPN stats order: MIN, PTS, FG, 3PT, FT, REB, AST, TO, STL, BLK, OREB, DREB, PF
    
    player = {
        'player_id': athlete_info.get('id', ''),
        'player_name': athlete_info.get('displayName', ''),
        'jersey': athlete_info.get('jersey', ''),
        'position': athlete_info.get('position', {}).get('abbreviation', ''),
    }
    
    if len(stats) >= 13:
        try:
            player['minutes'] = stats[0] if stats[0] != '--' else '0'
            player['points'] = int(stats[1]) if stats[1] not in ['--', ''] else 0
            player['field_goals'] = stats[2] if stats[2] != '--' else '0-0'
            player['three_pointers'] = stats[3] if stats[3] != '--' else '0-0'
            player['free_throws'] = stats[4] if stats[4] != '--' else '0-0'
            player['rebounds'] = int(stats[5]) if stats[5] not in ['--', ''] else 0
            player['assists'] = int(stats[6]) if stats[6] not in ['--', ''] else 0
            player['turnovers'] = int(stats[7]) if stats[7] not in ['--', ''] else 0
            player['steals'] = int(stats[8]) if stats[8] not in ['--', ''] else 0
            player['blocks'] = int(stats[9]) if stats[9] not in ['--', ''] else 0
            player['offensive_rebounds'] = int(stats[10]) if stats[10] not in ['--', ''] else 0
            player['defensive_rebounds'] = int(stats[11]) if stats[11] not in ['--', ''] else 0
            player['fouls'] = int(stats[12]) if stats[12] not in ['--', ''] else 0
        except (ValueError, IndexError) as e:
            print(f"⚠️  Error parsing stats for {player['player_name']}: {e}")
    
    return player


def build_metadata(game_id: str, season_value: int, summary: dict, plays: list, boxscore: dict) -> dict:
    """Build METADATA record in format frontend expects"""
    header = summary.get('header', {})
    competitions = header.get('competitions', [{}])
    competition = competitions[0] if competitions else {}
    competitors = competition.get('competitors', [])
    
    iowa_data = None
    opponent_data = None
    
    for comp in competitors:
        team = comp.get('team', {})
        team_id = str(team.get('id', ''))
        
        team_info = {
            'team_id': team_id,
            'name': team.get('displayName', ''),
            'abbreviation': team.get('abbreviation', ''),
            'home_away': comp.get('homeAway', ''),
            'score': str(comp.get('score', '0')),
            'winner': comp.get('winner', False),
            'period_scores': [str(p.get('value', 0)) for p in comp.get('linescores', [])]
        }
        
        if team_id == IOWA_TEAM_ID:
            iowa_data = team_info
        else:
            opponent_data = team_info
    
    # Get opponent team_id for player_stats
    opponent_team_id = opponent_data['team_id'] if opponent_data else ''
    
    return {
        'pk': f"GAME#{game_id}",
        'sk': 'METADATA',
        'entity_type': 'GAME',
        'game_id': game_id,
        'season': season_value,
        'season_type': str(summary.get('header', {}).get('season', {}).get('type', 2)),
        'date': competition.get('date', ''),
        'status': competition.get('status', {}).get('type', {}).get('description', 'Final'),
        'neutral_site': competition.get('neutralSite', False),
        'conference_competition': competition.get('conferenceCompetition', False),
        'play_count': str(len(plays)),
        'iowa': iowa_data,
        'opponent': opponent_data,
        'venue': {},
        'boxscore': boxscore,
        'player_stats': {
            'iowa': boxscore.get('players', {}).get(IOWA_TEAM_ID, []),
            'opponent': boxscore.get('players', {}).get(opponent_team_id, [])
        },
        'fetched_at': datetime.now().isoformat() + 'Z',
    }


def store_game_details(game_id: str, season_value: int, plays: list, boxscore: dict, summary: dict) -> bool:
    """Store game details in DynamoDB"""
    try:
        # Build and store METADATA record (what frontend expects)
        metadata = build_metadata(game_id, season_value, summary, plays, boxscore)
        table.put_item(Item=metadata)
        
        # Store DETAILS record (for raw data backup)
        detail_item = {
            'pk': f"GAME#{game_id}",
            'sk': 'DETAILS',
            'game_id': game_id,
            'season': season_value,
            'play_count': len(plays),
            'boxscore': json.loads(json.dumps(boxscore, cls=DecimalEncoder)),
            'fetched_at': datetime.now().isoformat(),
        }
        table.put_item(Item=detail_item)
        
        # Store plays in batches
        with table.batch_writer() as batch:
            for play in plays:
                play_item = {
                    'pk': f"GAME#{game_id}",
                    'sk': f"PLAY#{int(play['sequence']):04d}",
                    **play
                }
                # Convert any float coordinates to Decimal
                if 'coordinate_x' in play_item and play_item['coordinate_x'] is not None:
                    play_item['coordinate_x'] = Decimal(str(play_item['coordinate_x']))
                if 'coordinate_y' in play_item and play_item['coordinate_y'] is not None:
                    play_item['coordinate_y'] = Decimal(str(play_item['coordinate_y']))
                
                batch.put_item(Item=play_item)
        
        # Mark game as having details fetched
        response = table.query(
            KeyConditionExpression='pk = :pk AND begins_with(sk, :sk)',
            ExpressionAttributeValues={
                ':pk': f"SEASON#{season_value}",
                ':sk': 'GAME#'
            }
        )
        
        for item in response.get('Items', []):
            if item.get('game_id') == game_id:
                table.update_item(
                    Key={'pk': item['pk'], 'sk': item['sk']},
                    UpdateExpression='SET details_fetched = :val, details_fetched_at = :ts',
                    ExpressionAttributeValues={
                        ':val': True,
                        ':ts': datetime.now().isoformat()
                    }
                )
                break
        
        return True
        
    except ClientError as e:
        print(f"⚠️  Error storing game details: {e}")
        return False


def process_game(game_id: str, season_value: int) -> dict:
    """Process a single game - fetch and store details"""
    result = {
        'game_id': game_id,
        'success': False,
        'plays': 0,
        'players': 0,
        'error': None
    }
    
    try:
        # Fetch from ESPN
        summary = fetch_game_summary(game_id)
        
        # Parse plays
        plays = parse_plays(summary, game_id)
        result['plays'] = len(plays)
        
        # Parse boxscore
        boxscore = parse_boxscore(summary)
        result['players'] = sum(len(p) for p in boxscore.get('players', {}).values())
        
        # Store in DynamoDB (now passing summary for METADATA creation)
        if store_game_details(game_id, season_value, plays, boxscore, summary):
            result['success'] = True
        else:
            result['error'] = "Failed to store in DynamoDB"
            
    except requests.exceptions.RequestException as e:
        result['error'] = f"Network error: {e}"
    except Exception as e:
        result['error'] = f"Error: {e}"
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Fetch detailed game data from ESPN'
    )
    
    parser.add_argument(
        '--season',
        type=int,
        default=2026,
        help='Season ending year (default: 2026 for 2025-26)'
    )
    
    parser.add_argument(
        '--game',
        type=str,
        help='Specific game ID to fetch'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch even if already fetched'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Limit number of games to process (0 = no limit)'
    )
    
    args = parser.parse_args()
    
    print(f"\n🏀 Fetching Game Details - {args.season - 1}-{str(args.season)[2:]} Season")
    print("=" * 60)
    
    if args.game:
        # Process specific game
        print(f"📡 Fetching game {args.game}...")
        result = process_game(args.game, args.season)
        
        if result['success']:
            print(f"✅ Success! {result['plays']} plays, {result['players']} players")
        else:
            print(f"❌ Failed: {result['error']}")
        return
    
    # Get pending games
    if args.force:
        print("⚠️  Force mode: Will re-fetch all completed games")
        # TODO: Implement force mode - get all completed games
        games = get_pending_games(args.season)
    else:
        games = get_pending_games(args.season)
    
    print(f"📋 Found {len(games)} games needing details")
    
    if not games:
        print("✅ All completed games already have details!")
        return
    
    if args.limit > 0:
        games = games[:args.limit]
        print(f"📋 Processing {len(games)} games (limit applied)")
    
    # Process each game
    success_count = 0
    error_count = 0
    
    for i, game in enumerate(games, 1):
        game_id = game['game_id']
        opponent = game.get('opponent_abbrev', 'Unknown')
        date = game.get('date', '').split('T')[0]
        
        print(f"\n[{i}/{len(games)}] {date} vs {opponent} (ID: {game_id})")
        
        result = process_game(game_id, args.season)
        
        if result['success']:
            print(f"   ✅ {result['plays']} plays, {result['players']} players")
            success_count += 1
        else:
            print(f"   ❌ {result['error']}")
            error_count += 1
        
        # Be nice to ESPN's servers
        if i < len(games):
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()