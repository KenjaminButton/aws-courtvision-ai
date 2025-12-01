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

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
# ❌ REMOVED: table = dynamodb.Table(DYNAMODB_TABLE)  # This caused the error!

def fetch_espn_scoreboard():
    """
    Fetch women's college basketball scoreboard from ESPN API
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard"
    
    try:
        print(f"Fetching from ESPN: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"ESPN API returned {len(data.get('events', []))} games")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from ESPN: {str(e)}")
        raise

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
    


