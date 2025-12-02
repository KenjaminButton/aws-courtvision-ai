import json
import base64
import os
from datetime import datetime
import boto3

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def update_current_score(play):
    """
    Update the current score for a game in DynamoDB
    
    Args:
        play: Dictionary containing play data with homeScore, awayScore, etc.
    """
    try:
        table.update_item(
            Key={
                'PK': play['PK'],
                'SK': 'SCORE#CURRENT'
            },
            UpdateExpression='SET homeScore = :h, awayScore = :a, #q = :q, gameClock = :gc, lastUpdated = :t',
            ExpressionAttributeNames={
                '#q': 'quarter'  # 'quarter' is a reserved word in DynamoDB
            },
            ExpressionAttributeValues={
                ':h': play.get('homeScore', 0),
                ':a': play.get('awayScore', 0),
                ':q': play.get('quarter', 0),
                ':gc': play.get('gameClock', ''),
                ':t': play.get('timestamp', datetime.now().isoformat())
            }
        )
        print(f"✅ Updated score: {play['PK']} - {play.get('homeScore', 0)}-{play.get('awayScore', 0)}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating score: {str(e)}")
        return False

def store_play(play):
    """
    Store an individual play in DynamoDB
    
    Args:
        play: Dictionary containing complete play data
    """
    try:
        table.put_item(Item=play)
        return True
        
    except Exception as e:
        print(f"❌ Error storing play {play.get('playId')}: {str(e)}")
        return False

def update_player_stats(play):
    """
    Update player statistics in DynamoDB
    
    Args:
        play: Dictionary containing play data with playerId, scoringPlay, etc.
    """
    # Skip if no player ID
    if 'playerId' not in play:
        return False
    
    try:
        player_key = {
            'PK': f"PLAYER#{play['playerId']}",
            'SK': play['PK']  # Game ID as sort key
        }
        
        # Build update expression based on play type
        update_parts = []
        attr_values = {}
        
        # Track points for scoring plays
        if play.get('scoringPlay') and 'pointsScored' in play:
            update_parts.append('points :p')
            attr_values[':p'] = play['pointsScored']
        
        # If no stats to update, skip
        if not update_parts:
            return True
        
        # Update player stats
        table.update_item(
            Key=player_key,
            UpdateExpression=f'ADD {", ".join(update_parts)}',
            ExpressionAttributeValues=attr_values
        )
        
        print(f"✅ Updated stats for player {play['playerId']}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating player stats: {str(e)}")
        return False

def handler(event, context):
    """
    Processing Lambda - triggered by Kinesis stream
    
    Receives play-by-play data from Kinesis, processes it,
    and writes to DynamoDB.
    """
    try:
        print("🏀 CourtVision Processing Lambda started")
        print(f"Received {len(event['Records'])} records from Kinesis")
        
        processed_count = 0
        
        for record in event['Records']:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record['kinesis']['data'])
            play_data = json.loads(payload)
            
            # Update current score in DynamoDB
            update_current_score(play_data)
            
            # Store the individual play
            store_play(play_data)
            
            # Update player statistics
            update_player_stats(play_data)
            
            processed_count += 1
            
        print(f"✅ Successfully processed {processed_count} plays")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {processed_count} plays')
        }
        
    except Exception as e:
        print(f"❌ Error processing Kinesis records: {str(e)}")
        raise