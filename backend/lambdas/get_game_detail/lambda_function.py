"""
CourtVision AI - Get Game Detail Lambda
Returns game metadata, boxscore, and detected patterns.

Path: /games/{gameId}
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'courtvision-games'))


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def fetch_patterns(game_id: str) -> list:
    """Fetch all patterns for a game."""
    patterns = []
    
    try:
        response = table.query(
            KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#')
        )
        
        for item in response.get('Items', []):
            pattern = {
                'pattern_type': item.get('pattern_type', ''),
                'team': item.get('team', ''),
                'team_id': item.get('team_id', ''),
                'is_iowa': item.get('is_iowa', False),
                'description': item.get('description', ''),
                'period': item.get('period', 1),
            }
            
            # Add type-specific fields
            if item.get('pattern_type') == 'scoring_run':
                pattern['points_for'] = item.get('points_for', 0)
                pattern['points_against'] = item.get('points_against', 0)
                pattern['start_sequence'] = item.get('start_sequence', 0)
                pattern['end_sequence'] = item.get('end_sequence', 0)
            elif item.get('pattern_type') == 'hot_streak':
                pattern['player_id'] = item.get('player_id', '')
                pattern['player_name'] = item.get('player_name', '')
                pattern['consecutive_makes'] = item.get('consecutive_makes', 0)
            
            patterns.append(pattern)
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                pattern = {
                    'pattern_type': item.get('pattern_type', ''),
                    'team': item.get('team', ''),
                    'team_id': item.get('team_id', ''),
                    'is_iowa': item.get('is_iowa', False),
                    'description': item.get('description', ''),
                    'period': item.get('period', 1),
                }
                if item.get('pattern_type') == 'scoring_run':
                    pattern['points_for'] = item.get('points_for', 0)
                    pattern['points_against'] = item.get('points_against', 0)
                elif item.get('pattern_type') == 'hot_streak':
                    pattern['player_id'] = item.get('player_id', '')
                    pattern['player_name'] = item.get('player_name', '')
                    pattern['consecutive_makes'] = item.get('consecutive_makes', 0)
                patterns.append(pattern)
                
    except Exception as e:
        print(f"Error fetching patterns: {e}")
    
    return patterns


def handler(event, context):
    """Get game details including patterns."""
    try:
        # Get game ID from path
        game_id = event.get('pathParameters', {}).get('gameId')
        
        if not game_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': 'Game ID is required'})
            }
        
        # Fetch game metadata
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
        )
        
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': 'Game not found'})
            }
        
        # Fetch patterns for this game
        patterns = fetch_patterns(game_id)
        
        # Build response - include patterns
        game_data = {
            'game_id': item.get('game_id', game_id),
            'season': item.get('season'),
            'season_type': item.get('season_type'),
            'date': item.get('date', ''),
            'status': item.get('status', 'Final'),
            'neutral_site': item.get('neutral_site', False),
            'conference_competition': item.get('conference_competition', False),
            'iowa': item.get('iowa', {}),
            'opponent': item.get('opponent', {}),
            'venue': item.get('venue', {}),
            'boxscore': item.get('boxscore', {}),
            'player_stats': item.get('player_stats', {}),
            'play_count': item.get('play_count', '0'),
            # Add patterns!
            'patterns': patterns,
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(game_data, cls=DecimalEncoder)
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
