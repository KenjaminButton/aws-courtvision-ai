# CourtVision AI - Project Blueprint

## Project Name: CourtVision AI
**Tagline:** Real-time women's college basketball analytics with AI-powered predictions, commentary, and insights.

---

## Executive Summary

CourtVision AI is a real-time sports analytics platform for women's college basketball. The application ingests live game data from ESPN's hidden API, processes it through an event-driven AWS architecture, and uses AWS Bedrock (Claude) to generate intelligent insights including win probability, natural language commentary, pattern detection, shot charts, and post-game summaries.

**Key Differentiator:** This isn't a CRUD app. It demonstrates real-time streaming, event-driven architecture, AI orchestration, and WebSocket-based live updates—skills that enterprise companies actively seek.

---

## Core Features (All Included)

| Feature | Description | Wow Factor | Difficulty |
|---------|-------------|------------|------------|
| Win Probability | Live percentage that updates as game progresses with AI reasoning | High | Medium |
| AI Commentary | Natural language play-by-play that sounds like a sports broadcaster | Very High | Medium |
| Pattern Detection | Identifies scoring runs, hot/cold streaks, momentum shifts | High | Medium |
| Shot Charts | Visual representation of where players score from on the court | High (visual) | Medium |
| Post-Game Summary | AI-generated 200-word game recap in sports journalism style | Medium | Low |

---

## Data Source Strategy

### Two Operating Modes

The application supports two data modes, controlled by a single environment variable:

```
DATA_SOURCE = "live" | "replay"
```

### Mode 1: Live (Production)

**When to use:** During active basketball season (November - April)

**Data flow:**
```
EventBridge (every 60 seconds)
    ↓
Lambda (fetch from ESPN API)
    ↓
DynamoDB (store game state) + S3 (record for replay)
    ↓
DynamoDB Streams (detect changes)
    ↓
Lambda (AI analysis if significant)
    ↓
API Gateway WebSocket (push to frontend)
    ↓
React Dashboard
```

**ESPN Hidden API Endpoints:**

| Endpoint | URL |
|----------|-----|
| Scoreboard | `https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard` |
| Game Summary | `https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={gameId}` |
| Teams | `https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/teams` |
| Specific Team | `https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/teams/{team}` |

**Query Parameters:**
- `dates=YYYYMMDD` - Filter by specific date
- `groups=50` - Filter by conference
- `limit=100` - Control result count

### Mode 2: Replay (Off-Season / Demos)

**When to use:** Off-season (April - November), demos, interviews, testing

**Data flow:**
```
EventBridge (configurable speed)
    ↓
Lambda (read from S3 recorded game)
    ↓
DynamoDB (store game state)
    ↓
[Same as live mode from here]
```

**Recording Strategy:**
During Mode 1 operation, every ESPN API response is also saved to S3:

```
s3://courtvision-recordings/
├── 2025-12-15-uconn-stanford/
│   ├── metadata.json          # Teams, date, final score
│   ├── plays/
│   │   ├── 000001.json        # First play
│   │   ├── 000002.json        # Second play
│   │   └── ...
│   └── boxscore-final.json    # Final statistics
├── 2025-01-20-lsu-south-carolina/
└── 2025-03-30-ncaa-semifinal/
```

**Replay Speed Control:**
```python
REPLAY_SPEED = os.environ.get("REPLAY_SPEED", 1)  # 1x, 5x, 10x

# Real game: ~30 seconds between plays
# Replay at 10x: ~3 seconds between plays
time.sleep(30 / REPLAY_SPEED)
```

**Priority Games to Record:**
- Close games (margin < 5 points)
- Overtime games
- Star player performances (30+ points, triple-doubles)
- Rivalry matchups (UConn, Stanford, LSU, South Carolina)
- March Madness tournament games

---

## Technical Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA INGESTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐      │
│    │ EventBridge  │─────▶│  Ingestion      │─────▶│   Kinesis Data   │      │
│    │ (60 sec)     │      │  Lambda         │      │   Stream         │      │
│    └──────────────┘      └─────────────────┘      └──────────────────┘      │
│                                 │                          │                 │
│                                 ▼                          │                 │
│                          ┌─────────────┐                   │                 │
│                          │  S3 Bucket  │                   │                 │
│                          │  (recorder) │                   │                 │
│                          └─────────────┘                   │                 │
│                                                            │                 │
├────────────────────────────────────────────────────────────┼─────────────────┤
│                              DATA PROCESSING               │                 │
├────────────────────────────────────────────────────────────┼─────────────────┤
│                                                            │                 │
│                          ┌─────────────────┐               │                 │
│                          │   Processing    │◀──────────────┘                 │
│                          │   Lambda        │                                 │
│                          └─────────────────┘                                 │
│                                 │                                            │
│                                 ▼                                            │
│                          ┌─────────────────┐      ┌──────────────────┐      │
│                          │   DynamoDB      │─────▶│  DynamoDB        │      │
│                          │   (game state)  │      │  Streams         │      │
│                          └─────────────────┘      └──────────────────┘      │
│                                                            │                 │
├────────────────────────────────────────────────────────────┼─────────────────┤
│                              AI ANALYSIS                   │                 │
├────────────────────────────────────────────────────────────┼─────────────────┤
│                                                            │                 │
│                          ┌─────────────────┐               │                 │
│                          │  AI Orchestrator│◀──────────────┘                 │
│                          │  Lambda         │                                 │
│                          └─────────────────┘                                 │
│                                 │                                            │
│              ┌──────────────────┼──────────────────┐                        │
│              ▼                  ▼                  ▼                         │
│    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│    │ Win Probability │ │ AI Commentary   │ │ Pattern Detect  │             │
│    │ (Bedrock)       │ │ (Bedrock)       │ │ (Bedrock)       │             │
│    └─────────────────┘ └─────────────────┘ └─────────────────┘             │
│              │                  │                  │                        │
│              └──────────────────┼──────────────────┘                        │
│                                 ▼                                            │
│                          ┌─────────────────┐                                │
│                          │   DynamoDB      │                                │
│                          │   (AI outputs)  │                                │
│                          └─────────────────┘                                │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                              REAL-TIME DELIVERY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────────────┐      ┌─────────────────┐      ┌──────────────────┐  │
│    │   DynamoDB      │─────▶│  WebSocket      │─────▶│  API Gateway     │  │
│    │   Streams       │      │  Lambda         │      │  WebSocket API   │  │
│    └─────────────────┘      └─────────────────┘      └──────────────────┘  │
│                                                               │              │
│                                                               ▼              │
│                                                      ┌──────────────────┐   │
│                                                      │  React Frontend  │   │
│                                                      │  (S3 + CloudFront)│  │
│                                                      └──────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AWS Services Breakdown

