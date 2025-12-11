

# Get DynamoDB table name
aws dynamodb list-tables --region us-east-1

# Get S3 bucket names  
aws s3 ls

# Get Kinesis stream name
aws kinesis list-streams --region us-east-1

# Get Lambda function names
aws lambda list-functions --region us-east-1 --query 'Functions[].FunctionName'

### Project Folder Structure:
```
courtvision-ai/
├── frontend/                   # React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                    # AWS Lambda functions
│   ├── ingestion/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── processing/
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── api/
│       ├── handler.py
│       └── requirements.txt
│
├── scripts/                    # One-off analysis scripts
│   ├── fetch_iowa_schedule.py
│   ├── bulk_analyze_season.py
│   └── aggregate_player_stats.py
│
├── infrastructure/             # IaC (CDK or SAM)
│   ├── lib/
│   │   ├── dynamodb-stack.ts
│   │   ├── lambda-stack.ts
│   │   └── api-stack.ts
│   └── cdk.json
│
├── docs/                       # Documentation
│   ├── BLUEPRINT-V2.md
│   ├── IMPLEMENTATION-TIMELINE-V2.md
│   └── API.md
│
├── .gitignore
├── README.md
└── package.json               # Root package.json for scripts
```
# CourtVision AI - Iowa Hawkeyes Edition
**Tagline:** Historical basketball analytics and player performance tracking for Iowa Hawkeyes Women's Basketball

---

## Executive Summary

CourtVision AI is a sports analytics platform focused exclusively on **Iowa Hawkeyes Women's Basketball**. The application analyzes historical games, detects patterns (scoring runs, hot streaks), tracks player performance over time, and provides season-long insights with AI-powered analysis.

**Key Differentiator:** This isn't just a stats tracker. It combines historical game replay, AI pattern detection, season-long player analytics, and shot chart visualization to provide comprehensive insights into Iowa's performance.

---

## Project Pivot (December 2024)

### Original Vision
Real-time tracking of all women's college basketball games with live AI analysis.

### New Vision (Better!)
Deep historical analysis of Iowa Hawkeyes games with:
- Complete game-by-game breakdown
- Season-long player performance tracking
- AI-detected patterns and insights
- Interactive game replay capability

**Why This Is Better:**
- Always demo-able (not dependent on live game schedule)
- Richer insights (historical context, trends over time)
- More focused (one team you know intimately)
- Easier to build (no real-time complexity for MVP)

---

## What's Already Built & Working

### ✅ Core Infrastructure
- **AWS Account:** Dev environment configured
- **DynamoDB Table:** `courtvision-games` with working schema
- **S3 Buckets:** Game data storage
- **Kinesis Stream:** Event processing pipeline
- **Lambda Functions:** Processing pipeline (needs minor adjustments)

### ✅ Game Replay System
- **`replay_game.py`:** Downloads ESPN game data, replays play-by-play
- Works with completed games from ESPN API
- Correctly parses plays, player actions, scoring
- Stores all plays in DynamoDB

### ✅ Pattern Detection (Fully Functional)
- **Scoring Run Detection:** Multi-window analysis (25, 50, 75, 120 plays)
  - Detects runs like "Iowa 20-6 run" or "Opponent 8-0 run"
  - Quarter-based analysis
  - Proper deduplication
- **Hot Streak Detection:** Identifies players making 3+ consecutive field goals
  - Excludes free throws (field goals only)
  - Tracks consecutive makes
  - Example: "Caitlin Clark: 5 straight makes"

### ✅ Player Stats Tracking
- Points, field goals made/attempted, three-pointers, fouls
- Per-game stats stored in DynamoDB
- Foundation for season aggregation

### ✅ Shot Chart Data Collection
- X/Y coordinates stored for every shot
- Made vs. missed tracked
- Shot type classification (layup, mid-range, three-pointer)

---

## Core Features (To Build)

### Feature 1: Season Selection & Game Library
**User Flow:**
1. User lands on home page
2. Selects season: "2024-25" or "2025-26"
3. Sees list of all Iowa games with scores
4. Clicks a game to view details

**Data:**
- Fetch all Iowa games from ESPN API for selected season
- Store game metadata (opponent, date, final score)
- Mark games as "analyzed" or "pending analysis"

