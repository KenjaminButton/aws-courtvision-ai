import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# WebSocket API endpoint from environment variable
WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_API_ENDPOINT', '')
apigateway = boto3.client('apigatewaymanagementapi', endpoint_url=WEBSOCKET_ENDPOINT)

# Environment variables
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'courtvision-games')
table = dynamodb.Table(TABLE_NAME)

def build_commentary_prompt(play_data, game_context):
    """
    Build optimized commentary prompt (Phase 3: reduced tokens)
    """
    player_stats = get_player_stats(play_data.get('playerId'), play_data.get('gameId'))
    
    prompt = f"""Generate play-by-play commentary:

Player: {play_data.get('playerName', 'Unknown')} ({play_data.get('team', 'Unknown')})
Action: {play_data.get('action', 'Unknown')} ({play_data.get('pointsScored', 0)} pts)
Score: {game_context['homeTeam']} {game_context['homeScore']} - {game_context['awayTeam']} {game_context['awayScore']}
Player stats: {player_stats.get('points', 0)} PTS this game
Quarter {game_context['quarter']}, {game_context['gameClock']}

Write 1-2 exciting sentences. No clichés. Be specific.

JSON format:
{{
  "commentary": "<your text>",
  "excitement": 0.XX
}}"""
    
    return prompt

def validate_commentary(commentary_text):
    """
    Reject commentary with hallucinated details
    """
    forbidden_words = [
        'freshman', 'sophomore', 'junior', 'senior',  # Class years
        'guard', 'forward', 'center',  # Positions (unless we provide them)
    ]
    
    commentary_lower = commentary_text.lower()
    
    for word in forbidden_words:
        if word in commentary_lower:
            print(f"⚠️ WARNING: Commentary contains '{word}' - possible hallucination")
            return False
    
    return True

def call_bedrock(prompt):
    """
    Call AWS Bedrock to generate commentary
    """
    try:
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 150,  # CHANGED: Reduced (Haiku is more concise)
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        print(f"✅ Bedrock response: {content[:100]}...")
        return json.loads(content)
    
    except Exception as e:
        print(f"❌ Bedrock error: {str(e)}")
        return None

def extract_play_from_stream(record):
    """
    Extract play data from DynamoDB Stream record
    """
    if record['eventName'] != 'INSERT':
        return None
    
    new_image = record['dynamodb']['NewImage']
    
    # Only process PLAY records that are scoring plays
    if not new_image.get('SK', {}).get('S', '').startswith('PLAY#'):
        return None
    
    if not new_image.get('scoringPlay', {}).get('BOOL'):
        return None
    
    # Extract play data
    play_data = {
        'gameId': new_image['PK']['S'],
        'playId': new_image.get('playId', {}).get('S', ''),
        'playerId': new_image.get('playerId', {}).get('S', ''),  # ADD THIS LINE
        'playerName': new_image.get('playerName', {}).get('S', 'Unknown'),
        'team': new_image.get('team', {}).get('S', 'Unknown'),
        'action': new_image.get('action', {}).get('S', 'Unknown'),
        'description': new_image.get('description', {}).get('S', ''),
        'pointsScored': int(new_image.get('pointsScored', {}).get('N', 0)),
        'timestamp': new_image.get('timestamp', {}).get('S', ''),
    }
    
    print(f"🏀 Scoring play detected: {play_data['playerName']} - {play_data['action']}")
    return play_data

def get_game_context(game_id):
    """
    Get current game state for context
    """
    try:
        # Get current score
        response = table.get_item(
            Key={'PK': game_id, 'SK': 'SCORE#CURRENT'}
        )
        
        score_data = response.get('Item', {})
        
        # Get game metadata
        metadata_response = table.get_item(
            Key={'PK': game_id, 'SK': 'METADATA'}
        )
        
        metadata = metadata_response.get('Item', {})
        
        context = {
            'homeTeam': metadata.get('homeTeam', 'Home'),
            'awayTeam': metadata.get('awayTeam', 'Away'),
            'homeScore': int(score_data.get('homeScore', 0)),
            'awayScore': int(score_data.get('awayScore', 0)),
            'quarter': int(score_data.get('quarter', 1)),
            'gameClock': score_data.get('gameClockDisplay', '10:00'),
            'recentContext': 'Game in progress'
        }
        return context
    
    except Exception as e:
        print(f"❌ Error getting game context: {str(e)}")
        return None

