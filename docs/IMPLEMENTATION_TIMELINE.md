# CourtVision AI - Implementation Timeline V2
**Iowa Hawkeyes Basketball Analytics Platform**

---

## Overview

This timeline guides you through building CourtVision AI with a **clean project structure** focused on **historical game analysis** for Iowa Hawkeyes Women's Basketball.

**Total Duration:** 4-6 weeks (at 15-20 hours/week)

---

## Project Structure (Target)

```
courtvision-ai/
├── frontend/                   # React + TypeScript
├── backend/                    # AWS Lambda functions
├── scripts/                    # Analysis & data collection
├── docs/                       # Documentation
└── README.md
```

---

## Phase 0: Clean Restructure
**Duration:** 1 day  
**Goal:** Set up clean project structure, preserve working code

### Step 1: Backup Current Work
**Time:** 10 minutes

```bash
cd ~/Desktop/AWS/AWS\ Projects/03-AWS-Courtvision-AI

# Create archive of current state
mkdir -p archive
cp -r lambda archive/lambda-backup-$(date +%Y%m%d)
cp -r frontend archive/frontend-backup-$(date +%Y%m%d) 2>/dev/null || echo "No frontend yet"

echo "✅ Backed up to archive/"
```

### Step 2: Create New Structure
**Time:** 15 minutes

```bash
# Create new directory structure
mkdir -p backend/ingestion
mkdir -p backend/processing
mkdir -p backend/api
mkdir -p scripts
mkdir -p frontend
mkdir -p docs

# Move documentation
mv Blueprint.md docs/Blueprint-V1.md
mv implementation-timeline.md docs/Implementation-Timeline-V1.md
cp /path/to/BLUEPRINT-V2.md docs/
cp /path/to/IMPLEMENTATION-TIMELINE-V2.md docs/
cp /path/to/DECISIONS.md docs/

echo "✅ Created new structure"
```

### Step 3: Migrate Working Code
**Time:** 30 minutes

```bash
# Move working scripts to new locations
cp archive/lambda-backup-*/ingestion/replay_game.py scripts/
cp archive/lambda-backup-*/ingestion/analyze_patterns.py scripts/

# Move Lambda code (will refactor later)
cp -r archive/lambda-backup-*/ingestion/* backend/ingestion/
cp -r archive/lambda-backup-*/processing/* backend/processing/

# Create requirements files
cat > backend/ingestion/requirements.txt << 'EOF'
boto3>=1.28.0
requests>=2.31.0
EOF

cat > backend/processing/requirements.txt << 'EOF'
boto3>=1.28.0
EOF

cat > scripts/requirements.txt << 'EOF'
boto3>=1.28.0
requests>=2.31.0
EOF

echo "✅ Migrated working code"
```

### Step 4: Create Root README
**Time:** 15 minutes

```bash
cat > README.md << 'EOF'
# CourtVision AI - Iowa Hawkeyes Analytics

Historical basketball analytics platform for Iowa Hawkeyes Women's Basketball.

## Features
- Season-by-season game analysis
- Pattern detection (scoring runs, hot streaks)
- Player performance tracking
- Shot chart visualization
- AI-powered insights

## Project Structure
- `frontend/` - React application
- `backend/` - AWS Lambda functions
- `scripts/` - Data collection & analysis
- `docs/` - Documentation

## Quick Start
See `docs/IMPLEMENTATION-TIMELINE-V2.md`

## Documentation
- [Blueprint](docs/BLUEPRINT-V2.md)
- [Implementation Timeline](docs/IMPLEMENTATION-TIMELINE-V2.md)
- [Decisions Log](docs/DECISIONS.md)
EOF

echo "✅ Created README"
```

### Step 5: Initialize Git (if not already)
**Time:** 10 minutes

```bash
# If .git doesn't exist
git init
git add .
git commit -m "Initial commit: Clean project structure"

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
.DS_Store
.env.local
.env.production.local

# AWS
.aws-sam/
samconfig.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
archive/
*.json.bak
.pytest_cache/
EOF

git add .gitignore
git commit -m "Add .gitignore"

echo "✅ Git initialized"
```

**Phase 0 Checkpoint:** Clean project structure, working code preserved

---

## Phase 1: Data Collection Infrastructure
**Duration:** 3-5 days  
**Goal:** Fetch all Iowa games and store metadata

### Day 1: AWS Resource Verification
**Time:** 2-3 hours

