"""
CourtVision AI - Get Games Lambda
Returns list of all games for a season.
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


def handler(event, context):
    """List all games for a season."""
    try:
        params = event.get('queryStringParameters') or {}
        season = params.get('season', '2025')
        
        response = table.query(
            KeyConditionExpression=Key('pk').eq(f'SEASON#{season}')
        )
        
        items = response.get('Items', [])
        
        metadata = None
        games = []
        
        for item in items:
            if item.get('sk') == 'METADATA':
                metadata = {
                    'season_year': item.get('season_year'),
                    'total_games': item.get('total_games'),
                    'fetched_at': item.get('fetched_at'),
                }
            else:
                games.append({
                    'game_id': item.get('game_id'),
                    'date': item.get('date'),
                    'short_name': item.get('short_name'),
                    'season_type': item.get('season_type'),
                    'status_completed': item.get('status_completed'),
                    'iowa_score': item.get('iowa_score'),
                    'iowa_won': item.get('iowa_won'),
                    'opponent_abbrev': item.get('opponent_abbrev'),
                    'opponent_score': item.get('opponent_score'),
                    'tournament_round': item.get('tournament_round'),
                })
        
        games.sort(key=lambda x: x.get('date', ''))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'season': season,
                'metadata': metadata,
                'games': games,
                'count': len(games),
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