"""
CourtVision AI - Get Season Stats Lambda
Returns aggregated season statistics including record, splits, trends, and pattern insights.

Query params:
  - season: Season year (e.g., 2026 for 2025-26)
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'courtvision-games'))

IOWA_TEAM_ID = "2294"


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def get_season_games(season: str) -> list:
    """Get all games from SEASON# partition."""
    games = []
    
    response = table.query(
        KeyConditionExpression=Key('pk').eq(f'SEASON#{season}')
    )
    games.extend(response.get('Items', []))
    
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=Key('pk').eq(f'SEASON#{season}'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        games.extend(response.get('Items', []))
    
    return games


def get_game_metadata(game_id: str) -> dict:
    """Get METADATA for a single game."""
    response = table.get_item(
        Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
    )
    return response.get('Item', {})


def get_all_patterns_for_season(game_ids: list) -> list:
    """Get all patterns for a list of game IDs."""
    patterns = []
    
    for game_id in game_ids:
        response = table.query(
            KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#')
        )
        patterns.extend(response.get('Items', []))
        
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            patterns.extend(response.get('Items', []))
    
    return patterns


def parse_home_away_from_short_name(short_name: str) -> str:
    """
    Parse home/away from short_name like 'SOU @ IOWA' or 'IOWA @ OSU'.
    Returns 'home' if Iowa is after @, 'away' if Iowa is before @.
    """
    if not short_name or '@' not in short_name:
        return 'unknown'
    
    parts = short_name.split('@')
    if len(parts) != 2:
        return 'unknown'
    
    away_team = parts[0].strip().upper()
    home_team = parts[1].strip().upper()
    
    if 'IOWA' in home_team:
        return 'home'
    elif 'IOWA' in away_team:
        return 'away'
    
    return 'unknown'


def calculate_streak(games: list) -> dict:
    """Calculate current win/loss streak from most recent games."""
    if not games:
        return {'type': None, 'count': 0}
    
    # Sort by date descending (most recent first)
    sorted_games = sorted(
        [g for g in games if g.get('status_completed')],
        key=lambda x: x.get('date', ''),
        reverse=True
    )
    
    if not sorted_games:
        return {'type': None, 'count': 0}
    
    # Get streak type from most recent game
    streak_type = 'W' if sorted_games[0].get('iowa_won') else 'L'
    streak_count = 0
    
    for game in sorted_games:
        game_result = 'W' if game.get('iowa_won') else 'L'
        if game_result == streak_type:
            streak_count += 1
        else:
            break
    
    return {'type': streak_type, 'count': streak_count}


def aggregate_pattern_insights(patterns: list) -> dict:
    """Aggregate pattern data for season insights."""
    scoring_runs = [p for p in patterns if p.get('pattern_type') == 'scoring_run']
    hot_streaks = [p for p in patterns if p.get('pattern_type') == 'hot_streak']
    
    iowa_runs = [p for p in scoring_runs if p.get('is_iowa')]
    opponent_runs = [p for p in scoring_runs if not p.get('is_iowa')]
    
    iowa_streaks = [p for p in hot_streaks if p.get('is_iowa')]
    
    # Find hottest player (most hot streaks)
    player_streak_counts = defaultdict(lambda: {'name': '', 'count': 0})
    for streak in iowa_streaks:
        player_id = streak.get('player_id', '')
        player_name = streak.get('player_name', 'Unknown')
        if player_id:
            player_streak_counts[player_id]['name'] = player_name
            player_streak_counts[player_id]['count'] += 1
    
    hottest_player = None
    if player_streak_counts:
        hottest = max(player_streak_counts.items(), key=lambda x: x[1]['count'])
        hottest_player = {
            'player_id': hottest[0],
            'name': hottest[1]['name'],
            'count': hottest[1]['count']
        }
    
    # Find most common run quarter for Iowa
    quarter_counts = defaultdict(int)
    for run in iowa_runs:
        period = run.get('period', 0)
        if period:
            quarter_counts[period] += 1
    
    best_quarter = None
    if quarter_counts:
        best_q = max(quarter_counts.items(), key=lambda x: x[1])
        best_quarter = {'quarter': best_q[0], 'count': best_q[1]}
    
    return {
        'total_scoring_runs': len(scoring_runs),
        'iowa_runs': len(iowa_runs),
        'opponent_runs': len(opponent_runs),
        'total_hot_streaks': len(hot_streaks),
        'iowa_hot_streaks': len(iowa_streaks),
        'hottest_player': hottest_player,
        'best_quarter_for_runs': best_quarter,
    }


def handler(event, context):
    """Get aggregated season statistics."""
    try:
        params = event.get('queryStringParameters') or {}
        season = params.get('season', '2026')
        
        # 1. Get all games from SEASON# partition
        season_games = get_season_games(season)
        
        if not season_games:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': 'No games found for this season'})
            }
        
        # Filter to completed games only
        completed_games = [g for g in season_games if g.get('status_completed')]
        
        # 2. Fetch METADATA for each game to get home_away and conference info
        game_metadata = {}
        for game in completed_games:
            game_id = game.get('game_id')
            if game_id:
                metadata = get_game_metadata(game_id)
                if metadata:
                    game_metadata[game_id] = metadata
        
        # 3. Calculate basic record
        wins = sum(1 for g in completed_games if g.get('iowa_won'))
        losses = len(completed_games) - wins
        
        # 4. Calculate scoring stats
        total_iowa_points = 0
        total_opp_points = 0
        high_game = None
        low_game = None
        
        for game in completed_games:
            iowa_score = int(game.get('iowa_score', 0) or 0)
            opp_score = int(game.get('opponent_score', 0) or 0)
            
            total_iowa_points += iowa_score
            total_opp_points += opp_score
            
            if high_game is None or iowa_score > high_game['points']:
                high_game = {
                    'points': iowa_score,
                    'opponent': game.get('opponent_abbrev', ''),
                    'game_id': game.get('game_id', ''),
                    'date': game.get('date', '')
                }
            
            if low_game is None or iowa_score < low_game['points']:
                low_game = {
                    'points': iowa_score,
                    'opponent': game.get('opponent_abbrev', ''),
                    'game_id': game.get('game_id', ''),
                    'date': game.get('date', '')
                }
        
        games_played = len(completed_games)
        ppg = round(total_iowa_points / games_played, 1) if games_played > 0 else 0
        opp_ppg = round(total_opp_points / games_played, 1) if games_played > 0 else 0
        margin = round(ppg - opp_ppg, 1)
        
        # 5. Calculate splits
        splits = {
            'home': {'wins': 0, 'losses': 0, 'iowa_points': 0, 'opp_points': 0, 'games': 0},
            'away': {'wins': 0, 'losses': 0, 'iowa_points': 0, 'opp_points': 0, 'games': 0},
            'conference': {'wins': 0, 'losses': 0, 'iowa_points': 0, 'opp_points': 0, 'games': 0},
            'non_conference': {'wins': 0, 'losses': 0, 'iowa_points': 0, 'opp_points': 0, 'games': 0},
        }
        
        for game in completed_games:
            game_id = game.get('game_id')
            iowa_score = int(game.get('iowa_score', 0) or 0)
            opp_score = int(game.get('opponent_score', 0) or 0)
            won = game.get('iowa_won', False)
            
            # Determine home/away
            metadata = game_metadata.get(game_id, {})
            iowa_data = metadata.get('iowa', {})
            home_away = iowa_data.get('home_away', '')
            
            # Fallback to parsing from short_name if not in metadata
            if not home_away:
                home_away = parse_home_away_from_short_name(game.get('short_name', ''))
            
            if home_away == 'home':
                splits['home']['games'] += 1
                splits['home']['iowa_points'] += iowa_score
                splits['home']['opp_points'] += opp_score
                if won:
                    splits['home']['wins'] += 1
                else:
                    splits['home']['losses'] += 1
            elif home_away == 'away':
                splits['away']['games'] += 1
                splits['away']['iowa_points'] += iowa_score
                splits['away']['opp_points'] += opp_score
                if won:
                    splits['away']['wins'] += 1
                else:
                    splits['away']['losses'] += 1
            
            # Determine conference/non-conference
            is_conference = metadata.get('conference_competition', False)
            
            if is_conference:
                splits['conference']['games'] += 1
                splits['conference']['iowa_points'] += iowa_score
                splits['conference']['opp_points'] += opp_score
                if won:
                    splits['conference']['wins'] += 1
                else:
                    splits['conference']['losses'] += 1
            else:
                splits['non_conference']['games'] += 1
                splits['non_conference']['iowa_points'] += iowa_score
                splits['non_conference']['opp_points'] += opp_score
                if won:
                    splits['non_conference']['wins'] += 1
                else:
                    splits['non_conference']['losses'] += 1
        
        # Calculate split averages
        for split_name, split_data in splits.items():
            games = split_data['games']
            if games > 0:
                split_data['ppg'] = round(split_data['iowa_points'] / games, 1)
                split_data['opp_ppg'] = round(split_data['opp_points'] / games, 1)
                split_data['margin'] = round(split_data['ppg'] - split_data['opp_ppg'], 1)
                split_data['win_pct'] = round(split_data['wins'] / games, 3)
            else:
                split_data['ppg'] = 0
                split_data['opp_ppg'] = 0
                split_data['margin'] = 0
                split_data['win_pct'] = 0
        
        # 6. Calculate streak
        streak = calculate_streak(completed_games)
        
        # 7. Build games list for trend chart (chronological)
        games_list = []
        sorted_games = sorted(completed_games, key=lambda x: x.get('date', ''))
        
        for game in sorted_games:
            game_id = game.get('game_id')
            metadata = game_metadata.get(game_id, {})
            iowa_data = metadata.get('iowa', {})
            
            home_away = iowa_data.get('home_away', '')
            if not home_away:
                home_away = parse_home_away_from_short_name(game.get('short_name', ''))
            
            games_list.append({
                'game_id': game_id,
                'date': game.get('date', ''),
                'opponent': game.get('opponent_abbrev', ''),
                'iowa_score': int(game.get('iowa_score', 0) or 0),
                'opp_score': int(game.get('opponent_score', 0) or 0),
                'won': game.get('iowa_won', False),
                'home': home_away == 'home',
                'conference': metadata.get('conference_competition', False),
            })
        
        # 8. Get pattern insights
        game_ids = [g.get('game_id') for g in completed_games if g.get('game_id')]
        patterns = get_all_patterns_for_season(game_ids)
        pattern_insights = aggregate_pattern_insights(patterns)
        
        # 9. Build response
        response_data = {
            'season': season,
            'games_played': games_played,
            'record': {
                'wins': wins,
                'losses': losses,
                'pct': round(wins / games_played, 3) if games_played > 0 else 0,
            },
            'streak': streak,
            'scoring': {
                'ppg': ppg,
                'opp_ppg': opp_ppg,
                'margin': margin,
                'total_points': total_iowa_points,
                'total_opp_points': total_opp_points,
                'high_game': high_game,
                'low_game': low_game,
            },
            'splits': splits,
            'games': games_list,
            'patterns': pattern_insights,
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        }