| Service | Purpose | Configuration |
|---------|---------|---------------|
| EventBridge | Schedule data ingestion | Rate: 1 minute during games |
| Lambda (Ingestion) | Fetch from ESPN or S3 | Runtime: Python 3.12, 256MB, 30s timeout |
| Lambda (Processing) | Parse and aggregate stats | Runtime: Python 3.12, 512MB, 60s timeout |
| Lambda (AI Orchestrator) | Decide when to call Bedrock | Runtime: Python 3.12, 256MB, 30s timeout |
| Lambda (AI Workers) | Call Bedrock for each feature | Runtime: Python 3.12, 1024MB, 120s timeout |
| Lambda (WebSocket) | Push updates to connected clients | Runtime: Python 3.12, 256MB, 30s timeout |
| Kinesis Data Stream | Buffer play-by-play events | 1 shard (scale as needed) |
| DynamoDB | Primary database | On-demand capacity, streams enabled |
| S3 | Game recordings, static assets | Standard storage class |
| API Gateway WebSocket | Real-time client connections | $connect, $disconnect, $default routes |
| API Gateway REST | Dashboard API | For initial page load, historical data |
| Bedrock | AI analysis (Claude 3 Sonnet) | claude-3-sonnet model |
| CloudFront | CDN for React frontend | S3 origin |
| Cognito | User authentication | Google OAuth (optional for MVP) |
| CloudWatch | Logging and monitoring | All Lambda functions |

---

## DynamoDB Schema (Single-Table Design)

### Primary Key Structure
- **PK (Partition Key):** Identifies the entity type and primary identifier
- **SK (Sort Key):** Provides sorting and additional filtering

### Access Patterns

| Access Pattern | PK | SK | Description |
|----------------|----|----|-------------|
| Get game metadata | `GAME#{date}#{matchup}` | `METADATA` | Basic game info |
| Get current score | `GAME#{date}#{matchup}` | `SCORE#CURRENT` | Latest score |
| Get score by quarter | `GAME#{date}#{matchup}` | `SCORE#Q{n}` | Quarter scores |
| List all plays | `GAME#{date}#{matchup}` | `PLAY#{timestamp}` | Chronological plays |
| Get win probability | `GAME#{date}#{matchup}` | `AI#WIN_PROB#CURRENT` | Latest probability |
| Win probability history | `GAME#{date}#{matchup}` | `AI#WIN_PROB#{timestamp}` | Historical |
| Get AI commentary | `GAME#{date}#{matchup}` | `AI#COMMENTARY#{timestamp}` | Play commentary |
| Get patterns | `GAME#{date}#{matchup}` | `AI#PATTERN#{timestamp}` | Detected patterns |
| Get shot chart data | `GAME#{date}#{matchup}` | `SHOT#{playerId}#{timestamp}` | Shot locations |
| Get post-game summary | `GAME#{date}#{matchup}` | `AI#SUMMARY` | Game recap |
| Get player stats | `PLAYER#{playerId}` | `GAME#{date}#{matchup}` | Per-game stats |
| List today's games | `DATE#{YYYY-MM-DD}` | `GAME#{matchup}` | Daily schedule |
| WebSocket connections | `WS#CONNECTION` | `{connectionId}` | Active connections |

### Example Items