### Feature 2: Individual Game Analysis View
**Components:**
- **Score Summary:** Final score, quarter-by-quarter breakdown
- **Detected Patterns:** 
  - Scoring runs (e.g., "Iowa 23-4 run in Q3")
  - Hot streaks (e.g., "Hannah Stuelke: 4 straight makes")
- **Player Stats:** Box score for all players
- **Shot Charts:** Visual representation of shot locations
- **AI Commentary:** Claude's analysis of the game (key moments, turning points)

### Feature 3: Interactive Game Replay
**User Experience:**
- Click "Replay Game" button
- Select speed: 1x, 3x, 10x
- Watch play-by-play unfold in sequence
- Patterns appear as alerts when they occurred in the game
- Score updates in real-time
- Shot chart builds progressively

**Technical Approach:**
- Frontend queries all plays from DynamoDB
- Displays plays in sequence with timing delays
- Shows stored patterns at their timestamps
- Think: Movie player, not live analysis

### Feature 4: Season Player Analytics
**Per Player Dashboard:**
- **Season Stats:** Total points, PPG, FG%, 3P%, rebounds, assists
- **Shot Chart:** All shots from all games combined
- **Efficiency Analysis:** AI analysis of:
  - Shooting zones (strong/weak areas)
  - Shot selection patterns
  - Consistency across games
  - Improvement/decline trends
- **Game Log:** Performance in each game

**Example:**
"Caitlin Clark - 2024-25 Season"
- 28 games, 28.4 PPG, 49% FG, 38% 3P
- Shot chart shows: Strong from right wing, weak from left baseline
- AI: "Clark's efficiency improves in close games (52% FG when margin <5)"

### Feature 5: Team Season Summary
- Win/loss record
- Average scoring by quarter
- Biggest wins/losses
- Most common patterns (which runs happen most)
- Top performers

---

## Technical Architecture

### Data Source: ESPN Hidden API

**Endpoints Used:**
```
# Get team schedule
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/teams/2294/schedule

# Get game summary (play-by-play)
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={gameId}
```

**Iowa Hawkeyes Team ID:** `2294`

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     ONE-TIME SETUP                          │
│  (Run scripts to populate historical data)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. fetch_iowa_games.py                                     │
│     ├─ Queries ESPN for all Iowa games (season)            │
│     ├─ Saves game IDs, dates, opponents, scores            │
│     └─ Creates game list in DynamoDB                        │
│                                                             │
│  2. For each game:                                          │
│     ├─ download_game.py {gameId}                            │
│     │   └─ Saves iowa_vs_opponent.json                      │
│     │                                                        │
│     ├─ replay_game.py iowa_vs_opponent.json                 │
│     │   └─ Sends all plays to Kinesis                       │
│     │   └─ Stores in DynamoDB                               │
│     │                                                        │
│     └─ analyze_patterns.py {gameId}                         │
│         └─ Detects scoring runs                             │
│         └─ Detects hot streaks                              │
│         └─ Stores patterns in DynamoDB                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND QUERIES                         │
│  (User requests data, frontend fetches from DynamoDB)       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Season View:                                               │
│    └─ Query: List all games for season                      │
│                                                             │
│  Game View:                                                 │
│    ├─ Query: Game metadata                                  │
│    ├─ Query: All plays (for replay)                         │
│    ├─ Query: Detected patterns                              │
│    └─ Query: Player stats                                   │
│                                                             │
│  Player Season View:                                        │
│    ├─ Query: All games for player                           │
│    ├─ Aggregate: Sum stats across games                     │
│    └─ Query: All shots for season shot chart                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **DynamoDB** | Primary database | On-demand, streams enabled |
| **S3** | Store raw ESPN game JSON files | Standard storage |
| **Kinesis** | Event stream for play processing | 1 shard |
| **Lambda (Processing)** | Parse plays, update stats | Python 3.12, 512MB |
| **Lambda (Analysis)** | Pattern detection | Python 3.12, 512MB |
| **API Gateway REST** | Frontend API for queries | GET endpoints |
| **Bedrock (Claude)** | AI analysis & insights | Sonnet 4 |
| **S3 + CloudFront** | Frontend hosting | React SPA |

