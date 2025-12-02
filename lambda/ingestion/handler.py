import json
import os
import requests
from datetime import datetime, timezone
import boto3

# Environment variables
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'live')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')
S3_BUCKET = os.environ.get('S3_BUCKET')
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"
KINESIS_STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME')


dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
kinesis_client = boto3.client('kinesis')


def fetch_with_retry(url, max_retries=3, timeout=10):
    """
    Fetch URL with exponential backoff retry logic
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        dict: JSON response
    
    Raises:
        Exception: If all retries fail
    """
    import time
    
    for attempt in range(max_retries):
        try:
            print(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout on attempt {attempt + 1}")
        except requests.exceptions.HTTPError as e:
            print(f"⚠️  HTTP error on attempt {attempt + 1}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Request error on attempt {attempt + 1}: {e}")
        
        # Don't sleep after last attempt
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"   Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    raise Exception(f"Failed to fetch {url} after {max_retries} attempts")

def fetch_espn_scoreboard():
    """
    Fetch women's college basketball scoreboard from ESPN API
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard"
    
    try:
        data = fetch_with_retry(url)
        print(f"✅ ESPN API returned {len(data.get('events', []))} games")
        return data
    except Exception as e:
        print(f"❌ Error fetching scoreboard: {str(e)}")
        raise

def fetch_game_summary(game_id):
    """
    Fetch detailed game summary including play-by-play from ESPN API
    
    Args:
        game_id: ESPN game ID (e.g., "401825729")
    
    Returns:
        dict: Game summary with play-by-play data, or None if failed
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
    
    try:
        data = fetch_with_retry(url)
        play_count = len(data.get('plays', [])) if 'plays' in data else 0
        print(f"✅ Game summary returned {play_count} plays")
        return data
    except Exception as e:
        print(f"❌ Error fetching game summary for {game_id}: {str(e)}")
        return None

def parse_game_data(espn_game):
    """
    Parse ESPN game data into our internal format
    """
    try:
        game_id = espn_game['id']
        competition = espn_game['competitions'][0]
        
        # Get teams
        competitors = competition['competitors']
        home_team = next(c for c in competitors if c['homeAway'] == 'home')
        away_team = next(c for c in competitors if c['homeAway'] == 'away')
        
        # Get status
        status = competition['status']
        
        # Create matchup string and date
        matchup = f"{away_team['team']['displayName'].replace(' ', '-').upper()}-{home_team['team']['displayName'].replace(' ', '-').upper()}"
        date_str = espn_game['date'][:10]  # Extract YYYY-MM-DD
        
        parsed_game = {
            'PK': f"GAME#{date_str}#{matchup}",  # Add PK here
            'espnGameId': game_id,
            'name': espn_game['name'],
            'shortName': espn_game['shortName'],
            'date': espn_game['date'],
            'homeTeam': home_team['team']['displayName'],
            'homeTeamId': home_team['team']['id'],
            'homeScore': int(home_team.get('score', 0)),
            'awayTeam': away_team['team']['displayName'],
            'awayTeamId': away_team['team']['id'],
            'awayScore': int(away_team.get('score', 0)),
            'status': status['type']['name'],
            'statusState': status['type']['state'],
            'period': status.get('period', 0),
            'displayClock': status.get('displayClock', ''),
        }
        
        return parsed_game
        
    except Exception as e:
        print(f"Error parsing game {espn_game.get('id')}: {str(e)}")
        return None

def parse_play_data(espn_play, game_id):
    """
    Parse ESPN play data into our internal format
    
    Args:
        espn_play: Play data from ESPN API
        game_id: Our game ID (e.g., "GAME#2024-11-30#TEAM1-TEAM2")
    
    Returns:
        dict: Parsed play ready for DynamoDB
    """
    try:
        play_id = espn_play.get('sequenceNumber', espn_play['id'])
        
        # Get timestamp from play or use current time
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()
        
        parsed_play = {
            'PK': game_id,
            'SK': f"PLAY#{timestamp}#{play_id}",
            'playId': play_id,
            'timestamp': timestamp,
            'quarter': espn_play.get('period', {}).get('number', 0),
            'gameClock': espn_play.get('clock', {}).get('displayValue', ''),
            'text': espn_play.get('text', ''),
            'scoringPlay': espn_play.get('scoringPlay', False),
            'homeScore': espn_play.get('homeScore', 0),
            'awayScore': espn_play.get('awayScore', 0),
        }
        
        # Add team ID if present
        if 'team' in espn_play:
            parsed_play['teamId'] = espn_play['team'].get('id', '')
        
        # Add play type if present
        if 'type' in espn_play:
            parsed_play['playType'] = espn_play['type'].get('text', '')
        
        return parsed_play
        
    except Exception as e:
        print(f"Error parsing play: {str(e)}")
        return None

def store_game_metadata(game):
    """
    Store game metadata in DynamoDB
    """
    table = dynamodb.Table(DYNAMODB_TABLE)  # Initialize table here
    
    item = {
        'PK': game['PK'],
        'SK': 'METADATA',
        'espnGameId': game['espnGameId'],
        'homeTeam': game['homeTeam'],
        'awayTeam': game['awayTeam'],
        'homeTeamId': game['homeTeamId'],
        'awayTeamId': game['awayTeamId'],
        'date': game['date'],
        'status': game['status'],
        'statusState': game['statusState'],
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    }
    
    try:
        table.put_item(Item=item)
        print(f"✅ Stored metadata for: {game['PK']}")
        return True
    except Exception as e:
        print(f"❌ Error storing metadata: {str(e)}")
        return False

def store_current_score(game):
    """
    Store current score in DynamoDB
    """
    table = dynamodb.Table(DYNAMODB_TABLE)  # Initialize table here
    
    item = {
        'PK': game['PK'],
        'SK': 'SCORE#CURRENT',
        'homeScore': game['homeScore'],
        'awayScore': game['awayScore'],
        'period': game['period'],
        'displayClock': game['displayClock'],
        'lastUpdated': datetime.utcnow().isoformat()
    }
    
    try:
        table.put_item(Item=item)
        print(f"✅ Stored score: {game['awayTeam']} {game['awayScore']} - {game['homeTeam']} {game['homeScore']}")
        return True
    except Exception as e:
        print(f"❌ Error storing score: {str(e)}")
        return False

def store_play(play):
    """
    Store individual play in DynamoDB
    
    Args:
        play: Parsed play data
    """
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    try:
        table.put_item(Item=play)
        return True
    except Exception as e:
        print(f"❌ Error storing play {play.get('playId')}: {str(e)}")
        return False

def record_to_s3(game_id, data_type, data, timestamp):
    """
    Record data to S3 for replay capability
    
    Args:
        game_id: Format "GAME#YYYY-MM-DD#TEAM1-TEAM2" or "scoreboard"
        data_type: "raw_espn" or "parsed_game"
        data: Dictionary to save as JSON
        timestamp: ISO format timestamp string
    """
    try:
        # Extract date and matchup from game_id
        if game_id == "scoreboard":
            folder_name = "scoreboard"
        else:
            # game_id format: "GAME#2025-12-01#UCLA-UCONN"
            parts = game_id.split('#')
            if len(parts) >= 3:
                date_str = parts[1]  # "2025-12-01"
                matchup = parts[2]   # "UCLA-UCONN"
                folder_name = f"{date_str}-{matchup}"
            else:
                folder_name = game_id.replace('#', '-')
        
        # Create S3 key
        s3_key = f"{folder_name}/{data_type}/{timestamp}.json"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        
        print(f"✅ Recorded to S3: s3://{S3_BUCKET}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to record to S3: {str(e)}")
        return False

def send_to_kinesis(play_data):
    """
    Send play data to Kinesis stream
    
    Args:
        play_data: Dictionary of play data
    
    Returns:
        bool: True if successful
    """
    try:
        response = kinesis_client.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=json.dumps(play_data),
            PartitionKey=play_data['PK']  # Use game ID as partition key
        )
        
        print(f"✅ Sent play to Kinesis: {play_data.get('playId', 'unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send play to Kinesis: {str(e)}")
        return False