**Task 1.1: Document Existing Resources**

```bash
cd scripts

# Check DynamoDB
aws dynamodb describe-table \
  --table-name courtvision-games \
  --region us-east-1 \
  --query 'Table.[TableName, TableStatus, ItemCount]'

# Check S3 buckets
aws s3 ls | grep courtvision

# Check Kinesis
aws kinesis describe-stream \
  --stream-name courtvision-plays \
  --region us-east-1 \
  --query 'StreamDescription.[StreamName, StreamStatus]'
```

**Task 1.2: Update docs/BLUEPRINT-V2.md**

Fill in actual AWS resource names (replace placeholders).

**Checkpoint:** You have documented all existing AWS resources

---

### Day 2: Fetch Iowa Schedule Script
**Time:** 3-4 hours

**Task 2.1: Create `scripts/fetch_iowa_schedule.py`**

```python
#!/usr/bin/env python3
"""
Fetch all Iowa Hawkeyes games for a given season from ESPN API.
Store game metadata in DynamoDB.
"""

import boto3
import requests
import json
from datetime import datetime

TEAM_ID = "2294"  # Iowa Hawkeyes
DYNAMODB_TABLE = "courtvision-games"
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)

def fetch_season_schedule(season="2024-25"):
    """Fetch all games for Iowa in a season"""
    url = f"{ESPN_BASE_URL}/teams/{TEAM_ID}/schedule"
    
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    events = data.get('events', [])
    games = []
    
    for event in events:
        game_id = event.get('id')
        name = event.get('name', '')
        date = event.get('date', '').split('T')[0]
        
        competitions = event.get('competitions', [])
        if not competitions:
            continue
            
        comp = competitions[0]
        competitors = comp.get('competitors', [])
        
        if len(competitors) < 2:
            continue
        
        # Determine home/away
        home_team = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
        away_team = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
        
        home_name = home_team.get('team', {}).get('displayName', '')
        away_name = away_team.get('team', {}).get('displayName', '')
        
        home_score = home_team.get('score', {})
        away_score = away_team.get('score', {})
        
        if isinstance(home_score, dict):
            home_score = home_score.get('value', 'N/A')
        if isinstance(away_score, dict):
            away_score = away_score.get('value', 'N/A')
        
        status = comp.get('status', {}).get('type', {}).get('description', 'Unknown')
        
        # Determine if Iowa won
        iowa_score = home_score if 'Iowa' in home_name else away_score
        opp_score = away_score if 'Iowa' in home_name else home_score
        
        result = 'N/A'
        if status == 'Final' and iowa_score != 'N/A' and opp_score != 'N/A':
            result = 'W' if float(iowa_score) > float(opp_score) else 'L'
        
        opponent = away_name if 'Iowa' in home_name else home_name
        home_away = 'home' if 'Iowa' in home_name else 'away'
        
        games.append({
            'gameId': game_id,
            'date': date,
            'opponent': opponent,
            'homeAway': home_away,
            'homeTeam': home_name,
            'awayTeam': away_name,
            'homeScore': str(home_score),
            'awayScore': str(away_score),
            'finalScore': f"{home_score}-{away_score}",
            'result': result,
            'status': status,
            'season': season
        })
    
    return games

def store_season_index(games, season="2024-25"):
    """Store season index in DynamoDB"""
    for game in games:
        # Create composite key
        game_key = f"{game['date']}#{game['awayTeam'].upper().replace(' ', '-')}-{game['homeTeam'].upper().replace(' ', '-')}"
        
        item = {
            'PK': f"SEASON#{season}",
            'SK': f"GAME#{game_key}",
            'gameId': game['gameId'],
            'date': game['date'],
            'opponent': game['opponent'],
            'homeAway': game['homeAway'],
            'homeTeam': game['homeTeam'],
            'awayTeam': game['awayTeam'],
            'finalScore': game['finalScore'],
            'result': game['result'],
            'status': game['status'],
            'analyzed': False  # Will set to True after analysis
        }
        
        table.put_item(Item=item)
        print(f"✅ Stored: {game['date']} - {game['opponent']} ({game['result']})")

def main():
    season = "2024-25"
    
    print(f"🏀 Fetching Iowa Hawkeyes schedule for {season} season...\n")
    games = fetch_season_schedule(season)
    
    print(f"\n📊 Found {len(games)} games")
    print(f"   Completed: {sum(1 for g in games if g['status'] == 'Final')}")
    print(f"   Record: {sum(1 for g in games if g['result'] == 'W')}-{sum(1 for g in games if g['result'] == 'L')}\n")
    
    print("💾 Storing in DynamoDB...\n")
    store_season_index(games, season)
    
    print(f"\n✅ Complete! Stored {len(games)} games in SEASON#{season}")

if __name__ == '__main__':
    main()
```

