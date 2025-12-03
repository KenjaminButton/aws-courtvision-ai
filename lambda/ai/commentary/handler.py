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
    Build the commentary prompt using our tested format from Day 27
    """
    prompt = f"""You are an enthusiastic women's college basketball commentator. Generate exciting play-by-play commentary for this event.

Play Details:
- Player: {play_data.get('playerName', 'Unknown')} ({play_data.get('team', 'Unknown')})
- Action: {play_data.get('action', 'Unknown')}
- Description: {play_data.get('description', '')}
- Points (if scoring): {play_data.get('pointsScored', 0)}
- Current Score: {game_context['homeTeam']} {game_context['homeScore']} - {game_context['awayTeam']} {game_context['awayScore']}

Game Context:
- Quarter: {game_context['quarter']}, Time: {game_context['gameClock']}
- Player's Game Stats: {game_context.get('playerPoints', 0)} PTS, {game_context.get('playerRebounds', 0)} REB, {game_context.get('playerAssists', 0)} AST
- Recent Context: {game_context.get('recentContext', 'Game in progress')}

CRITICAL RULES:
1. MAXIMUM 2 sentences. No exceptions.
2. DO NOT mention player position (guard/forward/center) or class year (freshman/sophomore/junior/senior). These are NOT provided. Simply use the player's name.
3. DO NOT use clichés: "ice water in veins", "nothing but net", "from downtown", "on fire", "lights out"
4. Only mention facts explicitly provided in the data above
5. Match excitement to play significance (routine basket = 0.3-0.5, clutch shot = 0.7-0.9)

Generate natural, exciting commentary that sounds like a professional broadcaster.

Respond in JSON format:
{{
  "commentary": "<your commentary>",
  "excitement": <float 0-1>
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
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 300,
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
        
        return {
            'homeTeam': metadata.get('homeTeam', 'Home'),
            'awayTeam': metadata.get('awayTeam', 'Away'),
            'homeScore': int(score_data.get('homeScore', 0)),
            'awayScore': int(score_data.get('awayScore', 0)),
            'quarter': int(score_data.get('quarter', 1)),
            'gameClock': score_data.get('gameClockDisplay', '10:00'),
            'playerPoints': 0,  # TODO: Get player stats in future
            'playerRebounds': 0,
            'playerAssists': 0,
            'recentContext': 'Game in progress'
        }
    
    except Exception as e:
        print(f"❌ Error getting game context: {str(e)}")
        return None

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