```json
// Game Metadata
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "METADATA",
  "homeTeam": "UConn",
  "awayTeam": "Stanford",
  "homeTeamId": "41",
  "awayTeamId": "24",
  "venue": "Gampel Pavilion",
  "startTime": "2025-12-15T19:00:00Z",
  "status": "in_progress",
  "quarter": 3,
  "gameClockSeconds": 423,
  "espnGameId": "401593844",
  "createdAt": "2025-12-15T18:30:00Z",
  "updatedAt": "2025-12-15T20:15:00Z"
}

// Current Score
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "SCORE#CURRENT",
  "homeScore": 58,
  "awayScore": 52,
  "quarter": 3,
  "gameClockDisplay": "7:03",
  "lastUpdated": "2025-12-15T20:15:30Z"
}

// Individual Play
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "PLAY#2025-12-15T20:14:55Z#0142",
  "playId": "0142",
  "timestamp": "2025-12-15T20:14:55Z",
  "quarter": 3,
  "gameClock": "7:23",
  "team": "UConn",
  "playerId": "4433218",
  "playerName": "Paige Bueckers",
  "action": "made_three_pointer",
  "description": "Paige Bueckers made Three Point Jumper",
  "homeScore": 58,
  "awayScore": 52,
  "scoringPlay": true,
  "pointsScored": 3,
  "shotLocation": { "x": 25, "y": 8 },
  "assisted": true,
  "assistPlayerId": "4433220"
}

// Win Probability (Current)
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "AI#WIN_PROB#CURRENT",
  "homeWinProbability": 0.68,
  "awayWinProbability": 0.32,
  "reasoning": "UConn's 6-point lead midway through Q3, combined with their strong home record (12-1) and Bueckers' hot shooting (22 points), gives them a comfortable edge. Stanford will need to improve their 28% three-point shooting to mount a comeback.",
  "triggerEvent": "Bueckers third three-pointer extends lead to 6",
  "calculatedAt": "2025-12-15T20:15:02Z"
}

// AI Commentary
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "AI#COMMENTARY#2025-12-15T20:14:58Z",
  "playId": "0142",
  "commentary": "Bueckers pulls up from beyond the arc and drains her third triple of the night! She's absolutely scorching from deep with 22 points, and the Gampel crowd is on its feet!",
  "excitement": 0.85,
  "generatedAt": "2025-12-15T20:14:58Z"
}

// Pattern Detection
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "AI#PATTERN#2025-12-15T20:12:00Z",
  "patternType": "scoring_run",
  "description": "UConn on a 9-2 run over the last 3:24",
  "team": "UConn",
  "startTime": "2025-12-15T20:08:36Z",
  "pointsFor": 9,
  "pointsAgainst": 2,
  "significance": "high",
  "detectedAt": "2025-12-15T20:12:00Z"
}

// Shot Chart Entry
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "SHOT#4433218#2025-12-15T20:14:55Z",
  "playerId": "4433218",
  "playerName": "Paige Bueckers",
  "team": "UConn",
  "x": 25,
  "y": 8,
  "made": true,
  "shotType": "three_pointer",
  "quarter": 3,
  "timestamp": "2025-12-15T20:14:55Z"
}

// Post-Game Summary
{
  "PK": "GAME#2025-12-15#UCONN-STANFORD",
  "SK": "AI#SUMMARY",
  "summary": "In a marquee non-conference clash, UConn outlasted Stanford 78-71 at Gampel Pavilion behind Paige Bueckers' spectacular 32-point performance. The Huskies used a decisive 14-4 third-quarter run to take control after trailing by three at halftime. Bueckers connected on 6-of-9 from three-point range and added 7 assists, orchestrating the offense with precision. Stanford's Kiki Iriafen kept the Cardinal close with 24 points and 11 rebounds, but UConn's defense clamped down in the final five minutes, holding Stanford to just 2-of-9 shooting. The victory extends UConn's home winning streak to 23 games and cements their status as a national title contender.",
  "keyStats": {
    "topPerformer": { "name": "Paige Bueckers", "team": "UConn", "points": 32, "assists": 7 },
    "turningPoint": "14-4 UConn run in Q3",
    "biggestLead": { "team": "UConn", "margin": 12 }
  },
  "generatedAt": "2025-12-15T21:45:00Z"
}

// WebSocket Connection
{
  "PK": "WS#CONNECTION",
  "SK": "abc123xyz",
  "connectionId": "abc123xyz",
  "gameId": "GAME#2025-12-15#UCONN-STANFORD",
  "connectedAt": "2025-12-15T19:58:00Z",
  "ttl": 1734300000
}
```

### Global Secondary Indexes (GSIs)

| GSI Name | PK | SK | Purpose |
|----------|----|----|---------|
| GSI1 | `GSI1PK` | `GSI1SK` | Query by date, status |
| GSI2 | `playerId` | `timestamp` | Player stats across games |

---

## Feature Specifications

### Feature 1: Win Probability

**Description:** Calculate and display real-time win probability for each team, updating when significant events occur.

**Trigger Conditions (when to recalculate):**
- Score changes
- Quarter/half transitions
- Lead changes
- Significant scoring runs (8+ point run)
- Final 2 minutes of each half
- Overtime periods

**Bedrock Prompt:**
```
You are a sports analytics expert calculating win probability for a women's college basketball game.

Current Game State:
- Home Team: {home_team} (Score: {home_score})
- Away Team: {away_team} (Score: {away_score})
- Time Remaining: {quarter} quarter, {time_remaining}
- Recent Trend: {recent_scoring_description}
- Home Team Shooting: {home_fg_pct}% FG, {home_3pt_pct}% 3PT
- Away Team Shooting: {away_fg_pct}% FG, {away_3pt_pct}% 3PT
- Fouls: Home {home_fouls}, Away {away_fouls}
- Timeouts: Home {home_timeouts}, Away {away_timeouts}

Based on this game state, calculate the win probability for each team.

Respond in this exact JSON format:
{
  "home_probability": <float between 0 and 1>,
  "away_probability": <float between 0 and 1>,
  "reasoning": "<2-3 sentence explanation of the key factors>"
}

Consider: score differential, time remaining, momentum, shooting percentages, and historical comeback data. The probabilities must sum to 1.0.
```

