import json
import os
import boto3
from decimal import Decimal

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_ENDPOINT')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)
apigateway = boto3.client('apigatewaymanagementapi', endpoint_url=WEBSOCKET_ENDPOINT)


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def get_connections_for_game(game_id):
    """Get all WebSocket connections subscribed to a game"""
    try:
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :gid',
            ExpressionAttributeValues={':gid': game_id}  # <-- FIXED: game_id already has GAME# prefix
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"❌ Error fetching connections: {str(e)}")
        return []


def send_to_connection(connection_id, data):
    """Send data to a specific WebSocket connection"""
    try:
        apigateway.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data, default=decimal_to_float).encode('utf-8')
        )
        return True
    except apigateway.exceptions.GoneException:
        print(f"🗑️ Connection {connection_id} is stale, removing...")
        delete_connection(connection_id)
        return False
    except Exception as e:
        print(f"❌ Error sending to {connection_id}: {str(e)}")
        return False


def delete_connection(connection_id):
    """Remove stale connection from DynamoDB"""
    try:
        table.delete_item(
            Key={'PK': 'WS#CONNECTION', 'SK': connection_id}
        )
    except Exception as e:
        print(f"❌ Error deleting connection: {str(e)}")


def handler(event, context):
    """
    Push Lambda - sends updates to WebSocket clients
    Triggered by DynamoDB Streams
    """
    try:
        print("📤 Push Lambda started")
        print(f"Received {len(event['Records'])} DynamoDB Stream records")
        
        for record in event['Records']:
            # Only process INSERT and MODIFY events
            if record['eventName'] not in ['INSERT', 'MODIFY']:
                continue
            
            new_image = record['dynamodb'].get('NewImage', {})
            pk = new_image.get('PK', {}).get('S', '')
            sk = new_image.get('SK', {}).get('S', '')
            
            # Extract game ID from PK
            if not pk.startswith('GAME#'):
                continue
            
            game_id = pk  # Full game ID
            
            # Handle Score Updates
            if sk == 'SCORE#CURRENT':
                print(f"📊 Score update for {game_id}")
                
                score_data = {
                    'type': 'score',
                    'gameId': game_id,
                    'homeScore': int(new_image.get('homeScore', {}).get('N', 0)),
                    'awayScore': int(new_image.get('awayScore', {}).get('N', 0)),
                    'quarter': int(new_image.get('quarter', {}).get('N', 1)),
                    'gameClock': new_image.get('gameClock', {}).get('S', ''),
                }
                
                # Get connections and push
                connections = get_connections_for_game(game_id)
                for conn in connections:
                    send_to_connection(conn['SK'], score_data)
            
            # Handle Win Probability Updates
            if sk == 'AI#WIN_PROB#CURRENT':
                print(f"🎯 Win probability update for {game_id}")
                
                win_prob_data = {
                    'type': 'win_probability',
                    'gameId': game_id,
                    'homeProbability': float(new_image.get('homeWinProbability', {}).get('N', 0.5)),
                    'awayProbability': float(new_image.get('awayWinProbability', {}).get('N', 0.5)),
                    'reasoning': new_image.get('reasoning', {}).get('S', ''),
                    'calculatedAt': new_image.get('calculatedAt', {}).get('S', ''),
                }
                
                # Get connections and push
                connections = get_connections_for_game(game_id)
                pushed_count = 0
                for conn in connections:
                    if send_to_connection(conn['SK'], win_prob_data):
                        pushed_count += 1
                
                print(f"✅ Pushed win probability to {pushed_count} clients")
        
        return {'statusCode': 200, 'body': 'Updates pushed'}
        
    except Exception as e:
        print(f"❌ Error in Push Lambda: {str(e)}")
        raise