import requests
import json

# Texas vs UNC game that already finished
GAME_ID = "401806391"

print(f"Fetching completed game: {GAME_ID}")

# ESPN Summary endpoint (has all plays)
url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={GAME_ID}"

response = requests.get(url, timeout=10)
data = response.json()

# Save to file for inspection
with open('completed_game_full.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Saved full game data to completed_game_full.json")
print(f"   Game: {data.get('header', {}).get('competitions', [{}])[0].get('competitors', [])[0].get('team', {}).get('displayName', 'Unknown')}")
print(f"   Status: {data.get('header', {}).get('competitions', [{}])[0].get('status', {}).get('type', {}).get('description', 'Unknown')}")

# Check if plays exist
plays = data.get('plays', [])
print(f"   Total plays: {len(plays)}")

if len(plays) > 0:
    print(f"   First play: {plays[0].get('text', 'N/A')}")
    print(f"   Last play: {plays[-1].get('text', 'N/A')}")