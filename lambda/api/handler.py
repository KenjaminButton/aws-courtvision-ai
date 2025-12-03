import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# CORS headers
cors_headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,OPTIONS'
}

def decimal_to_number(obj):
    """Convert DynamoDB Decimal types to int/float"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    return obj


def get_todays_games():
    """Get recent games (handles timezone issues by checking today +/- 1 day)"""
    try:
        from datetime import timedelta
        
        # Check yesterday, today, and tomorrow to handle timezones
        base_date = datetime.now()
        
        all_games = []
        for offset in [-1, 0, 1]:
            check_date = (base_date + timedelta(days=offset)).strftime('%Y-%m-%d')
            
            response = table.query(
                IndexName='GSI1',
                KeyConditionExpression=Key('GSI1PK').eq(f'DATE#{check_date}')
            )
            
            for item in response.get('Items', []):
                if item.get('SK') == 'METADATA':
                    all_games.append({
                        'gameId': item['PK'],
                        'espnGameId': item.get('espnGameId'),
                        'homeTeam': item.get('homeTeam'),
                        'awayTeam': item.get('awayTeam'),
                        'status': item.get('status'),
                        'homeScore': int(item.get('homeScore', 0)),
                        'awayScore': int(item.get('awayScore', 0)),
                    })
        
        return all_games
        
    except Exception as e:
        print(f"❌ Error getting today's games: {str(e)}")
        return []


def get_game_by_espn_id(espn_game_id):
    """Get a single game by ESPN ID"""
    try:
        # Query GSI2 to find game by ESPN ID
        response = table.query(
            IndexName='GSI2',
            KeyConditionExpression=Key('espnGameId').eq(espn_game_id)
        )
        
        if not response.get('Items'):
            return None
        
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
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def get_win_prob_history(game_id):
    """Get all historical win probability records for a game"""
    try:
        # Query for all AI#WIN_PROB# items (excluding CURRENT)
        response = table.query(
            KeyConditionExpression=Key('PK').eq(game_id) & Key('SK').begins_with('AI#WIN_PROB#')
        )
        
        items = response.get('Items', [])
        
        # Filter out CURRENT, keep only timestamped records
        history = [
            item for item in items 
            if item['SK'] != 'AI#WIN_PROB#CURRENT'
        ]
        
        # Sort by timestamp (SK already has ISO format)
        history.sort(key=lambda x: x['SK'])
        
        print(f"✅ Found {len(history)} win prob history records")
        
        return history
        
    except Exception as e:
        print(f"❌ Error fetching win prob history: {str(e)}")
        return []


def handler(event, context):
    """
    REST API Lambda for game lookups
    Routes:
    - GET /games - Get today's games
    - GET /game/{espnGameId} - Get game by ESPN ID
    - GET /game/{espnGameId}/win-probability - Get win probability history
    """
    
    print(f"📡 API Request: {event['httpMethod']} {event['path']}")
    
    # Handle preflight OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    path = event.get('path', '')
    
    # Route: GET /games (today's games)
    if path == '/games':
        games = get_todays_games()
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(decimal_to_number({'games': games}))
        }
    
    # Route: GET /game/{espnGameId}/win-probability (win prob history)
    # Check this BEFORE the generic /game/{espnGameId} route
    if path.startswith('/game/') and path.endswith('/win-probability'):
        path_params = event.get('pathParameters', {})
        espn_game_id = path_params.get('espnGameId')
        
        if not espn_game_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing espnGameId'})
            }
        
        # First, get the game to find its PK
        game = get_game_by_espn_id(espn_game_id)
        if not game:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Game not found'})
            }
        
        game_id = game['gameId']
        
        # Get win probability history
        history = get_win_prob_history(game_id)
        
        # Format for frontend
        formatted = [
            {
                'timestamp': record['calculatedAt'],
                'homeWinProbability': float(record['homeWinProbability']),
                'awayWinProbability': float(record['awayWinProbability']),
                'homeScore': int(record.get('homeScore', 0)),
                'awayScore': int(record.get('awayScore', 0)),
                'quarter': int(record.get('quarter', 1))
            }
            for record in history
        ]
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(decimal_to_number({'history': formatted}))
        }
    
    # Route: GET /game/{espnGameId} (specific game)
    if path.startswith('/game/'):
        path_params = event.get('pathParameters', {})
        espn_game_id = path_params.get('espnGameId')
        
        if not espn_game_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing espnGameId'})
            }
        
        game = get_game_by_espn_id(espn_game_id)
        
        if not game:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Game not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(decimal_to_number(game))
        }
    
    # Unknown route
    return {
        'statusCode': 404,
        'headers': cors_headers,
        'body': json.dumps({'error': 'Not found'})
    }