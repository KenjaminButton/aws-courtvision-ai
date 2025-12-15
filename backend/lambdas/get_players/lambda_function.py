"""
CourtVision AI - Get Players Lambda
Returns aggregated player statistics for a season.

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
        
        game_ids = [
            item['game_id'] 
            for item in games_response.get('Items', [])
            if item.get('status_completed')
        ]
        
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
            }
        })
        
        # Fetch each game's metadata and aggregate
        for game_id in game_ids:
            game_response = table.get_item(
                Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
            )
            
            game_data = game_response.get('Item')
            if not game_data:
                continue
            
            iowa_players = game_data.get('player_stats', {}).get('iowa', [])
            
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
                
                # Only count if player actually played
                if minutes > 0:
                    stats['games_played'] += 1
                    stats['total_minutes'] += minutes
                
                # Aggregate counting stats
                points = int(player.get('points', 0)) if player.get('points') else 0
                rebounds = int(player.get('rebounds', 0)) if player.get('rebounds') else 0
                assists = int(player.get('assists', 0)) if player.get('assists') else 0
                
                stats['total_points'] += points
                stats['total_rebounds'] += rebounds
                stats['total_assists'] += assists
                stats['total_steals'] += int(player.get('steals', 0)) if player.get('steals') else 0
                stats['total_blocks'] += int(player.get('blocks', 0)) if player.get('blocks') else 0
                stats['total_turnovers'] += int(player.get('turnovers', 0)) if player.get('turnovers') else 0
                stats['total_fouls'] += int(player.get('fouls', 0)) if player.get('fouls') else 0
                
                # Parse shooting stats (format: "5-10")
                fg = player.get('field_goals', '0-0')
                if isinstance(fg, str) and '-' in fg:
                    made, att = fg.split('-')
                    stats['total_fg_made'] += int(made) if made else 0
                    stats['total_fg_attempted'] += int(att) if att else 0
                
                three = player.get('three_pointers', '0-0')
                if isinstance(three, str) and '-' in three:
                    made, att = three.split('-')
                    stats['total_3pt_made'] += int(made) if made else 0
                    stats['total_3pt_attempted'] += int(att) if att else 0
                
                ft = player.get('free_throws', '0-0')
                if isinstance(ft, str) and '-' in ft:
                    made, att = ft.split('-')
                    stats['total_ft_made'] += int(made) if made else 0
                    stats['total_ft_attempted'] += int(att) if att else 0
                
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
                'game_highs': stats['game_highs']
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