**Task 2.2: Test the script**

```bash
cd scripts
python3 fetch_iowa_schedule.py
```

**Expected output:**
```
🏀 Fetching Iowa Hawkeyes schedule for 2024-25 season...

📊 Found 28 games
   Completed: 10
   Record: 8-2

💾 Storing in DynamoDB...

✅ Stored: 2024-11-05 - Northern Illinois (W)
✅ Stored: 2024-11-10 - Virginia Tech (W)
...

✅ Complete! Stored 28 games in SEASON#2024-25
```

**Checkpoint:** Season games stored in DynamoDB

---

### Day 3: Download Individual Games
**Time:** 3-4 hours

**Task 3.1: Create `scripts/download_game.py`**

```python
#!/usr/bin/env python3
"""
Download a specific game's play-by-play data from ESPN.
Save to S3 for replay.
"""

import boto3
import requests
import json
import sys
from pathlib import Path

ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball"
S3_BUCKET = "courtvision-recordings-{YOUR_ACCOUNT_ID}"  # UPDATE THIS
LOCAL_STORAGE = Path("game_data")

s3 = boto3.client('s3', region_name='us-east-1')

def download_game(game_id, save_local=True, save_s3=True):
    """Download game summary from ESPN"""
    url = f"{ESPN_BASE_URL}/summary?event={game_id}"
    
    print(f"📥 Downloading game {game_id}...")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Extract game info for filename
    header = data.get('header', {})
    comp = header.get('competitions', [{}])[0]
    competitors = comp.get('competitors', [])
    
    home_team = competitors[0].get('team', {}).get('displayName', 'Home')
    away_team = competitors[1].get('team', {}).get('displayName', 'Away')
    date = comp.get('date', '').split('T')[0]
    
    filename = f"{date}_{away_team.replace(' ', '_')}@{home_team.replace(' ', '_')}.json"
    
    # Save locally
    if save_local:
        LOCAL_STORAGE.mkdir(exist_ok=True)
        filepath = LOCAL_STORAGE / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved locally: {filepath}")
    
    # Save to S3
    if save_s3:
        s3_key = f"games/{filename}"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        print(f"☁️  Saved to S3: s3://{S3_BUCKET}/{s3_key}")
    
    return filename, data

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 download_game.py <game_id>")
        print("Example: python3 download_game.py 401818630")
        sys.exit(1)
    
    game_id = sys.argv[1]
    filename, data = download_game(game_id)
    
    plays = data.get('plays', [])
    print(f"\n✅ Downloaded {len(plays)} plays")
    print(f"   File: {filename}")

if __name__ == '__main__':
    main()
```

**Task 3.2: Update S3 bucket name in script**

Replace `{YOUR_ACCOUNT_ID}` with your actual bucket name.

**Task 3.3: Test download**

```bash
cd scripts

# Download the Baylor game we already tested
python3 download_game.py 401818630
```

**Checkpoint:** Can download individual games to local and S3

---

### Day 4: Bulk Download Script
**Time:** 2-3 hours

**Task 4.1: Create `scripts/bulk_download_season.py`**

```python
#!/usr/bin/env python3
"""
Download all games for a season from DynamoDB game list.
"""

import boto3
import time
from download_game import download_game

DYNAMODB_TABLE = "courtvision-games"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)

def get_season_games(season="2024-25"):
    """Query all games for a season"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f"SEASON#{season}"}
    )
    return response['Items']

def main():
    season = "2024-25"
    
    print(f"🏀 Fetching game list for {season}...\n")
    games = get_season_games(season)
    
    completed_games = [g for g in games if g.get('status') == 'Final']
    
    print(f"📊 Found {len(completed_games)} completed games\n")
    
    for i, game in enumerate(completed_games, 1):
        game_id = game['gameId']
        opponent = game['opponent']
        date = game['date']
        
        print(f"\n[{i}/{len(completed_games)}] {date} vs {opponent}")
        
        try:
            download_game(game_id, save_local=True, save_s3=True)
            time.sleep(1)  # Be nice to ESPN
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print(f"\n✅ Downloaded {len(completed_games)} games")

if __name__ == '__main__':
    main()
```