---

## DynamoDB Schema

### Single-Table Design

**Primary Key:**
- **PK (Partition Key):** Entity type + identifier
- **SK (Sort Key):** Sorting and filtering

### Access Patterns

| Pattern | PK | SK | Example |
|---------|----|----|---------|
| List games for season | `SEASON#2024-25` | `GAME#{date}#{opponent}` | All Iowa games 2024-25 |
| Get game metadata | `GAME#{date}#{opponent}` | `METADATA` | Iowa @ Baylor Nov 21 |
| Get all plays in game | `GAME#{date}#{opponent}` | `PLAY#{timestamp}` | Chronological plays |
| Get patterns in game | `GAME#{date}#{opponent}` | `AI#PATTERN#{timestamp}` | Scoring runs, hot streaks |
| Get player stats (one game) | `PLAYER#{playerId}` | `GAME#{date}#{opponent}#STATS` | Caitlin's stats vs Baylor |
| Get player season stats | `PLAYER#{playerId}` | `SEASON#2024-25#SUMMARY` | Caitlin's season totals |
| Get all player shots (season) | `PLAYER#{playerId}` | `SHOT#{gameId}#{timestamp}` | All Caitlin shots |

### Example Items

```json
// Season Index
{
  "PK": "SEASON#2024-25",
  "SK": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS",
  "gameId": "401818630",
  "opponent": "Baylor Bears",
  "homeAway": "away",
  "finalScore": "57-52",
  "result": "W",
  "analyzed": true
}

// Game Metadata
{
  "PK": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS",
  "SK": "METADATA",
  "homeTeam": "Baylor Bears",
  "awayTeam": "Iowa Hawkeyes",
  "homeTeamId": "239",
  "awayTeamId": "2294",
  "finalScore": { "home": 52, "away": 57 },
  "date": "2024-11-21",
  "season": "2024-25"
}

// Individual Play
{
  "PK": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS",
  "SK": "PLAY#2024-11-21T19:15:30Z#115588",
  "playId": "401818630115588",
  "timestamp": "2024-11-21T19:15:30Z",
  "quarter": 2,
  "gameClock": "5:23",
  "team": "Iowa Hawkeyes",
  "playerId": "4433218",
  "playerName": "Caitlin Clark",
  "action": "made_three_pointer",
  "text": "Caitlin Clark made Three Point Jumper",
  "homeScore": 28,
  "awayScore": 31,
  "scoringPlay": true,
  "pointsScored": 3,
  "shotLocation": { "x": 23, "y": 8 }
}

// Detected Pattern
{
  "PK": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS",
  "SK": "AI#PATTERN#2024-11-21T19:20:00Z",
  "patternType": "scoring_run",
  "team": "Iowa Hawkeyes",
  "pointsFor": 12,
  "pointsAgainst": 2,
  "quarter": 2,
  "description": "Iowa Hawkeyes on a 12-2 run",
  "windowType": "50-play"
}

// Player Game Stats
{
  "PK": "PLAYER#4433218",
  "SK": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS#STATS",
  "playerId": "4433218",
  "playerName": "Caitlin Clark",
  "team": "Iowa Hawkeyes",
  "gameId": "GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS",
  "points": 28,
  "fgMade": 10,
  "fgAttempted": 18,
  "threeMade": 4,
  "threeAttempted": 9,
  "fouls": 2,
  "season": "2024-25"
}

// Player Season Summary
{
  "PK": "PLAYER#4433218",
  "SK": "SEASON#2024-25#SUMMARY",
  "playerId": "4433218",
  "playerName": "Caitlin Clark",
  "team": "Iowa Hawkeyes",
  "gamesPlayed": 28,
  "totalPoints": 795,
  "avgPoints": 28.4,
  "fgPct": 0.489,
  "threePct": 0.378,
  "updatedAt": "2025-03-15T00:00:00Z"
}
```

---

## Scripts & Tools (Already Built, but look at this as a guide, not a solution to what we're building)

### Working Scripts