**Expected Response:**
```json
{
  "home_probability": 0.68,
  "away_probability": 0.32,
  "reasoning": "UConn's 6-point lead with 15 minutes remaining gives them a solid advantage. Their superior three-point shooting (42% vs 28%) and Bueckers' hot hand suggest they can extend the lead. Stanford historically struggles to close large gaps on the road."
}
```

**Testing Strategy:**

| Test Case | Input Scenario | Expected Outcome |
|-----------|----------------|------------------|
| Blowout | 20+ point lead, Q4 | >95% for leading team |
| Tie game | Tied score, Q3 | ~50% each, slight home edge |
| Close finish | 2-point lead, 30 seconds left | 60-70% for leading team |
| Comeback setup | Down 10, start of Q4 | 25-35% for trailing team |
| Overtime | Tied, OT starts | ~52% home, ~48% away |

**Mode 1 Testing:** Run during live games, verify probabilities feel intuitively correct.

**Mode 2 Testing:** Replay known games, compare AI probabilities to actual outcomes.

---

### Feature 2: AI Commentary

**Description:** Generate natural, exciting play-by-play commentary that sounds like a sports broadcaster.

**Trigger Conditions (when to generate):**
- Every scoring play
- Blocks and steals
- Turnovers in crucial moments
- Players reaching milestones (10, 20, 30 points; double-doubles)
- Quarter endings
- Timeout returns with context

**Bedrock Prompt:**
```
You are an enthusiastic women's college basketball commentator. Generate exciting play-by-play commentary for this event.

Play Details:
- Player: {player_name} ({team})
- Action: {action_type}
- Description: {espn_description}
- Points (if scoring): {points}
- Current Score: {home_team} {home_score} - {away_team} {away_score}

Game Context:
- Quarter: {quarter}, Time: {game_clock}
- Player's Game Stats: {player_points} PTS, {player_rebounds} REB, {player_assists} AST
- Recent Context: {recent_plays_summary}

Generate 1-2 sentences of natural, exciting commentary. Match the excitement level to the play's significance. Avoid clichés like "nothing but net" or "on fire." Be specific about what makes this play meaningful.

Respond in JSON format:
{
  "commentary": "<your commentary>",
  "excitement": <float 0-1, where 1 is most exciting>
}
```

**Expected Response:**
```json
{
  "commentary": "Bueckers rises up from the left wing and splashes her fourth three of the quarter! That's 24 points for the junior guard, and Stanford is calling timeout to stop the bleeding.",
  "excitement": 0.82
}
```

**Testing Strategy:**

| Test Case | Input Scenario | Expected Outcome |
|-----------|----------------|------------------|
| Routine basket | Layup, mid-game, no streak | Low excitement, factual |
| Hot streak | 4th three-pointer in a row | High excitement, mention streak |
| Milestone | Player hits 30 points | Reference milestone explicitly |
| Clutch moment | Go-ahead basket, under 1 minute | Maximum excitement |
| Defensive play | Block on potential game-tying shot | High excitement, defensive focus |

**Quality Checks:**
- No hallucinated player names
- Stats match actual game state
- Variety in sentence structure (not repetitive)
- Appropriate excitement calibration

---

### Feature 3: Pattern Detection

**Description:** Identify and alert users to meaningful game patterns as they develop.

**Patterns to Detect:**

| Pattern | Definition | Significance |
|---------|------------|--------------|
| Scoring Run | 8+ unanswered points or 10-2 differential | High |
| Cold Streak | Team scores <4 points in 5+ minutes | Medium |
| Hot Shooting | Player 4+ consecutive made shots | High |
| Momentum Shift | Lead change after 5+ point deficit | Very High |
| Foul Trouble | Key player with 3+ fouls before Q4 | Medium |
| Milestone Alert | Player approaching double-double, 30+ points | Medium |

**Detection Logic (Lambda):**
```python
def detect_patterns(game_state, recent_plays):
    patterns = []
    
    # Scoring run detection
    last_n_plays = recent_plays[-15:]  # Last 15 plays
    home_points = sum(p['pointsScored'] for p in last_n_plays if p['team'] == game_state['homeTeam'] and p.get('scoringPlay'))
    away_points = sum(p['pointsScored'] for p in last_n_plays if p['team'] == game_state['awayTeam'] and p.get('scoringPlay'))
    
    if home_points >= 10 and away_points <= 2:
        patterns.append({
            'type': 'scoring_run',
            'team': game_state['homeTeam'],
            'description': f"{game_state['homeTeam']} on a {home_points}-{away_points} run"
        })
    
    # Similar logic for other patterns...
    
    return patterns
```

**Bedrock Prompt (for enriched descriptions):**
```
Analyze this basketball pattern and provide context.

Pattern Detected: {pattern_type}
Details: {pattern_details}
Game Context: {game_context}

Respond in JSON:
{
  "description": "<1 sentence describing the pattern>",
  "significance": "<why this matters>",
  "historical_context": "<optional: similar situations>"
}
```

**Testing Strategy:**

