import json
import os
import requests
from datetime import datetime

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
        
        parsed_game = {
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

def handler(event, context):
    """
    Ingestion Lambda - fetches ESPN data and stores to DynamoDB/S3
    """
    print("Ingestion Lambda invoked")
    
    # Get environment variables
    data_source = os.environ.get('DATA_SOURCE', 'live')
    
    # Fetch scoreboard data
    scoreboard_data = fetch_espn_scoreboard()
    
    # Parse each game
    parsed_games = []
    for espn_game in scoreboard_data.get('events', []):
        parsed = parse_game_data(espn_game)
        if parsed:
            parsed_games.append(parsed)
    
    print(f"Successfully parsed {len(parsed_games)} games")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Ingestion successful',
            'data_source': data_source,
            'games_parsed': len(parsed_games),
            'timestamp': datetime.utcnow().isoformat()
        })
    }