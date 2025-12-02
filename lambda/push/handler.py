import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# API Gateway Management API client (initialized per connection)
apigateway_clients = {}

def get_apigateway_client(endpoint_url):
    """Get or create API Gateway Management API client"""
    if endpoint_url not in apigateway_clients:
        apigateway_clients[endpoint_url] = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint_url
        )
    return apigateway_clients[endpoint_url]


def handler(event, context):
    """
    Triggered by DynamoDB Streams
    Pushes updates to WebSocket clients subscribed to the game
    """
    
    print(f"🔔 Push Lambda triggered with {len(event['Records'])} records")
    
    for record in event['Records']:
        # Only process INSERT and MODIFY events
        if record['eventName'] not in ['INSERT', 'MODIFY']:
            continue
        
        # Get the new item
        new_image = record['dynamodb'].get('NewImage', {})
        pk = new_image.get('PK', {}).get('S', '')
        sk = new_image.get('SK', {}).get('S', '')
        
        print(f"📝 Processing: PK={pk}, SK={sk}")
        
        # Only push updates for score changes
        if not pk.startswith('GAME#') or sk != 'SCORE#CURRENT':
            continue
        
        game_id = pk
        
        # Extract score data
        update_data = {
            'type': 'score_update',
            'gameId': game_id,
            'homeScore': int(new_image.get('homeScore', {}).get('N', 0)),
            'awayScore': int(new_image.get('awayScore', {}).get('N', 0)),
            'quarter': new_image.get('quarter', {}).get('N'),
            'gameClock': new_image.get('gameClock', {}).get('S', ''),
            'lastUpdated': new_image.get('lastUpdated', {}).get('S', '')
        }
        
        print(f"🏀 Score update: {update_data['homeScore']}-{update_data['awayScore']}")
        
        # Find all connections for this game
        connections = get_game_connections(game_id)
        print(f"👥 Found {len(connections)} connections for {game_id}")
        
        # Push to all connections
        for connection in connections:
            connection_id = connection['connectionId']
            success = push_to_connection(connection_id, update_data)
            
            # If connection is stale (410 Gone), delete it
            if not success:
                delete_stale_connection(connection_id)
    
    return {'statusCode': 200}


def get_game_connections(game_id):
    """Query GSI1 to find all connections for a game"""
    try:
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(game_id)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"❌ Error querying connections: {str(e)}")
        return []


def push_to_connection(connection_id, data):
    """Push data to a WebSocket connection"""
    try:
        # Get endpoint from environment variable
        websocket_endpoint = os.environ['WEBSOCKET_ENDPOINT']
        
        client = get_apigateway_client(websocket_endpoint)
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8')
        )
        
        print(f"✅ Pushed to {connection_id}")
        return True
        
    except client.exceptions.GoneException:
        print(f"⚠️ Connection {connection_id} is gone (stale)")
        return False
    except Exception as e:
        print(f"❌ Failed to push to {connection_id}: {str(e)}")
        return False


def delete_stale_connection(connection_id):
    """Remove stale connection from DynamoDB"""
    try:
        table.delete_item(
            Key={
                'PK': 'WS#CONNECTION',
                'SK': connection_id
            }
        )
        print(f"🗑️ Deleted stale connection: {connection_id}")
    except Exception as e:
        print(f"❌ Error deleting connection: {str(e)}")