import json
import boto3
import base64
from datetime import datetime

# Your existing config
KINESIS_STREAM = 'courtvision-plays'
kinesis = boto3.client('kinesis', region_name='us-east-1')

def parse_play_for_processing(play, game_id, home_team, away_team, home_team_id, away_team_id):
    """
    Transform ESPN play format to our Processing Lambda format
    """
    # Get team info (ESPN puts it directly in 'team' field)
    team_id = play.get('team', {}).get('id', '')
    team_name = None
    
    # Map team ID to team name
    if str(team_id) == str(home_team_id):
        team_name = home_team
    elif str(team_id) == str(away_team_id):
        team_name = away_team
    
    # Extract player name from text
    player_name = 'Unknown'
    play_text = play.get('text', '')

    # Exclude plays with no player (jumpballs, timeouts, etc.)
    exclude_keywords = ['jump ball', 'timeout', 'start game', 'end of', 'official', 'subbing']
    
    if play_text and not any(keyword in play_text.lower() for keyword in exclude_keywords):
        # Try common action patterns
        action_verbs = [' made ', ' missed ', ' misses ', ' makes ', 
                       ' Offensive Rebound', ' Defensive Rebound', ' Turnover',
                       ' Steal', ' Block', ' enters the game', ' goes to the bench']
        
        for verb in action_verbs:
            if verb in play_text:
                player_name = play_text.split(verb)[0].strip()
                break
        
        # If still Unknown, try period as delimiter (e.g., "Player Name.")
        if player_name == 'Unknown' and '.' in play_text:
            potential_name = play_text.split('.')[0].strip()
            # Basic validation: name should have at least 2 words and be < 40 chars
            if len(potential_name.split()) >= 2 and len(potential_name) < 40:
                player_name = potential_name
    
    # Get player ID
    player_id = ''
    participants = play.get('participants', [])
    if participants and 'athlete' in participants[0]:
        player_id = str(participants[0]['athlete'].get('id', ''))
    
    # Build our play format
    processed_play = {
        'PK': game_id,
        'SK': f"PLAY#{play.get('wallclock', datetime.now().isoformat())}#{play.get('sequenceNumber', '')}",
        'playId': play.get('id', ''),
        'timestamp': play.get('wallclock', datetime.now().isoformat()),
        'quarter': play.get('period', {}).get('number', 1),
        'gameClock': play.get('clock', {}).get('displayValue', '10:00'),
        'text': play_text,
        'description': play_text,  # Add description field
        'homeScore': play.get('homeScore', 0),
        'awayScore': play.get('awayScore', 0),
        'scoringPlay': play.get('scoringPlay', False) or play.get('scoreValue', 0) > 0,
        'pointsScored': play.get('scoreValue', 0),
        'teamId': team_id,
        'team': team_name if team_name else 'Unknown',
        'playerId': player_id,
        'playerName': player_name,
    }
    
    # Add play type
    play_type = play.get('type', {}).get('text', '').lower()
    processed_play['playType'] = play_type
    
    # Determine action from play type
    text_lower = play_text.lower()
    scored = play.get('scoreValue', 0) > 0
    
    if 'three point' in text_lower or '3pt' in play_type:
        processed_play['action'] = 'made_three_pointer' if scored else 'missed_three_pointer'
    elif 'layup' in play_type or 'dunk' in play_type:
        processed_play['action'] = 'made_layup' if scored else 'missed_layup'
    elif 'free throw' in play_type:
        processed_play['action'] = 'made_free_throw' if scored else 'missed_free_throw'
    elif 'shot' in play_type:
        processed_play['action'] = 'made_two_pointer' if scored else 'missed_two_pointer'
    else:
        processed_play['action'] = play_type
    
    return processed_play

def send_to_kinesis(play_data):
    """Send play to Kinesis stream"""
    try:
        response = kinesis.put_record(
            StreamName=KINESIS_STREAM,
            Data=json.dumps(play_data),
            PartitionKey=play_data['PK']
        )
        return True
    except Exception as e:
        print(f"❌ Kinesis error: {str(e)}")
        return False

def replay_game(file_path, batch_size=10, delay=0):
    """
    Replay a completed game from ESPN data
    
    Args:
        file_path: Path to completed_game_full.json
        batch_size: How many plays to send at once
        delay: Seconds to wait between batches (0 = send all at once)
    """
    print("🎬 Starting game replay...")
    
    # Load game data
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    plays = data.get('plays', [])
    
    # Get game metadata
    header = data.get('header', {})
    competition = header.get('competitions', [{}])[0]
    competitors = competition.get('competitors', [])
    
    home_team = competitors[0].get('team', {}).get('displayName', 'Home')
    home_team_id = competitors[0].get('team', {}).get('id', '')
    away_team = competitors[1].get('team', {}).get('displayName', 'Away')
    away_team_id = competitors[1].get('team', {}).get('id', '')
    
    game_date = competition.get('date', '').split('T')[0]
    game_id = f"GAME#{game_date}#{away_team.upper().replace(' ', '-')}-{home_team.upper().replace(' ', '-')}"
    
    print(f"📋 Game: {away_team} @ {home_team}")
    print(f"   Game ID: {game_id}")
    print(f"   Total plays: {len(plays)}")
    
    # Process and send plays
    sent_count = 0
    scoring_debug_count = 0  # NEW: separate counter for debug

    for i, play in enumerate(plays):
        # Parse play
        processed_play = parse_play_for_processing(
            play, game_id, home_team, away_team, home_team_id, away_team_id
        )
        
        # *** DEBUG: Show Unknown player plays ***
        if processed_play.get('playerName') == 'Unknown' and i < 50:
            print(f"\n⚠️  Unknown player in play #{i}:")
            print(f"   Text: {processed_play.get('text')}")
            print(f"   Action: {processed_play.get('action')}")
            print(f"   Scoring: {processed_play.get('scoringPlay')}")
            print(f"   Has participants: {len(play.get('participants', []))}")
        
        # Send to Kinesis
        if send_to_kinesis(processed_play):
            sent_count += 1
            
            if (i + 1) % batch_size == 0:
                print(f"   Sent {sent_count}/{len(plays)} plays...")
    
    print(f"✅ Replay complete! Sent {sent_count} plays to Kinesis")
    print(f"   Processing Lambda should now be running...")

if __name__ == '__main__':
    replay_game('iowa_rutgers_game.json', batch_size=20, delay=0)