def handler(event, context):
    try:
        print("🏀 CourtVision Ingestion Lambda started")
        print(f"DATA_SOURCE: {DATA_SOURCE}")
        
        # Fetch ESPN data
        scoreboard_data = fetch_espn_scoreboard()
        
        # Get current timestamp for this ingestion run
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Record the entire scoreboard to S3
        record_to_s3(
            game_id="scoreboard",
            data_type="raw_espn",
            data=scoreboard_data,
            timestamp=timestamp
        )
        
        # Parse games
        games = scoreboard_data.get('events', [])
        print(f"Found {len(games)} games")
        
        for game in games:
            parsed_game = parse_game_data(game)
            
            if parsed_game:
                game_id = parsed_game['PK']  # e.g., "GAME#2025-12-01#UCLA-UCONN"
                
                # Record parsed game data to S3
                record_to_s3(
                    game_id=game_id,
                    data_type="parsed_game",
                    data=parsed_game,
                    timestamp=timestamp
                )
                
                # Store to DynamoDB
                store_game_metadata(parsed_game)
                store_current_score(parsed_game)
        
                # Fetch detailed game summary if game is active or completed
                game_state = parsed_game.get('statusState', '')
                if game_state in ['in', 'post']:
                    print(f"Game is {game_state}, fetching play-by-play data...")
                    summary = fetch_game_summary(parsed_game['espnGameId'])
                    
                    if summary and 'plays' in summary:
                        play_count = len(summary['plays'])
                        print(f"✅ Fetched {play_count} plays for {game_id}")
                        # Parse and send each play to Kinesis
                        plays_sent = 0
                        for espn_play in summary['plays']:
                            parsed_play = parse_play_data(espn_play, game_id)
                            if parsed_play and send_to_kinesis(parsed_play):
                                plays_sent += 1
                        print(f"✅ Sent {plays_sent}/{play_count} plays to Kinesis")
                    else:
                        print(f"⚠️  No plays found for {game_id}")

        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {len(games)} games')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
    