**`lambda/ingestion/replay_game.py`**
- Purpose: Replay completed game from ESPN JSON
- Input: `iowa_vs_opponent.json` file
- Output: All plays sent to Kinesis → stored in DynamoDB
- Status: ✅ Working, tested with multiple games

**`lambda/ingestion/analyze_patterns.py`**
- Purpose: Detect scoring runs and hot streaks
- Input: Game ID
- Output: Patterns stored in DynamoDB
- Features:
  - Multi-window run detection (25, 50, 75, 120 plays)
  - Quarter-based analysis
  - Hot streak detection (3+ consecutive makes)
- Status: ✅ Working perfectly

### Scripts to Build

**`scripts/fetch_iowa_schedule.py`**
- Fetch all Iowa games for a season from ESPN API
- Store game list in DynamoDB
- Mark games as pending analysis

**`scripts/bulk_analyze_season.py`**
- Loop through all games in a season
- Download → Replay → Analyze each game
- Progress tracking

**`scripts/aggregate_player_stats.py`**
- Query all games for a player
- Calculate season totals
- Store in PLAYER#X / SEASON#Y#SUMMARY

---

## Frontend (React)

### Page Structure

```
/                               → Landing page
/seasons                        → Season selector (2024-25, 2025-26)
/seasons/2024-25                → Game list for season
/seasons/2024-25/game/{gameId}  → Individual game view
/seasons/2024-25/players        → Player list
/seasons/2024-25/player/{id}    → Player season dashboard
```

### Key Components

**SeasonSelector**
- Dropdown or button group
- Options: 2024-25, 2025-26, etc.

**GameList**
- Table/cards showing: Date, Opponent, Score, Result (W/L)
- Click to view game details
- Badge showing "Analyzed" status

**GameView**
- Score summary (final + quarters)
- Pattern alerts section
- Player box score
- Shot charts (team & individual)
- Replay button

**GameReplay (Interactive)**
- Play/pause controls
- Speed selector (1x, 3x, 10x)
- Current score display
- Play-by-play feed
- Pattern alerts appear at correct time

**PlayerSeasonDashboard**
- Season stats summary
- Shot chart (all games combined)
- Game log table
- AI insights section

---

## AI Analysis Features

### Game-Level AI Insights (Bedrock)

**After pattern detection, call Bedrock to generate:**

```
Prompt: 
"Analyze this Iowa Hawkeyes game vs {opponent}. 

Final Score: Iowa {score}, {opponent} {score}

Detected Patterns:
- Iowa 23-4 run in Q3
- Caitlin Clark hot streak (5 straight makes)

Player Stats:
{box score data}

Provide:
1. Game summary (2-3 sentences)
2. Key moment that decided the game
3. Top performer analysis
4. What this reveals about Iowa's strengths/weaknesses

Format as JSON."
```

**Store in DynamoDB:**
```json
{
  "PK": "GAME#...",
  "SK": "AI#SUMMARY",
  "summary": "Iowa dominated the third quarter...",
  "keyMoment": "23-4 run in Q3 turned a 2-point deficit into a 17-point lead",
  "topPerformer": {
    "name": "Caitlin Clark",
    "statline": "28 PTS / 4 REB / 7 AST",
    "analysis": "Efficient shooting (10-18 FG) and clutch three-pointers"
  },
  "insights": "Iowa's press defense created 8 turnovers in Q3..."
}
```

### Player Season AI Insights

```
Prompt:
"Analyze Caitlin Clark's 2024-25 season performance.

Season Stats: 28.4 PPG, 49% FG, 38% 3P, 7.2 AST

Shot Chart Data:
- Strong: Right wing 3PT (45%), paint (58%)
- Weak: Left baseline (28%)

Game Performance:
- Avg vs ranked opponents: 31.2 PPG
- Avg vs unranked: 26.1 PPG

Provide:
1. Overall assessment
2. Shooting analysis (strengths/weaknesses)
3. Consistency evaluation
4. Areas for improvement

Format as JSON."
```

---

## Implementation Philosophy

### Backend: One-Time Bulk Analysis

**Approach:**
- Download and analyze ALL Iowa games upfront
- Store everything in DynamoDB
- No real-time processing needed for MVP

**Advantages:**
- Always demo-able
- Fast frontend queries
- Can re-analyze games if algorithm improves