def get_player_stats(player_id, game_id):
    """
    Fetch player statistics for this game
    Returns stats dict or defaults if not found
    """
    try:
        response = table.get_item(
            Key={
                'PK': f"PLAYER#{player_id}",
                'SK': f"{game_id}#STATS"
            }
        )
        
        if 'Item' in response:
            stats = response['Item']
            print(f"📊 Player stats: {stats.get('playerName', 'Unknown')} - {stats.get('points', 0)} PTS, {stats.get('fgMade', 0)}-{stats.get('fgAttempted', 0)} FG")
            return stats
        else:
            # No stats yet (first play of game)
            print(f"📊 No stats found for player {player_id} - returning defaults")
            return {
                'points': 0,
                'fgMade': 0,
                'fgAttempted': 0,
                'threeMade': 0,
                'threeAttempted': 0,
                'fouls': 0
            }
    
    except Exception as e:
        print(f"❌ Error fetching player stats: {str(e)}")
        return {
            'points': 0,
            'fgMade': 0,
            'fgAttempted': 0,
            'threeMade': 0,
            'threeAttempted': 0,
            'fouls': 0
        }

def store_commentary(game_id, play_id, commentary_data):
    """
    Store commentary in DynamoDB
    """
    try:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        table.put_item(Item={
            'PK': game_id,
            'SK': f'AI#COMMENTARY#{timestamp}',
            'playId': play_id,
            'commentary': commentary_data['commentary'],
            'excitement': Decimal(str(commentary_data['excitement'])),
            'generatedAt': timestamp
        })
        
        print(f"✅ Commentary stored: {commentary_data['commentary'][:50]}...")
        return True
    
    except Exception as e:
        print(f"❌ Error storing commentary: {str(e)}")
        return False

def push_to_websocket(game_id, commentary_data):
    """
    Push commentary update to all connected WebSocket clients for this game
    """
    try:
        # Get all connections for this game
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(game_id)
        )
        
        connections = response.get('Items', [])
        print(f"📡 Found {len(connections)} WebSocket connections for {game_id}")
        
        if len(connections) == 0:
            print("⚠️ No active connections - skipping WebSocket push")
            return True
        
        # Prepare message
        message = {
            'type': 'commentary',
            'data': commentary_data
        }
        
        # Push to each connection
        stale_connections = []
        for conn in connections:
            connection_id = conn['SK'].replace('WS#CONNECTION#', '')
            
            try:
                apigateway.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(message)
                )
                print(f"✅ Pushed to connection {connection_id[:8]}...")
            
            except apigateway.exceptions.GoneException:
                print(f"🗑️ Stale connection {connection_id[:8]}... - marking for deletion")
                stale_connections.append(conn)
            
            except Exception as e:
                print(f"❌ Error pushing to {connection_id[:8]}...: {str(e)}")
        
        # Clean up stale connections
        for conn in stale_connections:
            table.delete_item(Key={'PK': conn['PK'], 'SK': conn['SK']})
        
        return True
    
    except Exception as e:
        print(f"❌ Error in WebSocket push: {str(e)}")
        return False

def handler(event, context):
    """
    Lambda handler - triggered by DynamoDB Streams when scoring play occurs
    """
    print(f"📥 Commentary Lambda triggered with {len(event.get('Records', []))} records")
    
    for record in event.get('Records', []):
        # Step 1: Extract play from DynamoDB Stream
        play_data = extract_play_from_stream(record)
        if not play_data:
            continue
        
        # Step 2: Get game context
        game_context = get_game_context(play_data['gameId'])
        if not game_context:
            continue
        
        # Step 3: Build prompt
        prompt = build_commentary_prompt(play_data, game_context)
        
        # Step 4: Call Bedrock
        commentary = call_bedrock(prompt)
        if not commentary:
            continue
        
        # Step 5: Validate commentary (THIS IS WHERE VALIDATION HAPPENS)
        if not validate_commentary(commentary['commentary']):
            print("❌ Rejecting hallucinated commentary")
            continue
        
        # Step 6: Store commentary
        store_commentary(play_data['gameId'], play_data['playId'], commentary)
        
        # Step 7: Push to WebSocket
        push_to_websocket(play_data['gameId'], commentary)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': f'Processed {len(event.get("Records", []))} records'})
    }