| Test Case | Simulated Scenario | Expected Detection |
|-----------|-------------------|-------------------|
| Clear run | 12-0 run over 8 plays | Scoring run alert |
| Borderline run | 8-3 run | Scoring run (meets threshold) |
| No run | 8-6 differential | No alert |
| Hot shooter | Player makes 5 straight | Hot shooting alert |
| Foul trouble | Star with 4 fouls in Q3 | Foul trouble alert |

---

### Feature 4: Shot Charts

**Description:** Visual representation of where players take and make shots on the court.

**Data Required:**
- Shot location (x, y coordinates from ESPN)
- Shot result (made/missed)
- Shot type (layup, mid-range, three-pointer)
- Player ID
- Timestamp

**ESPN Shot Location Data:**
ESPN provides shot coordinates in their play-by-play. The court is represented as:
- X: 0-50 (half-court width in feet)
- Y: 0-47 (half-court length in feet)
- Origin (0,0): Baseline corner

**Data Transformation:**
```python
def transform_shot_for_chart(espn_shot):
    return {
        'x': espn_shot['coordinate']['x'],
        'y': espn_shot['coordinate']['y'],
        'made': espn_shot['scoringPlay'],
        'type': classify_shot_type(espn_shot),
        'player': espn_shot['playerName'],
        'playerId': espn_shot['playerId']
    }

def classify_shot_type(shot):
    x, y = shot['coordinate']['x'], shot['coordinate']['y']
    distance = calculate_distance_from_basket(x, y)
    
    if distance <= 4:
        return 'layup'
    elif distance <= 22:  # Inside three-point line
        return 'mid_range'
    else:
        return 'three_pointer'
```

**Frontend Component (React):**
```jsx
// Shot chart using D3.js or custom SVG
const ShotChart = ({ shots, playerId }) => {
  const playerShots = shots.filter(s => s.playerId === playerId);
  
  return (
    <svg viewBox="0 0 500 470" className="shot-chart">
      {/* Court background */}
      <Court />
      
      {/* Shot markers */}
      {playerShots.map(shot => (
        <circle
          key={shot.timestamp}
          cx={shot.x * 10}
          cy={shot.y * 10}
          r={8}
          fill={shot.made ? '#22c55e' : '#ef4444'}
          opacity={0.7}
        />
      ))}
    </svg>
  );
};
```

**Testing Strategy:**

| Test Case | Scenario | Validation |
|-----------|----------|------------|
| Shot placement | Various coordinates | Shots render in correct positions |
| Made vs missed | Mix of results | Green for made, red for missed |
| Three-point accuracy | Shots beyond arc | Correctly classified as 3PT |
| Player filter | Select specific player | Only their shots display |
| Empty state | Game just started | Shows court with no shots |

---

### Feature 5: Post-Game Summary

**Description:** Automatically generate a professional 200-word game recap after the final buzzer.

**Trigger:** Game status changes to "final"

**Bedrock Prompt:**
```
You are a professional sports journalist writing a game recap for a women's college basketball game.

Final Score: {home_team} {home_score} - {away_team} {away_score}

Box Score:
{formatted_box_score}

Key Plays:
{key_plays_list}

Win Probability Swings:
{probability_timeline_summary}

Detected Patterns:
{patterns_list}

Write a 200-word game recap in professional sports journalism style. Include:
1. Opening with final score and significance
2. The game's turning point
3. Top performer(s) with specific stats
4. Key storyline or matchup that defined the game
5. Brief mention of what this means going forward

Respond in JSON:
{
  "summary": "<200-word recap>",
  "headline": "<catchy 8-12 word headline>",
  "top_performer": {
    "name": "<player name>",
    "team": "<team>",
    "statline": "<points/rebounds/assists>"
  },
  "turning_point": "<brief description>"
}
```

**Expected Output:**
```json
{
  "summary": "Paige Bueckers delivered a masterclass performance, pouring in 32 points to lead UConn past Stanford 78-71 at Gampel Pavilion on Sunday night. The Huskies trailed 38-35 at halftime before Bueckers ignited a decisive 14-4 run midway through the third quarter that flipped the game's momentum...",
  "headline": "Bueckers' 32-Point Explosion Powers UConn Past Stanford",
  "top_performer": {
    "name": "Paige Bueckers",
    "team": "UConn",
    "statline": "32 PTS / 4 REB / 7 AST"
  },
  "turning_point": "14-4 UConn run in the third quarter erased a 3-point halftime deficit"
}
```

**Testing Strategy:**

| Test Case | Scenario | Validation |
|-----------|----------|------------|
| Blowout | 25-point margin | Summary focuses on dominance |
| Nail-biter | 2-point margin, lead changes | Emphasizes drama, clutch plays |
| Overtime | OT finish | Mentions OT, extra period drama |
| Stat accuracy | Various box scores | All referenced stats are correct |
| Length | Any game | Summary is 180-220 words |

---

## Lambda Function Specifications

### 1. Ingestion Lambda (`courtvision-ingest`)

**Purpose:** Fetch data from ESPN API (live) or S3 (replay)

**Trigger:** EventBridge (every 60 seconds during active games)

**Environment Variables:**
```
DATA_SOURCE=live|replay
REPLAY_GAME_ID=GAME#2025-12-15#UCONN-STANFORD  (only for replay mode)
REPLAY_SPEED=1
ESPN_BASE_URL=https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball
KINESIS_STREAM_NAME=courtvision-plays
S3_RECORDING_BUCKET=courtvision-recordings
```

