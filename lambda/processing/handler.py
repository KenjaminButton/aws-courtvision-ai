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
        
        # *** NEW: Determine actual team name from game metadata ***
        team_name = "Unknown"
        try:
            metadata_response = table.get_item(
                Key={'PK': play['PK'], 'SK': 'METADATA'}
            )
            metadata = metadata_response.get('Item', {})
            
            play_team_id = play.get('teamId', '')
            home_team_id = str(metadata.get('homeTeamId', ''))
            away_team_id = str(metadata.get('awayTeamId', ''))
            
            if play_team_id == home_team_id:
                team_name = metadata.get('homeTeam', 'Unknown')
            elif play_team_id == away_team_id:
                team_name = metadata.get('awayTeam', 'Unknown')
            
            print(f"🔍 Team mapping: play team ID {play_team_id} → {team_name}")
        except Exception as e:
            print(f"⚠️ Could not determine team name: {str(e)}")
        
        player_key = {
            'PK': f"PLAYER#{play['playerId']}",
            'SK': f"{play['PK']}#STATS"
        }
        
        # Build update expression
        update_parts = []
        attr_values = {}
        
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
        attr_values[':team'] = team_name  # *** CHANGED: Use resolved team name ***
        attr_values[':gid'] = play['PK']
        
        # Update player stats
        table.update_item(
            Key=player_key,
            UpdateExpression=f'ADD {", ".join(update_parts)} SET lastUpdated = :t, playerId = :pid, playerName = :pname, team = :team, gameId = :gid',
            ExpressionAttributeValues=attr_values
        )
        
        print(f"✅ Updated stats for {play.get('playerName', 'Unknown')} ({team_name}): +{stats_delta['points']} pts, {stats_delta['fgMade']}/{stats_delta['fgAttempted']} FG, {stats_delta['threeMade']}/{stats_delta['threeAttempted']} 3PT, +{stats_delta['fouls']} fouls")
        return True
        
    except Exception as e:
        print(f"⚠️ Error updating player stats (non-critical): {str(e)}")
        return False

def detect_scoring_run(recent_plays, home_team, away_team):
    """
    Detect scoring runs (8+ unanswered points or 10-2 differential)
    
    Args:
        recent_plays: List of recent play dicts (last 15 plays)
        home_team: Home team name
        away_team: Away team name
    
    Returns:
        dict with pattern info or None if no run detected
    """
    # Look at last 15 plays for scoring patterns
    home_points = 0
    away_points = 0
    
    for play in recent_plays:
        if play.get('scoringPlay'):
            if play.get('team') == home_team:
                home_points += play.get('pointsScored', 0)
            elif play.get('team') == away_team:
                away_points += play.get('pointsScored', 0)
    
    # Check for scoring run (8+ unanswered or 10-2 differential)
    if home_points >= 10 and away_points <= 2:
        return {
            'type': 'scoring_run',
            'team': home_team,
            'points_for': home_points,
            'points_against': away_points,
            'description': f"{home_team} on a {home_points}-{away_points} run"
        }
    elif away_points >= 10 and home_points <= 2:
        return {
            'type': 'scoring_run',
            'team': away_team,
            'points_for': away_points,
            'points_against': home_points,
            'description': f"{away_team} on a {away_points}-{home_points} run"
        }
    
    return None

def get_recent_plays(game_id, limit=15):
    """
    Query DynamoDB for the most recent plays in a game
    
    Args:
        game_id: Game PK (e.g., "GAME#2025-12-15#UCONN-STANFORD")
        limit: Number of recent plays to retrieve
    
    Returns:
        List of play dictionaries (newest first)
    """
    try:
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :play)',
            ExpressionAttributeValues={
                ':pk': game_id,
                ':play': 'PLAY#'
            },
            ScanIndexForward=False,  # Get newest first
            Limit=limit
        )
        
        plays = response.get('Items', [])
        print(f"📋 Retrieved {len(plays)} recent plays for pattern detection")
        return plays
        
    except Exception as e:
        print(f"⚠️ Error getting recent plays: {str(e)}")
        return []

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
            
            # *** NEW: Pattern Detection ***
            # Get recent plays for pattern analysis
            recent_plays = get_recent_plays(play_data['PK'], limit=15)
            
            # Get game metadata for team names
            try:
                metadata_response = table.get_item(
                    Key={'PK': play_data['PK'], 'SK': 'METADATA'}
                )
                metadata = metadata_response.get('Item', {})
                home_team = metadata.get('homeTeam', 'Home')
                away_team = metadata.get('awayTeam', 'Away')
                
                # Detect scoring run
                pattern = detect_scoring_run(recent_plays, home_team, away_team)
                
                if pattern:
                    print(f"🔥 Pattern detected: {pattern['description']}")
                    # TODO: Store pattern in DynamoDB (Step 3)
                
            except Exception as e:
                print(f"⚠️ Pattern detection error (non-critical): {str(e)}")
            
            processed_count += 1
            
        print(f"✅ Successfully processed {processed_count} plays")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {processed_count} plays')
        }
        
    except Exception as e:
        print(f"❌ Error processing Kinesis records: {str(e)}")
        raise
