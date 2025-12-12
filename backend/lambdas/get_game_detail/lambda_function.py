"""
CourtVision AI - Get Game Detail Lambda
Returns game metadata, boxscore, and player stats for a single game.

Path params:
  - gameId: ESPN game ID (e.g., 401713556)
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
    """Get details for a single game."""
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
        
        # Get game metadata
        response = table.get_item(
            Key={
                'pk': f'GAME#{game_id}',
                'sk': 'METADATA'
            }
        )
        
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': f'Game {game_id} not found'})
            }
        
        # Remove DynamoDB keys from response
        item.pop('pk', None)
        item.pop('sk', None)
        item.pop('entity_type', None)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(item, cls=DecimalEncoder)
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