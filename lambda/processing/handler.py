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

def calculate_stats_delta(play):
    """
    Calculate stats delta for a single play
    Returns dict with stat increments
    """
    stats_delta = {
        'points': 0,
        'fgMade': 0,
        'fgAttempted': 0,
        'threeMade': 0,
        'threeAttempted': 0,
        'fouls': 0
    }
    
    # Get play details
    text = play.get('text', '').lower()
    play_type = play.get('playType', '').lower()
    scoring_play = play.get('scoringPlay', False)
    points_scored = play.get('pointsScored', 0)
    
    # Detect play type from text and playType
    is_three = 'three' in text or '3pt' in text or 'three point' in text
    is_free_throw = 'free throw' in text or 'free' in play_type
    is_foul = 'foul' in text
    
    # Handle scoring plays
    if scoring_play and points_scored > 0:
        stats_delta['points'] = points_scored
        
        # Three-pointer made
        if is_three:
            stats_delta['fgMade'] = 1
            stats_delta['fgAttempted'] = 1
            stats_delta['threeMade'] = 1
            stats_delta['threeAttempted'] = 1
        
        # Two-pointer made (not three, not free throw)
        elif not is_free_throw:
            stats_delta['fgMade'] = 1
            stats_delta['fgAttempted'] = 1
        
        # Free throw made (points only, no FG impact)
        # else: points already added, no FG stats
    
    # Handle missed shots (non-scoring but has shot attempt)
    # Handle missed shots (non-scoring but has shot attempt)
    elif not scoring_play:
        if 'miss' in text or 'block' in text:
            if is_three:
                stats_delta['fgAttempted'] = 1
                stats_delta['threeAttempted'] = 1
            elif not is_free_throw:
                stats_delta['fgAttempted'] = 1
    
    # Handle fouls
    if is_foul:
        stats_delta['fouls'] = 1
    
    return stats_delta

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

def play_already_processed(play):
    """
    Check if a play has already been stored in DynamoDB
    
    Args:
        play: Dictionary containing play data with PK and SK
    
    Returns:
        bool: True if play exists, False if new
    """
    try:
        response = table.get_item(
            Key={'PK': play['PK'], 'SK': play['SK']}
        )
        return 'Item' in response
    except Exception as e:
        print(f"⚠️ Error checking play existence: {str(e)}")
        return False  # If error, assume new play

def update_player_stats(play):
    """
    Update player statistics in DynamoDB using calculated stats delta
    
    Args:
        play: Dictionary containing play data with playerId, scoringPlay, etc.
    """
    # Skip if no player ID
    if 'playerId' not in play:
        return False
    
    try:
        # Calculate stats delta for this play
        stats_delta = calculate_stats_delta(play)
        
        # Skip if no stats to update (all zeros)
        if all(value == 0 for value in stats_delta.values()):
            return True
        
        player_key = {
            'PK': f"PLAYER#{play['playerId']}",
            'SK': f"{play['PK']}#STATS"  # Updated SK pattern
        }
        
        # Build update expression
        update_parts = []
        attr_values = {}
        attr_names = {}
        
        if stats_delta['points'] > 0:
            update_parts.append('points :pts')
            attr_values[':pts'] = stats_delta['points']
        
        if stats_delta['fgMade'] > 0:
            update_parts.append('fgMade :fgm')
            attr_values[':fgm'] = stats_delta['fgMade']
        
        if stats_delta['fgAttempted'] > 0:
            update_parts.append('fgAttempted :fga')
            attr_values[':fga'] = stats_delta['fgAttempted']
        
        if stats_delta['threeMade'] > 0:
            update_parts.append('threeMade :tm')
            attr_values[':tm'] = stats_delta['threeMade']
        
        if stats_delta['threeAttempted'] > 0:
            update_parts.append('threeAttempted :ta')
            attr_values[':ta'] = stats_delta['threeAttempted']
        
        if stats_delta['fouls'] > 0:
            update_parts.append('fouls :f')
            attr_values[':f'] = stats_delta['fouls']
        
        # Add metadata
        attr_values[':t'] = datetime.now().isoformat()
        attr_values[':pid'] = play['playerId']
        attr_values[':pname'] = play.get('playerName', 'Unknown')
        attr_values[':team'] = play.get('team', 'Unknown')
        attr_values[':gid'] = play['PK']
        
        # Update player stats (ADD will create if doesn't exist)
        table.update_item(
            Key=player_key,
            UpdateExpression=f'ADD {", ".join(update_parts)} SET lastUpdated = :t, playerId = :pid, playerName = :pname, team = :team, gameId = :gid',
            ExpressionAttributeValues=attr_values
        )
        
        print(f"✅ Updated stats for {play.get('playerName', 'Unknown')}: +{stats_delta['points']} pts, {stats_delta['fgMade']}/{stats_delta['fgAttempted']} FG, {stats_delta['threeMade']}/{stats_delta['threeAttempted']} 3PT, +{stats_delta['fouls']} fouls")
        return True
        
    except Exception as e:
        print(f"⚠️ Error updating player stats (non-critical): {str(e)}")
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
            
            # Check if play already processed (deduplication)
            if play_already_processed(play_data):
                print(f"⏭️  Skipping already processed play: {play_data.get('playId')}")
                continue
            
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
