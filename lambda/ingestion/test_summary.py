#!/usr/bin/env python3
import requests
import json

# Try to find games from the past few days
dates_to_try = [
    "20241130",  # November 30
    "20241129",  # November 29
    "20241127",  # November 27
    "20241123",  # November 23
]

for date in dates_to_try:
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard?dates={date}"
    
    print(f"\nChecking {date}...")
    response = requests.get(url, timeout=10)
    data = response.json()
    games = data.get('events', [])
    
    if not games:
        print(f"  No games found")
        continue
    
    print(f"  Found {len(games)} games")
    
    for game in games[:3]:  # Check first 3 games
        game_id = game['id']
        name = game['shortName']
        status = game['competitions'][0]['status']['type']
        state = status['state']
        
        if state == 'post':
            print(f"\n✅ FOUND COMPLETED GAME:")
            print(f"   {name}")
            print(f"   Game ID: {game_id}")
            print(f"   Date: {date}")
            
            # Try to fetch summary
            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
            summary_response = requests.get(summary_url, timeout=10)
            summary = summary_response.json()
            
            if 'plays' in summary:
                play_count = len(summary['plays'])
                print(f"   ✅ Has {play_count} plays!")
                
                if play_count > 0:
                    print(f"\n   Sample play:")
                    print(json.dumps(summary['plays'][0], indent=2)[:400])
                
                print(f"\n   Use this game_id for testing: {game_id}")
                exit(0)
            else:
                print(f"   ⚠️  No plays found")