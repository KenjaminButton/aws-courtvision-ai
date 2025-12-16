"""
CourtVision AI - Get Plays Lambda
Returns play-by-play data for a game.

Path params:
  - gameId: ESPN game ID (e.g., 401713556)

Query params:
  - period (optional): Filter by period number (1, 2, 3, 4)
  - scoring_only (optional): If 'true', return only scoring plays
  - limit (optional): Max number of plays to return
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


def deduplicate_plays(plays):
    """
    Remove duplicate plays based on period + clock + text.
    Keeps the first occurrence of each unique play.
    """
    seen = set()
    unique_plays = []
    
    for play in plays:
        # Create a unique key from play identifiers
        # Using period, clock, and text since these should be unique per play
        key = (
            play.get('period', ''),
            play.get('clock', ''),
            play.get('text', ''),
        )
        
        if key not in seen:
            seen.add(key)
            unique_plays.append(play)
    
    return unique_plays


def handler(event, context):
    """Get play-by-play for a game."""
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
                'body': json.dumps({'error': 'gameId is required'})
            }
        
        # Get query parameters
        params = event.get('queryStringParameters') or {}
        period_filter = params.get('period')
        scoring_only = params.get('scoring_only', '').lower() == 'true'
        limit = params.get('limit')
        
        # Query all plays for the game
        response = table.query(
            KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PLAY#')
        )
        
        plays = response.get('Items', [])
        
        if not plays:
            # Check if game exists
            game_check = table.get_item(
                Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
            )
            if not game_check.get('Item'):
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                    'body': json.dumps({'error': f'Game {game_id} not found'})
                }
        
        # Clean up plays (remove DynamoDB keys)
        cleaned_plays = []
        for play in plays:
            play.pop('pk', None)
            play.pop('sk', None)
            play.pop('entity_type', None)
            cleaned_plays.append(play)
        
        # Deduplicate plays
        cleaned_plays = deduplicate_plays(cleaned_plays)
        
        # Apply filters
        if period_filter:
            try:
                period_num = int(period_filter)
                cleaned_plays = [p for p in cleaned_plays if p.get('period') == period_num]
            except ValueError:
                pass
        
        if scoring_only:
            cleaned_plays = [p for p in cleaned_plays if p.get('scoring_play')]
        
        # Sort by sequence
        cleaned_plays.sort(key=lambda x: x.get('sequence', 0))
        
        # Apply limit
        if limit:
            try:
                cleaned_plays = cleaned_plays[:int(limit)]
            except ValueError:
                pass
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'game_id': game_id,
                'plays': cleaned_plays,
                'count': len(cleaned_plays),
                'filters': {
                    'period': period_filter,
                    'scoring_only': scoring_only,
                    'limit': limit,
                }
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