**Logic:**
```python
def handler(event, context):
    data_source = os.environ['DATA_SOURCE']
    
    if data_source == 'live':
        games = fetch_live_games()
        for game in games:
            plays = fetch_game_plays(game['espnGameId'])
            
            # Record to S3 for future replay
            record_to_s3(game, plays)
            
            # Send to Kinesis for processing
            send_to_kinesis(plays)
    
    elif data_source == 'replay':
        game_id = os.environ['REPLAY_GAME_ID']
        next_play = get_next_replay_play(game_id)
        send_to_kinesis([next_play])
```

### 2. Processing Lambda (`courtvision-process`)

**Purpose:** Parse plays, update game state, aggregate statistics

**Trigger:** Kinesis Data Stream

**Logic:**
```python
def handler(event, context):
    for record in event['Records']:
        play = parse_kinesis_record(record)
        
        # Update current score
        update_score(play)
        
        # Update player stats
        update_player_stats(play)
        
        # Store play
        store_play(play)
        
        # Store shot for shot chart (if applicable)
        if play.get('shotLocation'):
            store_shot(play)
```

### 3. AI Orchestrator Lambda (`courtvision-ai-orchestrator`)

**Purpose:** Decide when to trigger AI analysis

**Trigger:** DynamoDB Streams

**Logic:**
```python
def handler(event, context):
    for record in event['Records']:
        if record['eventName'] in ['INSERT', 'MODIFY']:
            item = record['dynamodb']['NewImage']
            
            # Check if this change warrants AI analysis
            if should_analyze(item):
                trigger_type = determine_analysis_type(item)
                
                # Invoke appropriate AI Lambda(s)
                if 'scoring_play' in trigger_type:
                    invoke_lambda('courtvision-ai-commentary', item)
                
                if 'significant_event' in trigger_type:
                    invoke_lambda('courtvision-ai-winprob', get_game_state(item))
                
                # Always check for patterns
                invoke_lambda('courtvision-ai-patterns', get_recent_plays(item))

def should_analyze(item):
    """Determine if this DynamoDB change warrants AI analysis"""
    sk = item['SK']['S']
    
    # Analyze scoring plays
    if sk.startswith('PLAY#') and item.get('scoringPlay', {}).get('BOOL'):
        return True
    
    # Analyze quarter changes
    if sk == 'SCORE#CURRENT' and quarter_changed(item):
        return True
    
    # Analyze game end
    if sk == 'METADATA' and item.get('status', {}).get('S') == 'final':
        return True
    
    return False
```

### 4. AI Commentary Lambda (`courtvision-ai-commentary`)

**Purpose:** Generate natural language commentary

**Trigger:** Invoked by AI Orchestrator

**Logic:**
```python
def handler(event, context):
    play = event['play']
    game_context = event['game_context']
    
    prompt = build_commentary_prompt(play, game_context)
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 200,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    commentary = parse_response(response)
    
    # Store commentary
    store_commentary(play['gameId'], play['playId'], commentary)
    
    # Push to WebSocket clients
    push_to_websocket(play['gameId'], {
        'type': 'commentary',
        'data': commentary
    })
```

### 5. WebSocket Lambda (`courtvision-websocket`)

**Purpose:** Manage WebSocket connections and push updates

**Trigger:** DynamoDB Streams (AI outputs table)

**Routes:**
- `$connect`: Store connection in DynamoDB
- `$disconnect`: Remove connection from DynamoDB
- `subscribe`: Associate connection with specific game
- `$default`: Handle incoming messages

**Logic:**
```python
def handle_connect(event, context):
    connection_id = event['requestContext']['connectionId']
    store_connection(connection_id)
    return {'statusCode': 200}

def handle_subscribe(event, context):
    connection_id = event['requestContext']['connectionId']
    body = json.loads(event['body'])
    game_id = body['gameId']
    
    update_connection_game(connection_id, game_id)
    
    # Send current game state
    game_state = get_current_game_state(game_id)
    send_to_connection(connection_id, game_state)
    
    return {'statusCode': 200}

def push_update(game_id, update):
    connections = get_connections_for_game(game_id)
    
    for conn in connections:
        try:
            send_to_connection(conn['connectionId'], update)
        except GoneException:
            delete_connection(conn['connectionId'])
```

---

## Frontend Specification (React)

### Tech Stack
- React 18 + TypeScript
- Tailwind CSS for styling
- Recharts for data visualization (win probability graph)
- D3.js for shot charts
- Native WebSocket API for real-time updates

### Page Structure

```
/                     → Dashboard (list of today's games)
/game/:gameId         → Live game view
/game/:gameId/summary → Post-game summary view
```

### Key Components

