"""
CourtVision AI - Get Players Lambda
Returns aggregated player statistics for a season, including game logs, bios, and splits.

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

# Position corrections (ESPN has some positions wrong)
POSITION_OVERRIDES = {
    "5240175": "C",  # Ava Heiden - Center, not Guard
}

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def fetch_player_bios(player_ids, season):
    """Fetch bio data for a list of player IDs."""
    if not player_ids:
        return {}
    
    bios = {}
    
    for pid in player_ids:
        try:
            response = table.get_item(
                Key={
                    'pk': f'PLAYER#{pid}',
                    'sk': f'BIO#{season}'
                }
            )
            item = response.get('Item')
            if item:
                bios[pid] = {
                    'height': item.get('height', ''),
                    'hometown': item.get('hometown', ''),
                    'high_school': item.get('high_school', ''),
                    'previous_school': item.get('previous_school', ''),
                    'class_year': item.get('class_year', ''),
                    'major': item.get('major', ''),
                    'bio_summary': item.get('bio_summary', ''),
                    'accolades': item.get('accolades', []),
                }
        except Exception as e:
            print(f"Error fetching bio for player {pid}: {e}")
            continue
    
    return bios


def create_empty_split():
    """Create an empty split stats bucket."""
    return {
        'games': 0,
        'total_points': 0,
        'total_rebounds': 0,
        'total_assists': 0,
        'total_steals': 0,
        'total_blocks': 0,
        'total_minutes': 0,
        'total_fg_made': 0,
        'total_fg_attempted': 0,
        'total_3pt_made': 0,
        'total_3pt_attempted': 0,
        'total_ft_made': 0,
        'total_ft_attempted': 0,
    }


def calculate_split_averages(split):
    """Calculate averages and percentages for a split."""
    if split['games'] == 0:
        return {
            'games': 0,
            'ppg': 0,
            'rpg': 0,
            'apg': 0,
            'spg': 0,
            'bpg': 0,
            'mpg': 0,
            'fg_pct': 0,
            'three_pct': 0,
            'ft_pct': 0,
        }
    
    gp = split['games']
    fg_pct = (split['total_fg_made'] / split['total_fg_attempted'] * 100) if split['total_fg_attempted'] > 0 else 0
    three_pct = (split['total_3pt_made'] / split['total_3pt_attempted'] * 100) if split['total_3pt_attempted'] > 0 else 0
    ft_pct = (split['total_ft_made'] / split['total_ft_attempted'] * 100) if split['total_ft_attempted'] > 0 else 0
    
    return {
        'games': gp,
        'ppg': round(split['total_points'] / gp, 1),
        'rpg': round(split['total_rebounds'] / gp, 1),
        'apg': round(split['total_assists'] / gp, 1),
        'spg': round(split['total_steals'] / gp, 1),
        'bpg': round(split['total_blocks'] / gp, 1),
        'mpg': round(split['total_minutes'] / gp, 1),
        'fg_pct': round(fg_pct, 1),
        'three_pct': round(three_pct, 1),
        'ft_pct': round(ft_pct, 1),
    }


def handler(event, context):
    """Get aggregated player stats for a season."""
    try:
        params = event.get('queryStringParameters') or {}
        season = params.get('season', '2026')
        
        # Get all games for the season
        games_response = table.query(
            KeyConditionExpression=Key('pk').eq(f'SEASON#{season}')
        )
        
        # Build list of completed games with metadata from SEASON# records
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
        
        # Fetch GAME#METADATA for each game to get player_stats AND home_away/conference info
        games_metadata = {}
        for game_info in completed_games:
            game_id = game_info['game_id']
            game_response = table.get_item(
                Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
            )
            if game_response.get('Item'):
                games_metadata[game_id] = game_response['Item']
        
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
            'game_log': [],
            # Splits buckets
            'splits': {
                'home': create_empty_split(),
                'away': create_empty_split(),
                'conference': create_empty_split(),
                'non_conference': create_empty_split(),
            }
        })
        
        # Process each game
        for game_info in completed_games:
            game_id = game_info['game_id']
            game_data = games_metadata.get(game_id)
            if not game_data:
                continue
            
            iowa_players = game_data.get('player_stats', {}).get('iowa', [])
            game_date = game_info['date'].split('T')[0] if game_info['date'] else ''
            game_result = 'W' if game_info['iowa_won'] else 'L'
            
            # Get home/away and conference info from METADATA
            iowa_info = game_data.get('iowa', {})
            is_home = iowa_info.get('home_away', '').lower() == 'home'
            is_conference = game_data.get('conference_competition', False)
            
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
                    stats['position'] = POSITION_OVERRIDES.get(pid, player.get('position', ''))
                
                # Parse minutes
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
                    
                    # Add to game log with home/away and conference info
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
                        'is_home': is_home,
                        'is_conference': is_conference,
                    })
                    
                    # Update splits
                    split_key = 'home' if is_home else 'away'
                    conf_key = 'conference' if is_conference else 'non_conference'
                    
                    for key in [split_key, conf_key]:
                        split = stats['splits'][key]
                        split['games'] += 1
                        split['total_points'] += points
                        split['total_rebounds'] += rebounds
                        split['total_assists'] += assists
                        split['total_steals'] += steals
                        split['total_blocks'] += blocks
                        split['total_minutes'] += minutes
                        split['total_fg_made'] += fg_made
                        split['total_fg_attempted'] += fg_att
                        split['total_3pt_made'] += three_made
                        split['total_3pt_attempted'] += three_att
                        split['total_ft_made'] += ft_made
                        split['total_ft_attempted'] += ft_att
                
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
        
        # Fetch bios for all players
        player_ids = [pid for pid in player_stats.keys() if player_stats[pid]['games_played'] > 0]
        player_bios = fetch_player_bios(player_ids, season)
        
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
            
            # Calculate split averages
            splits_formatted = {
                'home': calculate_split_averages(stats['splits']['home']),
                'away': calculate_split_averages(stats['splits']['away']),
                'conference': calculate_split_averages(stats['splits']['conference']),
                'non_conference': calculate_split_averages(stats['splits']['non_conference']),
            }
            
            player_data = {
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
                'game_log': stats['game_log'],
                'splits': splits_formatted,
            }
            
            # Add bio if available
            if pid in player_bios:
                player_data['bio'] = player_bios[pid]
            
            players_list.append(player_data)
        
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
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        }
    