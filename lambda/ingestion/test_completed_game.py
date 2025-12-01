#!/usr/bin/env python3
import handler
import os

# Set environment variables for local testing
os.environ['DATA_SOURCE'] = 'live'
os.environ['DYNAMODB_TABLE'] = 'courtvision-games'
os.environ['S3_BUCKET'] = 'courtvision-recordings-811230534980'

# Fake a scoreboard response with the completed game
fake_scoreboard = {
    'events': [
        {
            'id': '401724074',
            'name': 'Fresno State Bulldogs vs UCLA Bruins',
            'shortName': 'FRES VS UCLA',
            'date': '2024-11-30T00:00Z',
            'competitions': [{
                'id': '401724074',
                'competitors': [
                    {
                        'id': '26',
                        'homeAway': 'home',
                        'team': {'id': '26', 'displayName': 'UCLA Bruins'},
                        'score': '87'
                    },
                    {
                        'id': '278',
                        'homeAway': 'away',
                        'team': {'id': '278', 'displayName': 'Fresno State Bulldogs'},
                        'score': '66'
                    }
                ],
                'status': {
                    'type': {
                        'name': 'STATUS_FINAL',
                        'state': 'post'  # ← Completed game
                    },
                    'period': 4,
                    'displayClock': '0:00'
                }
            }]
        }
    ]
}

# Parse the game
print("Parsing completed game...")
parsed_game = handler.parse_game_data(fake_scoreboard['events'][0])

if parsed_game:
    print(f"✅ Parsed: {parsed_game['PK']}")
    print(f"   Status state: {parsed_game.get('statusState')}")
    
    # Test summary fetch
    game_state = parsed_game.get('statusState', '')
    if game_state in ['in', 'post']:
        print(f"\n   Game is '{game_state}', fetching play-by-play...")
        summary = handler.fetch_game_summary(parsed_game['espnGameId'])
        
        if summary and 'plays' in summary:
            play_count = len(summary['plays'])
            print(f"   ✅ Fetched {play_count} plays!")
            print(f"\n   First play:")
            print(f"   {summary['plays'][0]['text']}")
        else:
            print(f"   ❌ No plays found")