```
src/
├── components/
│   ├── GameCard.tsx           # Game preview card for dashboard
│   ├── LiveScore.tsx          # Current score display
│   ├── WinProbabilityBar.tsx  # Visual probability bar
│   ├── WinProbabilityGraph.tsx # Historical probability chart
│   ├── PlayFeed.tsx           # Scrolling play-by-play
│   ├── AICommentary.tsx       # AI-generated commentary display
│   ├── PatternAlert.tsx       # Pattern detection notifications
│   ├── ShotChart.tsx          # D3-based shot visualization
│   ├── BoxScore.tsx           # Traditional box score table
│   └── GameSummary.tsx        # Post-game AI summary
├── hooks/
│   ├── useWebSocket.ts        # WebSocket connection management
│   ├── useGameState.ts        # Game state management
│   └── useRealtimeUpdates.ts  # Process incoming updates
├── pages/
│   ├── Dashboard.tsx          # Home page with game list
│   ├── GameView.tsx           # Live game page
│   └── Summary.tsx            # Post-game summary page
└── utils/
    ├── api.ts                 # REST API calls
    └── transforms.ts          # Data transformation helpers
```

### WebSocket Integration

```typescript
// hooks/useWebSocket.ts
export function useWebSocket(gameId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<GameUpdate | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(WS_ENDPOINT);
    
    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ action: 'subscribe', gameId }));
    };
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setLastUpdate(update);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      // Implement reconnection logic
    };
    
    return () => ws.close();
  }, [gameId]);
  
  return { isConnected, lastUpdate };
}
```

---

## Testing Strategy Summary

### By Feature

| Feature | Unit Tests | Integration Tests | Mode 1 Tests | Mode 2 Tests |
|---------|-----------|------------------|--------------|--------------|
| Win Probability | Prompt formatting, probability math | Bedrock integration | Live game validation | Historical accuracy |
| AI Commentary | Prompt formatting, JSON parsing | Bedrock integration | Live commentary quality | Replay variety check |
| Pattern Detection | Detection algorithms | End-to-end detection | Live pattern accuracy | Forced scenario tests |
| Shot Charts | Coordinate transforms | Data flow to frontend | Live rendering | Historical games |
| Post-Game Summary | Prompt formatting | Bedrock integration | Live game summaries | Multiple game types |

### By Mode

**Mode 1 (Live) Testing Checklist:**
- [ ] ESPN API returns valid data
- [ ] Kinesis receives and buffers plays
- [ ] DynamoDB updates correctly
- [ ] AI triggers fire on correct events
- [ ] WebSocket pushes reach clients < 2 seconds
- [ ] Frontend renders updates smoothly
- [ ] Game recorder saves to S3

**Mode 2 (Replay) Testing Checklist:**
- [ ] S3 game data loads correctly
- [ ] Replay speed control works (1x, 5x, 10x)
- [ ] Play sequence maintains order
- [ ] All features work identically to live mode
- [ ] Can pause and resume replay
- [ ] Multiple concurrent replays supported

---

## Implementation Timeline

### Month 1: Foundation + Data Pipeline

**Week 1: Infrastructure Setup**
- [ ] Create AWS account structure (dev/prod)
- [ ] Set up CDK or SAM for infrastructure as code
- [ ] Create DynamoDB table with schema
- [ ] Set up S3 buckets (recordings, frontend)
- [ ] Configure CloudWatch logging

**Week 2: Data Ingestion**
- [ ] Build Ingestion Lambda (Mode 1 - ESPN)
- [ ] Test ESPN API endpoints
- [ ] Set up EventBridge schedule
- [ ] Implement game recorder (save to S3)
- [ ] Create Kinesis Data Stream

**Week 3: Data Processing**
- [ ] Build Processing Lambda
- [ ] Parse ESPN play-by-play format
- [ ] Update game state in DynamoDB
- [ ] Aggregate player statistics
- [ ] Enable DynamoDB Streams

**Week 4: Real-Time Delivery**
- [ ] Set up API Gateway WebSocket
- [ ] Build WebSocket Lambda (connect/disconnect/subscribe)
- [ ] Implement push notifications
- [ ] Basic React frontend (score display only)
- [ ] Test end-to-end data flow

**Month 1 Deliverable:** Live scores updating in React via WebSocket

---

### Month 2: AI Features

**Week 5: Win Probability**
- [ ] Set up Bedrock access
- [ ] Build AI Orchestrator Lambda
- [ ] Create Win Probability Lambda
- [ ] Design and test prompts
- [ ] Store probability in DynamoDB
- [ ] Push probability updates via WebSocket
- [ ] Frontend: probability bar component

**Week 6: AI Commentary**
- [ ] Build Commentary Lambda
- [ ] Create commentary prompts
- [ ] Test with various play types
- [ ] Implement excitement calibration
- [ ] Frontend: commentary feed component

**Week 7: Pattern Detection**
- [ ] Build Pattern Detection Lambda
- [ ] Implement scoring run detection
- [ ] Implement hot streak detection
- [ ] Implement momentum shift detection
- [ ] Frontend: pattern alert component

**Week 8: Shot Charts**
- [ ] Parse shot location data from ESPN
- [ ] Store shots in DynamoDB
- [ ] Build shot chart API endpoint
- [ ] Frontend: D3.js shot chart component
- [ ] Player filter functionality

**Month 2 Deliverable:** All AI features working against live games

---

### Month 3: Polish + Replay Mode

**Week 9: Post-Game Summary**
- [ ] Build Summary Lambda
- [ ] Trigger on game completion
- [ ] Create summary prompts
- [ ] Frontend: summary page
- [ ] Historical summary access

**Week 10: Replay Mode**
- [ ] Build replay data loader
- [ ] Implement speed control
- [ ] Test all features in replay mode
- [ ] Record priority games (if in season)
- [ ] Create demo game library