**Task 4.2: Run bulk download (only for completed games)**

```bash
cd scripts
python3 bulk_download_season.py
```

**This will take ~5 minutes for 10 games.**

**Checkpoint:** All completed Iowa games downloaded to S3

---

### Day 5: Update Replay Script for Batch Processing
**Time:** 2-3 hours

**Task 5.1: Update `scripts/replay_game.py`**

Make sure it can:
- Accept filename as argument
- Work with game_data/*.json files
- Store proper game metadata in DynamoDB

**Task 5.2: Test replay with downloaded game**

```bash
cd scripts
python3 replay_game.py game_data/2024-11-21_Iowa_Hawkeyes@Baylor_Bears.json
```

**Checkpoint:** Can replay downloaded games

---

**Phase 1 Complete:**
- ✅ All Iowa games for season fetched
- ✅ Game metadata in DynamoDB
- ✅ Completed games downloaded
- ✅ Replay system working

---

## Phase 2: Bulk Game Analysis
**Duration:** 3-5 days  
**Goal:** Analyze all downloaded games, store patterns and stats

### Day 6: Bulk Analysis Script
**Time:** 3-4 hours

**Task 6.1: Create `scripts/bulk_analyze_season.py`**

```python
#!/usr/bin/env python3
"""
Analyze all games for a season:
1. Replay game (sends to Kinesis/DynamoDB)
2. Run pattern detection
3. Mark game as analyzed
"""

import boto3
import time
import subprocess
from pathlib import Path

DYNAMODB_TABLE = "courtvision-games"
GAME_DATA_DIR = Path("game_data")

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)

def get_season_games(season="2024-25"):
    """Get all games for season"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f"SEASON#{season}"}
    )
    return response['Items']

def mark_game_analyzed(season, game_sk):
    """Update game as analyzed"""
    table.update_item(
        Key={'PK': f"SEASON#{season}", 'SK': game_sk},
        UpdateExpression='SET analyzed = :val',
        ExpressionAttributeValues={':val': True}
    )

def analyze_game(game_file, game_id):
    """Run replay and analysis for a game"""
    print(f"\n  1️⃣  Replaying game...")
    result = subprocess.run(
        ['python3', 'replay_game.py', str(game_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"  ❌ Replay failed: {result.stderr}")
        return False
    
    print(f"  ✅ Replay complete")
    
    time.sleep(2)  # Let DynamoDB settle
    
    print(f"  2️⃣  Analyzing patterns...")
    result = subprocess.run(
        ['python3', 'analyze_patterns.py', game_id],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"  ❌ Analysis failed: {result.stderr}")
        return False
    
    print(f"  ✅ Analysis complete")
    return True

def main():
    season = "2024-25"
    
    print(f"🏀 Bulk analyzing {season} season...\n")
    
    games = get_season_games(season)
    completed_games = [g for g in games if g.get('status') == 'Final']
    
    print(f"📊 Found {len(completed_games)} completed games")
    
    # Find corresponding game files
    game_files = list(GAME_DATA_DIR.glob("*.json"))
    print(f"📁 Found {len(game_files)} downloaded game files\n")
    
    success_count = 0
    
    for i, game in enumerate(completed_games, 1):
        opponent = game['opponent']
        date = game['date']
        game_id = game['gameId']
        game_sk = game['SK']
        
        # Check if already analyzed
        if game.get('analyzed', False):
            print(f"[{i}/{len(completed_games)}] ⏭️  {date} vs {opponent} - Already analyzed")
            continue
        
        print(f"\n[{i}/{len(completed_games)}] 🎯 {date} vs {opponent}")
        
        # Find game file
        game_file = None
        for f in game_files:
            if date in f.name and opponent.replace(' ', '_') in f.name:
                game_file = f
                break
        
        if not game_file:
            print(f"  ❌ Game file not found")
            continue
        
        # Analyze
        if analyze_game(game_file, game_id):
            mark_game_analyzed(season, game_sk)
            success_count += 1
            print(f"  ✅ Marked as analyzed")
        
        time.sleep(2)  # Throttle
    
    print(f"\n✅ Complete! Analyzed {success_count}/{len(completed_games)} games")

if __name__ == '__main__':
    main()
```

**Task 6.2: Update `analyze_patterns.py` to accept game_id as argument**

```python
import sys

def main():
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
    else:
        game_id = 'GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS'  # default
    
    analyze_game(game_id)
```

**Task 6.3: Run bulk analysis**

```bash
cd scripts
python3 bulk_analyze_season.py
```

**This will take 30-60 minutes for 10 games.**

**Checkpoint:** All completed games analyzed with patterns stored

---

### Day 7-8: Player Season Aggregation
**Time:** 4-6 hours

**Task 7.1: Create `scripts/aggregate_player_stats.py`**

```python
#!/usr/bin/env python3
"""
Aggregate player stats across all games in a season.
Store season summary in DynamoDB.
"""

import boto3
from collections import defaultdict

DYNAMODB_TABLE = "courtvision-games"
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)

def get_all_player_game_stats(season="2024-25"):
    """Scan for all player game stats in a season"""
    # This is inefficient but OK for small dataset
    response = table.scan()
    items = response['Items']
    
    # Filter for player stats
    player_stats = [
        item for item in items 
        if item.get('PK', '').startswith('PLAYER#') 
        and '#STATS' in item.get('SK', '')
        and item.get('season') == season
    ]
    
    return player_stats

def aggregate_season_stats(player_game_stats):
    """Aggregate stats by player"""
    player_totals = defaultdict(lambda: {
        'playerId': '',
        'playerName': '',
        'team': '',
        'gamesPlayed': 0,
        'totalPoints': 0,
        'totalFGMade': 0,
        'totalFGAttempted': 0,
        'totalThreeMade': 0,
        'totalThreeAttempted': 0,
        'totalRebounds': 0,
        'totalAssists': 0,
        'totalFouls': 0
    })
    
    for stat in player_game_stats:
        player_id = stat['playerId']
        
        # Initialize player info
        if not player_totals[player_id]['playerId']:
            player_totals[player_id]['playerId'] = player_id
            player_totals[player_id]['playerName'] = stat.get('playerName', '')
            player_totals[player_id]['team'] = stat.get('team', '')
        
        # Aggregate stats
        player_totals[player_id]['gamesPlayed'] += 1
        player_totals[player_id]['totalPoints'] += stat.get('points', 0)
        player_totals[player_id]['totalFGMade'] += stat.get('fgMade', 0)
        player_totals[player_id]['totalFGAttempted'] += stat.get('fgAttempted', 0)
        player_totals[player_id]['totalThreeMade'] += stat.get('threeMade', 0)
        player_totals[player_id]['totalThreeAttempted'] += stat.get('threeAttempted', 0)
        player_totals[player_id]['totalRebounds'] += stat.get('rebounds', 0)
        player_totals[player_id]['totalAssists'] += stat.get('assists', 0)
        player_totals[player_id]['totalFouls'] += stat.get('fouls', 0)
    
    # Calculate averages and percentages
    for player_id, totals in player_totals.items():
        games = totals['gamesPlayed']
        
        if games > 0:
            totals['avgPoints'] = round(totals['totalPoints'] / games, 1)
            totals['avgRebounds'] = round(totals['totalRebounds'] / games, 1)
            totals['avgAssists'] = round(totals['totalAssists'] / games, 1)
        
        if totals['totalFGAttempted'] > 0:
            totals['fgPct'] = round(totals['totalFGMade'] / totals['totalFGAttempted'], 3)
        else:
            totals['fgPct'] = 0.0
        
        if totals['totalThreeAttempted'] > 0:
            totals['threePct'] = round(totals['totalThreeMade'] / totals['totalThreeAttempted'], 3)
        else:
            totals['threePct'] = 0.0
    
    return player_totals

def store_season_summaries(player_totals, season="2024-25"):
    """Store season summaries in DynamoDB"""
    for player_id, stats in player_totals.items():
        item = {
            'PK': f"PLAYER#{player_id}",
            'SK': f"SEASON#{season}#SUMMARY",
            **stats,
            'season': season
        }
        
        table.put_item(Item=item)
        
        print(f"✅ {stats['playerName']}: {stats['avgPoints']} PPG, {stats['fgPct']} FG%, {stats['threePct']} 3P%")

def main():
    season = "2024-25"
    
    print(f"🏀 Aggregating player stats for {season} season...\n")
    
    print("📥 Loading all player game stats...")
    player_game_stats = get_all_player_game_stats(season)
    print(f"   Found {len(player_game_stats)} player-game records\n")
    
    print("🧮 Calculating season totals...")
    player_totals = aggregate_season_stats(player_game_stats)
    print(f"   Aggregated stats for {len(player_totals)} players\n")
    
    print("💾 Storing season summaries...\n")
    store_season_summaries(player_totals, season)
    
    print(f"\n✅ Complete! Stored season summaries for {len(player_totals)} players")

if __name__ == '__main__':
    main()
```

**Task 7.2: Run aggregation**

```bash
cd scripts
python3 aggregate_player_stats.py
```

**Checkpoint:** Player season summaries stored in DynamoDB

---

**Phase 2 Complete:**
- ✅ All games analyzed
- ✅ Patterns detected and stored
- ✅ Player stats aggregated by season

---

## Phase 3: Frontend - Season & Game Views
**Duration:** 1-2 weeks  
**Goal:** Build React UI to display games and patterns

### Day 9: Frontend Setup
**Time:** 2-3 hours

**Task 9.1: Create React App**

```bash
cd courtvision-ai

npx create-react-app frontend --template typescript
cd frontend

# Install dependencies
npm install tailwindcss recharts react-router-dom
npx tailwindcss init
```

**Task 9.2: Configure Tailwind**

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'iowa-gold': '#FFCD00',
        'iowa-black': '#000000',
      }
    },
  },
  plugins: [],
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Task 9.3: Set up React Router**

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/seasons/:season" element={<SeasonView />} />
        <Route path="/seasons/:season/game/:gameId" element={<GameView />} />
        <Route path="/seasons/:season/players" element={<PlayerList />} />
        <Route path="/seasons/:season/player/:playerId" element={<PlayerDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**Checkpoint:** Frontend initialized with routing

---

### Day 10-11: API Gateway + Lambda for Queries
**Time:** 4-6 hours

**Task 10.1: Create `backend/api/handler.py`**

```python
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    API Gateway Lambda handler
    Routes: 
    - GET /seasons/{season}/games
    - GET /games/{gameId}
    - GET /games/{gameId}/patterns
    - GET /players/{playerId}/season/{season}
    """
    
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    if http_method == 'GET':
        if '/seasons/' in path and '/games' in path:
            # GET /seasons/2024-25/games
            season = path.split('/seasons/')[1].split('/')[0]
            return get_season_games(season)
        
        elif '/games/' in path and '/patterns' in path:
            # GET /games/{gameId}/patterns
            game_id = path.split('/games/')[1].split('/')[0]
            return get_game_patterns(game_id)
        
        elif '/games/' in path:
            # GET /games/{gameId}
            game_id = path.split('/games/')[1]
            return get_game_details(game_id)
        
        elif '/players/' in path:
            # GET /players/{playerId}/season/{season}
            parts = path.split('/')
            player_id = parts[parts.index('players') + 1]
            season = parts[parts.index('season') + 1]
            return get_player_season(player_id, season)
    
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'})
    }

def get_season_games(season):
    """Get all games for a season"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f"SEASON#{season}"}
    )
    
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(response['Items'], cls=DecimalEncoder)
    }

def get_game_details(game_id):
    """Get game metadata"""
    response = table.get_item(
        Key={'PK': game_id, 'SK': 'METADATA'}
    )
    
    item = response.get('Item')
    if not item:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Game not found'})}
    
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(item, cls=DecimalEncoder)
    }

def get_game_patterns(game_id):
    """Get all patterns for a game"""
    response = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :pattern)',
        ExpressionAttributeValues={
            ':pk': game_id,
            ':pattern': 'AI#PATTERN#'
        }
    )
    
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(response['Items'], cls=DecimalEncoder)
    }

def get_player_season(player_id, season):
    """Get player season summary"""
    response = table.get_item(
        Key={
            'PK': f"PLAYER#{player_id}",
            'SK': f"SEASON#{season}#SUMMARY"
        }
    )
    
    item = response.get('Item')
    if not item:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Player not found'})}
    
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(item, cls=DecimalEncoder)
    }
```

**Task 10.2: Deploy API Lambda**

```bash
cd backend/api

# Create deployment package
zip -r function.zip handler.py
aws lambda create-function \
  --function-name courtvision-api \
  --runtime python3.12 \
  --role arn:aws:iam::{ACCOUNT_ID}:role/lambda-execution-role \
  --handler handler.lambda_handler \
  --zip-file fileb://function.zip \
  --region us-east-1
```

**Task 10.3: Create API Gateway**

Use AWS Console or CLI to create REST API with routes pointing to Lambda.

**Checkpoint:** API returning data from DynamoDB

---

### Day 12-13: Season Game List Component
**Time:** 4-6 hours

**Task 12.1: Create `src/components/GameCard.tsx`**

```typescript
interface GameCardProps {
  game: {
    date: string;
    opponent: string;
    homeAway: 'home' | 'away';
    finalScore: string;
    result: 'W' | 'L' | 'N/A';
    analyzed: boolean;
  };
  onClick: () => void;
}

export const GameCard: React.FC<GameCardProps> = ({ game, onClick }) => {
  const resultColor = game.result === 'W' ? 'text-green-600' : 'text-red-600';
  
  return (
    <div 
      onClick={onClick}
      className="p-4 bg-white rounded-lg shadow hover:shadow-lg cursor-pointer transition"
    >
      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm text-gray-500">{game.date}</p>
          <p className="text-lg font-semibold">
            {game.homeAway === 'away' ? '@' : 'vs'} {game.opponent}
          </p>
        </div>
        <div className="text-right">
          <p className={`text-2xl font-bold ${resultColor}`}>
            {game.result}
          </p>
          <p className="text-sm text-gray-600">{game.finalScore}</p>
        </div>
      </div>
      
      {game.analyzed && (
        <span className="mt-2 inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
          Analyzed
        </span>
      )}
    </div>
  );
};
```

**Task 12.2: Create `src/pages/SeasonView.tsx`**

```typescript
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GameCard } from '../components/GameCard';

export const SeasonView = () => {
  const { season } = useParams();
  const navigate = useNavigate();
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchGames();
  }, [season]);
  
  const fetchGames = async () => {
    const response = await fetch(`${API_URL}/seasons/${season}/games`);
    const data = await response.json();
    setGames(data);
    setLoading(false);
  };
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">
        Iowa Hawkeyes {season} Season
      </h1>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {games.map(game => (
          <GameCard 
            key={game.SK}
            game={game}
            onClick={() => navigate(`/seasons/${season}/game/${game.gameId}`)}
          />
        ))}
      </div>
    </div>
  );
};
```

**Checkpoint:** Can view season game list

---

### Day 14-16: Individual Game View
**Time:** 6-8 hours

Build components for:
- Game score summary
- Pattern alerts display
- Player box score
- Basic shot chart (circles on court SVG)

**Checkpoint:** Individual game view displays all data

---

**Phase 3 Complete:**
- ✅ Frontend displays season games
- ✅ Can view individual game details
- ✅ Patterns and stats visible

---

## Phase 4: Interactive Replay & Polish
**Duration:** 1 week  
**Goal:** Add replay feature, improve UI

### Day 17-19: Game Replay Component

Build interactive replay that:
- Queries all plays from DynamoDB
- Displays them in sequence with delays
- Shows patterns at their timestamps
- Updates score progressively

### Day 20-21: Player Dashboard

Build player season view with:
- Season stats
- Combined shot chart
- Game log

### Day 22-23: Polish & Deploy

- Loading states
- Error handling
- Mobile responsiveness
- Deploy to S3 + CloudFront

**Phase 4 Complete:**
- ✅ Interactive replay working
- ✅ Player dashboards functional
- ✅ Deployed to production

---

## Phase 5: AI Insights (Optional)
**Duration:** 3-5 days  

Generate AI analysis using Bedrock for:
- Game summaries
- Player efficiency insights
- Season trends

---

## Demo Checklist

Before showing to employers:

- [ ] 2024-25 season fully analyzed
- [ ] At least 10 games with patterns detected
- [ ] 5+ player dashboards working
- [ ] Interactive replay smooth at 3x speed
- [ ] Deployed and accessible via URL
- [ ] README with architecture diagram
- [ ] 2-minute demo video recorded

---

## When to Start New Chat Sessions

**Start fresh chat when:**
1. Beginning Phase 3 (Frontend)
2. Stuck on a bug for >30 minutes
3. Context window getting full (Claude forgets early decisions)

**What to upload to new chat:**
- This timeline (mark where you are)
- BLUEPRINT-V2.md
- DECISIONS.md
- Specific code files if debugging

---

**Good luck! This is a great portfolio project.** 🏀