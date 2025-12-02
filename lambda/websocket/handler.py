import json
import os
import boto3
from boto3.dynamodb.conditions import Key

from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
apigateway_management_api = None

def handler(event, context):
    """
    WebSocket Lambda handler
    Routes: $connect, $disconnect, $default
    """
    
    route_key = event['requestContext']['routeKey']
    connection_id = event['requestContext']['connectionId']
    
    print(f"🔌 WebSocket route: {route_key}, connectionId: {connection_id}")
    
    if route_key == '$connect':
        return handle_connect(connection_id)
    elif route_key == '$disconnect':
        return handle_disconnect(connection_id)
    elif route_key == '$default':
        return handle_message(event, connection_id)
    else:
        return {'statusCode': 400, 'body': 'Unknown route'}


def handle_connect(connection_id):
    """Store new WebSocket connection"""
    try:
        table.put_item(
            Item={
                'PK': 'WS#CONNECTION',
                'SK': connection_id,
                'connectionId': connection_id,
                'connectedAt': datetime.utcnow().isoformat(),
                'gameId': None,  # Will be set when client subscribes
                'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hours
            }
        )
        print(f"✅ Stored connection: {connection_id}")
        return {'statusCode': 200, 'body': 'Connected'}
    except Exception as e:
        print(f"❌ Error storing connection: {str(e)}")
        return {'statusCode': 500, 'body': 'Failed to connect'}


def handle_disconnect(connection_id):
    """Remove WebSocket connection"""
    try:
        table.delete_item(
            Key={
                'PK': 'WS#CONNECTION',
                'SK': connection_id
            }
        )
        print(f"✅ Removed connection: {connection_id}")
        return {'statusCode': 200, 'body': 'Disconnected'}
    except Exception as e:
        print(f"❌ Error removing connection: {str(e)}")
        return {'statusCode': 500, 'body': 'Failed to disconnect'}

def send_to_connection(connection_id, data, event):
    """Send data to a specific WebSocket connection"""
    global apigateway_management_api
    
    if apigateway_management_api is None:
        # Initialize API Gateway Management API client
        domain_name = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        endpoint_url = f"https://{domain_name}/{stage}"
        
        apigateway_management_api = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )
    
    try:
        apigateway_management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8')
        )
        print(f"✅ Sent data to connection {connection_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to send to {connection_id}: {str(e)}")
        return False

def get_current_game_state(game_id):
    """Fetch current game state from DynamoDB"""
    try:
        # Get game metadata
        metadata_response = table.get_item(
            Key={'PK': game_id, 'SK': 'METADATA'}
        )
        
        # Get current score
        score_response = table.get_item(
            Key={'PK': game_id, 'SK': 'SCORE#CURRENT'}
        )
        
        game_state = {
            'type': 'game_state',
            'gameId': game_id,
        }
        
        # Add metadata if exists
        if 'Item' in metadata_response:
            metadata = metadata_response['Item']
            game_state['homeTeam'] = metadata.get('homeTeam')
            game_state['awayTeam'] = metadata.get('awayTeam')
            game_state['status'] = metadata.get('status')
            game_state['quarter'] = metadata.get('quarter')
        
        # Add score if exists
        if 'Item' in score_response:
            score = score_response['Item']
            game_state['homeScore'] = int(score.get('homeScore', 0))
            game_state['awayScore'] = int(score.get('awayScore', 0))
            game_state['gameClock'] = score.get('gameClock')
            game_state['lastUpdated'] = score.get('lastUpdated')
        
        print(f"✅ Retrieved game state for {game_id}")
        return game_state
        
    except Exception as e:
        print(f"❌ Error fetching game state: {str(e)}")
        return {'type': 'error', 'message': 'Game not found'}

def handle_message(event, connection_id):
    """Handle messages from client (e.g., subscribe to game)"""
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        print(f"📨 Message from {connection_id}: {action}")
        
        if action == 'subscribe':
            game_id = body.get('gameId')
            if not game_id:
                return {'statusCode': 400, 'body': 'Missing gameId'}
            
            # Update connection with game subscription
            table.update_item(
                Key={'PK': 'WS#CONNECTION', 'SK': connection_id},
                UpdateExpression='SET gameId = :gid, GSI1PK = :gid, GSI1SK = :cid',
                ExpressionAttributeValues={
                    ':gid': game_id,
                    ':cid': connection_id
                }
            )
            print(f"✅ {connection_id} subscribed to {game_id}")
            
            # Fetch current game state
            game_state = get_current_game_state(game_id)
            
            # Send game state back to client
            send_to_connection(connection_id, game_state, event)
            
            return {'statusCode': 200, 'body': 'Subscribed'}
        
        return {'statusCode': 400, 'body': 'Unknown action'}
        
    except Exception as e:
        print(f"❌ Error handling message: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}