**Week 11: Polish**
- [ ] Error handling and retries
- [ ] Loading states and skeletons
- [ ] Mobile responsiveness
- [ ] Performance optimization
- [ ] Rate limiting and caching

**Week 12: Documentation + Demo Prep**
- [ ] Architecture documentation
- [ ] README with setup instructions
- [ ] Record demo video
- [ ] Prepare interview talking points
- [ ] Cost analysis documentation

**Month 3 Deliverable:** Production-ready application with demo capabilities

---

## Cost Estimation

### Monthly Costs (Estimated at moderate usage)

| Service | Usage Estimate | Cost |
|---------|---------------|------|
| Lambda | 500K invocations | ~$5 |
| DynamoDB | 5GB storage, on-demand | ~$10 |
| Kinesis | 1 shard | ~$15 |
| Bedrock (Claude Sonnet) | 100K input + 50K output tokens | ~$20 |
| API Gateway | WebSocket connections | ~$5 |
| S3 | 10GB recordings | ~$1 |
| CloudFront | 50GB transfer | ~$5 |
| **Total** | | **~$60/month** |

### Cost Optimization Strategies
1. Cache AI responses for identical game states
2. Batch AI calls when possible
3. Use DynamoDB TTL to auto-delete old WebSocket connections
4. Implement request throttling on Bedrock calls
5. Use S3 Intelligent Tiering for old recordings

---

## Interview Talking Points

### Architecture Decisions

**Q: Why Kinesis instead of direct Lambda-to-DynamoDB?**
A: "Kinesis provides buffering for bursty play-by-play data. During fast-paced game moments, we might get 10 plays in 30 seconds. Kinesis handles the spikes while letting my processing Lambda work at a steady pace. It also gives me replay capability for debugging."

**Q: Why DynamoDB Streams for AI triggers instead of direct invocation?**
A: "Decoupling. The Processing Lambda shouldn't know or care about AI analysis. DynamoDB Streams let me add new AI features without modifying the data pipeline. It's also more resilient—if my AI Lambda fails, the data is still safely stored."

**Q: How do you handle WebSocket disconnections?**
A: "Three strategies: First, TTL on connection records so stale connections auto-delete. Second, graceful handling of GoneException when pushing updates. Third, client-side reconnection with exponential backoff and state reconciliation on reconnect."

### Scaling Considerations

**Q: How would you scale this to 10,000 concurrent users?**
A: "The architecture already supports it. Lambda scales automatically. DynamoDB on-demand handles the read/write spikes. The main bottleneck would be WebSocket connections—I'd add connection pooling and potentially fan out through SNS. For Bedrock, I'd implement aggressive caching since the same game state produces the same probability."

**Q: What about multiple simultaneous games?**
A: "Already handled. Each game has its own partition key in DynamoDB, so there's no contention. WebSocket connections are tagged with game IDs, so updates only go to relevant clients. The only shared resource is the Kinesis stream, which I'd scale by adding shards."

---

## Appendix: ESPN API Response Examples

### Scoreboard Response
```json
{
  "events": [
    {
      "id": "401593844",
      "date": "2025-12-15T00:00Z",
      "name": "Stanford Cardinal at Connecticut Huskies",
      "shortName": "STAN @ CONN",
      "competitions": [
        {
          "id": "401593844",
          "date": "2025-12-15T00:00Z",
          "competitors": [
            {
              "id": "41",
              "homeAway": "home",
              "team": {
                "id": "41",
                "name": "Huskies",
                "displayName": "Connecticut Huskies",
                "abbreviation": "CONN"
              },
              "score": "58"
            },
            {
              "id": "24",
              "homeAway": "away",
              "team": {
                "id": "24",
                "name": "Cardinal",
                "displayName": "Stanford Cardinal",
                "abbreviation": "STAN"
              },
              "score": "52"
            }
          ],
          "status": {
            "type": {
              "name": "STATUS_IN_PROGRESS",
              "state": "in"
            },
            "period": 3,
            "displayClock": "7:03"
          }
        }
      ]
    }
  ]
}
```

### Play-by-Play Response (Summary Endpoint)
```json
{
  "plays": [
    {
      "id": "4015938440142",
      "sequenceNumber": "0142",
      "type": {
        "id": "558",
        "text": "Three Point Jumper"
      },
      "text": "Paige Bueckers made Three Point Jumper. Assisted by Azzi Fudd.",
      "period": {
        "number": 3
      },
      "clock": {
        "displayValue": "7:23"
      },
      "team": {
        "id": "41"
      },
      "scoringPlay": true,
      "scoreValue": 3,
      "coordinate": {
        "x": 25,
        "y": 8
      },
      "participants": [
        {
          "athlete": {
            "id": "4433218",
            "displayName": "Paige Bueckers"
          },
          "type": "scorer"
        },
        {
          "athlete": {
            "id": "4433220",
            "displayName": "Azzi Fudd"
          },
          "type": "assist"
        }
      ],
      "homeScore": 58,
      "awayScore": 52
    }
  ]
}
```

---

## Final Notes

This blueprint is designed to be comprehensive enough to build from, but flexible enough to adapt as you learn more during development. Start with Month 1's deliverable (live scores in a React app) before adding AI complexity.

**Remember:** A polished demo of 70% of features beats a broken demo of 100%. Focus on reliability first, then add wow factor.

Good luck! 🏀