**Process:**
1. Run `fetch_iowa_schedule.py` → get game list
2. For each game, run download → replay → analyze
3. Frontend just queries stored data

### Frontend: Display & Interaction

**Approach:**
- Query DynamoDB for pre-analyzed data
- Interactive replay simulates live experience
- No heavy computation in frontend

**User Experience:**
- Fast page loads (data already computed)
- Smooth animations
- Feels "live" even though it's historical

---

## Success Metrics

### MVP Complete When:

✅ All Iowa games for 2024-25 season analyzed  
✅ Game list displays correctly  
✅ Individual game view shows patterns & stats  
✅ Interactive replay works at 3x speed  
✅ At least one player dashboard functional  
✅ AI insights generated for 5+ games  

### Demo-Ready Features:

1. Show season game list
2. Click Iowa @ Baylor game
3. Show detected patterns ("Iowa 12-2 run in Q2")
4. Click replay → watch at 3x speed
5. Show Caitlin Clark season dashboard
6. Display shot chart with AI analysis

---

## Cost Estimation

### One-Time Analysis (28 games)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 500K invocations | $5 |
| DynamoDB | Write 50K items | $2 |
| Bedrock (Analysis) | 28 games × 1000 tokens | $5 |
| S3 | 500MB storage | $0.01 |
| **Total** | | **~$12 one-time** |

### Monthly Ongoing

| Service | Usage | Cost |
|---------|-------|------|
| DynamoDB | 10GB storage | $2.50 |
| API Gateway | 10K requests | $0.04 |
| CloudFront | 10GB transfer | $1 |
| **Total** | | **~$4/month** |

---

## Current Status (December 2024)

### ✅ Completed
- Core infrastructure (AWS, DynamoDB, Kinesis)
- Game replay system
- Pattern detection (runs, hot streaks)
- Player stats tracking
- Shot chart data collection
- Analyzed 3 Iowa games successfully

### 🚧 In Progress
- Season data collection scripts
- Player season aggregation
- Frontend React app

### 📋 To Do
- Bulk season analysis
- AI insights generation
- Interactive replay UI
- Player dashboards
- Shot chart visualization

---

## Next Steps

### Phase 1: Data Collection (Week 1)
1. Build `fetch_iowa_schedule.py`
2. Download all 2024-25 games
3. Bulk replay and analyze
4. Verify data in DynamoDB

### Phase 2: Season Aggregation (Week 2)
1. Build player season summary script
2. Aggregate stats for key players
3. Generate AI insights for top games

### Phase 3: Frontend MVP (Week 3-4)
1. Season selector + game list
2. Individual game view
3. Basic replay functionality
4. One player dashboard

### Phase 4: Polish & Demo (Week 5)
1. Interactive replay improvements
2. Shot chart visualization
3. AI insights display
4. Demo video

---

## Key Design Decisions

**Why Iowa Only?**
- Manageable scope
- Deep insights vs. surface-level tracking
- You know the team intimately
- Better storytelling

**Why Historical First?**
- Always demo-able
- No real-time complexity
- Can perfect analysis before adding live features

**Why Pattern Detection Over Predictions?**
- Pattern detection is deterministic and explainable
- Predictions require training data and are harder to validate
- Patterns tell better stories ("Iowa went on 20-4 run" vs "58% win probability")

**Why Single-Table DynamoDB?**
- Flexible querying
- Cost-effective at scale
- Proven pattern for sports data

---

## Future Enhancements (Post-MVP)

- **Live Game Tracking:** Add EventBridge for real-time games
- **Opponent Comparison:** Compare Iowa vs. specific opponents over time
- **Player Comparison:** Head-to-head player stats
- **Trend Detection:** Identify improving/declining performance
- **Export Features:** Download stats as CSV/PDF
- **Social Sharing:** Share game highlights
- **Multiple Teams:** Add other Big Ten teams

---

## Documentation References

- Original Blueprint: `Blueprint.md`
- Original Timeline: `implementation-timeline.md`
- DynamoDB Access Patterns: See "Access Patterns" section above
- ESPN API Documentation: Reverse-engineered, endpoints listed above

---

**This blueprint is a living document. Update as the project evolves.**