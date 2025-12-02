import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def decimal_to_number(obj):
    """Convert DynamoDB Decimal types to int/float"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    return obj

def handler(event, context):
    """
    REST API Lambda for game lookups
    Routes:
    - GET /game/{espnGameId} - Get game by ESPN ID
    """
    
    print(f"📡 API Request: {event['httpMethod']} {event['path']}")
    
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    # Handle preflight OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Extract ESPN game ID from path
    path_params = event.get('pathParameters', {})
    espn_game_id = path_params.get('espnGameId')
    
    if not espn_game_id:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Missing espnGameId'})
        }
    
    try:
        # Query GSI2 to find game by ESPN ID
        response = table.query(
            IndexName='GSI2',
            KeyConditionExpression=Key('espnGameId').eq(espn_game_id)
        )
        
        if not response.get('Items'):
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Game not found'})
            }
        
        # Get the METADATA item
        game_data = response['Items'][0]
        
        # Also get current score
        game_pk = game_data['PK']
        score_response = table.get_item(
            Key={'PK': game_pk, 'SK': 'SCORE#CURRENT'}
        )
        
        # Combine metadata and score
        result = {
            'gameId': game_pk,
            'espnGameId': espn_game_id,
            'homeTeam': game_data.get('homeTeam'),
            'awayTeam': game_data.get('awayTeam'),
            'homeTeamId': game_data.get('homeTeamId'),
            'awayTeamId': game_data.get('awayTeamId'),
            'status': game_data.get('status'),
            'venue': game_data.get('venue'),
            'startTime': game_data.get('startTime'),
        }
        
        # Add score if available
        if 'Item' in score_response:
            score = score_response['Item']
            result['homeScore'] = int(score.get('homeScore', 0))
            result['awayScore'] = int(score.get('awayScore', 0))
            result['quarter'] = score.get('quarter')
            result['gameClock'] = score.get('gameClock')
        
        print(f"✅ Found game: {result['homeTeam']} vs {result['awayTeam']}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(decimal_to_number(result))
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }