import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

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
                UpdateExpression='SET gameId = :gid',
                ExpressionAttributeValues={':gid': game_id}
            )
            print(f"✅ {connection_id} subscribed to {game_id}")
            return {'statusCode': 200, 'body': 'Subscribed'}
        
        return {'statusCode': 400, 'body': 'Unknown action'}
        
    except Exception as e:
        print(f"❌ Error handling message: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}