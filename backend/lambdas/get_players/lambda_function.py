"""
CourtVision AI - Get Players Lambda
Returns aggregated player statistics for a season, including game logs.

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


def handler(event, context):
    """Get aggregated player stats for a season."""
    try:
        params = event.get('queryStringParameters') or {}
        season = params.get('season', '2026')
        
        # Get all games for the season
        games_response = table.query(
            KeyConditionExpression=Key('pk').eq(f'SEASON#{season}')
        )
        
        # Build list of completed games with metadata
        completed_games = []
        for item in games_response.get('Items', []):
            if item.get('status_completed'):
                completed_games.append({
                    'game_id': item['game_id'],
                    'date': item.get('date', ''),
                    'opponent': item.get('opponent_abbrev', 'OPP'),
                    'iowa_won': item.get('iowa_won', False),
                    'iowa_score': item.get('iowa_score', '0'),
                    'opponent_score': item.get('opponent_score', '0'),
                })
        
        # Sort games by date
        completed_games.sort(key=lambda x: x['date'])
        
        # Aggregate player stats across all games
        player_stats = defaultdict(lambda: {
            'player_id': '',
            'player_name': '',
            'jersey': '',
            'position': '',
            'games_played': 0,
            'total_points': 0,
            'total_rebounds': 0,
            'total_assists': 0,
            'total_steals': 0,
            'total_blocks': 0,
            'total_turnovers': 0,
            'total_fouls': 0,
            'total_minutes': 0,
            'total_fg_made': 0,
            'total_fg_attempted': 0,
            'total_3pt_made': 0,
            'total_3pt_attempted': 0,
            'total_ft_made': 0,
            'total_ft_attempted': 0,
            'game_highs': {
                'points': 0,
                'rebounds': 0,
                'assists': 0
            },
            'game_log': []  # NEW: track individual games
        })
        
        # Fetch each game's metadata and aggregate
        for game_info in completed_games:
            game_id = game_info['game_id']
            
            game_response = table.get_item(
                Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
            )
            
            game_data = game_response.get('Item')
            if not game_data:
                continue
            
            iowa_players = game_data.get('player_stats', {}).get('iowa', [])
            game_date = game_info['date'].split('T')[0] if game_info['date'] else ''
            game_result = 'W' if game_info['iowa_won'] else 'L'
            
            for player in iowa_players:
                pid = player.get('player_id', '')
                if not pid:
                    continue
                
                stats = player_stats[pid]
                
                # Set player info (first occurrence)
                if not stats['player_id']:
                    stats['player_id'] = pid
                    stats['player_name'] = player.get('player_name', '')
                    stats['jersey'] = player.get('jersey', '')
                    stats['position'] = player.get('position', '')
                
                # Parse minutes (could be "25" or "25:30")
                minutes_str = str(player.get('minutes', '0'))
                try:
                    if ':' in minutes_str:
                        mins, secs = minutes_str.split(':')
                        minutes = int(mins) + int(secs) / 60
                    else:
                        minutes = int(minutes_str)
                except (ValueError, TypeError):
                    minutes = 0
                
                # Get counting stats
                points = int(player.get('points', 0)) if player.get('points') else 0
                rebounds = int(player.get('rebounds', 0)) if player.get('rebounds') else 0
                assists = int(player.get('assists', 0)) if player.get('assists') else 0
                steals = int(player.get('steals', 0)) if player.get('steals') else 0
                blocks = int(player.get('blocks', 0)) if player.get('blocks') else 0
                turnovers = int(player.get('turnovers', 0)) if player.get('turnovers') else 0
                fouls = int(player.get('fouls', 0)) if player.get('fouls') else 0
                
                # Parse shooting stats
                fg = player.get('field_goals', '0-0')
                fg_made, fg_att = 0, 0
                if isinstance(fg, str) and '-' in fg:
                    parts = fg.split('-')
                    fg_made = int(parts[0]) if parts[0] else 0
                    fg_att = int(parts[1]) if parts[1] else 0
                
                three = player.get('three_pointers', '0-0')
                three_made, three_att = 0, 0
                if isinstance(three, str) and '-' in three:
                    parts = three.split('-')
                    three_made = int(parts[0]) if parts[0] else 0
                    three_att = int(parts[1]) if parts[1] else 0
                
                ft = player.get('free_throws', '0-0')
                ft_made, ft_att = 0, 0
                if isinstance(ft, str) and '-' in ft:
                    parts = ft.split('-')
                    ft_made = int(parts[0]) if parts[0] else 0
                    ft_att = int(parts[1]) if parts[1] else 0
                
                # Only count if player actually played
                if minutes > 0:
                    stats['games_played'] += 1
                    stats['total_minutes'] += minutes
                    
                    # Add to game log
                    stats['game_log'].append({
                        'game_id': game_id,
                        'date': game_date,
                        'opponent': game_info['opponent'],
                        'result': game_result,
                        'score': f"{game_info['iowa_score']}-{game_info['opponent_score']}",
                        'minutes': round(minutes),
                        'points': points,
                        'rebounds': rebounds,
                        'assists': assists,
                        'steals': steals,
                        'blocks': blocks,
                        'turnovers': turnovers,
                        'fouls': fouls,
                        'fg': fg,
                        'three_pt': three,
                        'ft': ft,
                    })
                
                # Aggregate totals
                stats['total_points'] += points
                stats['total_rebounds'] += rebounds
                stats['total_assists'] += assists
                stats['total_steals'] += steals
                stats['total_blocks'] += blocks
                stats['total_turnovers'] += turnovers
                stats['total_fouls'] += fouls
                stats['total_fg_made'] += fg_made
                stats['total_fg_attempted'] += fg_att
                stats['total_3pt_made'] += three_made
                stats['total_3pt_attempted'] += three_att
                stats['total_ft_made'] += ft_made
                stats['total_ft_attempted'] += ft_att
                
                # Track game highs
                if points > stats['game_highs']['points']:
                    stats['game_highs']['points'] = points
                if rebounds > stats['game_highs']['rebounds']:
                    stats['game_highs']['rebounds'] = rebounds
                if assists > stats['game_highs']['assists']:
                    stats['game_highs']['assists'] = assists
        
        # Calculate averages and format response
        players_list = []
        for pid, stats in player_stats.items():
            if stats['games_played'] == 0:
                continue
            
            gp = stats['games_played']
            
            # Calculate percentages
            fg_pct = (stats['total_fg_made'] / stats['total_fg_attempted'] * 100) if stats['total_fg_attempted'] > 0 else 0
            three_pct = (stats['total_3pt_made'] / stats['total_3pt_attempted'] * 100) if stats['total_3pt_attempted'] > 0 else 0
            ft_pct = (stats['total_ft_made'] / stats['total_ft_attempted'] * 100) if stats['total_ft_attempted'] > 0 else 0
            
            players_list.append({
                'player_id': stats['player_id'],
                'player_name': stats['player_name'],
                'jersey': stats['jersey'],
                'position': stats['position'],
                'games_played': gp,
                'minutes_per_game': round(stats['total_minutes'] / gp, 1),
                'points_per_game': round(stats['total_points'] / gp, 1),
                'rebounds_per_game': round(stats['total_rebounds'] / gp, 1),
                'assists_per_game': round(stats['total_assists'] / gp, 1),
                'steals_per_game': round(stats['total_steals'] / gp, 1),
                'blocks_per_game': round(stats['total_blocks'] / gp, 1),
                'turnovers_per_game': round(stats['total_turnovers'] / gp, 1),
                'fouls_per_game': round(stats['total_fouls'] / gp, 1),
                'field_goal_pct': round(fg_pct, 1),
                'three_point_pct': round(three_pct, 1),
                'free_throw_pct': round(ft_pct, 1),
                'totals': {
                    'points': stats['total_points'],
                    'rebounds': stats['total_rebounds'],
                    'assists': stats['total_assists'],
                    'steals': stats['total_steals'],
                    'blocks': stats['total_blocks'],
                },
                'game_highs': stats['game_highs'],
                'game_log': stats['game_log'],  # Include game log
            })
        
        # Sort by points per game descending
        players_list.sort(key=lambda x: x['points_per_game'], reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'season': season,
                'player_count': len(players_list),
                'players': players_list,
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        }
