# CourtVision AI - Session Summary
**Date:** December 15, 2024
**Purpose:** Context for next chat session

---

## Project Overview
**CourtVision AI** - Iowa Hawkeyes Women's Basketball Analytics Platform
- Historical game analysis with play-by-play data
- Player statistics and biographies
- Score flow visualization
- Pattern detection (scoring runs, hot streaks)

**Location:** `~/Desktop/AWS/AWS Projects/03-AWS-Courtvision-AI/`

**Live API:** `https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod`

**Frontend Dev:** `cd frontend && npm run dev` → `http://localhost:5173`

---

## Database Schema (CRITICAL)

**Table:** `courtvision-games`
**Region:** `us-east-1`
**Keys:** LOWERCASE `pk` and `sk` (not PK/SK)

### Data Structure:
| pk | sk | Description |
|----|-----|-------------|
| `SEASON#2025` | `GAME#2024-11-07#401713556` | Season game index |
| `SEASON#2026` | `GAME#2025-11-04#401703034` | Season game index |
| `GAME#401713556` | `METADATA` | Game details (frontend uses this) |
| `GAME#401713556` | `DETAILS` | Raw backup |
| `GAME#401713556` | `PLAY#0001` | Individual plays (zero-padded sequence) |
| `PLAYER#12345` | `BIO#2026` | Player biography |
| `SCHEDULE#2026` | (various) | Schedule data |

### Game METADATA Structure:
```json
{
  "pk": "GAME#401703034",
  "sk": "METADATA",
  "game_id": "401703034",
  "season": 2026,
  "date": "2025-11-04T23:00Z",
  "iowa": {
    "team_id": "2294",
    "name": "Iowa Hawkeyes",
    "score": "102",
    "winner": true,
    "home_away": "home",
    "period_scores": ["25", "28", "26", "23"]
  },
  "opponent": {
    "team_id": "2329",
    "name": "Lindenwood Lions",
    "score": "68",
    "winner": false,
    "home_away": "away"
  },
  "venue": {
    "id": "363",
    "name": "Carver-Hawkeye Arena",
    "city": "Iowa City",
    "state": "IA",
    "attendance": 14998
  },
  "player_stats": { "iowa": [...], "opponent": [...] },
  "boxscore": {...}
}
```

### Play Structure:
```json
{
  "pk": "GAME#401703034",
  "sk": "PLAY#0001",
  "sequence": 1,
  "period": 1,
  "clock": "9:45",
  "text": "Hannah Stuelke made Layup",
  "type": "LayUpShot",
  "scoring_play": true,
  "score_value": 2,
  "home_score": 2,
  "away_score": 0,
  "player_id": "4433405",
  "player_name": "Hannah Stuelke"
}
```

### Player Bio Structure:
```json
{
  "pk": "PLAYER#4433405",
  "sk": "BIO#2026",
  "height": "6-2",
  "hometown": "Cedar Rapids, Iowa",
  "high_school": "Cedar Rapids Washington",
  "class_year": "Junior",
  "major": "Sport and Recreation Management",
  "bio_summary": "...",
  "accolades": ["All-Big Ten First Team", "..."]
}
```

---

## Project Tree Structure

```
03-AWS-Courtvision-AI/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BoxScore.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── PlayByPlay.tsx
│   │   │   ├── ScoreBoard.tsx
│   │   │   ├── ScoreFlowChart.tsx      # ✅ Completed this session
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── GamePage.tsx
│   │   │   ├── HomePage.tsx
│   │   │   ├── PlayerDetailPage.tsx
│   │   │   ├── PlayersPage.tsx
│   │   │   └── StatsPage.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── context/
│   │       └── SeasonContext.tsx
│   ├── package.json
│   └── tailwind.config.js
├── backend/
│   ├── lambdas/
│   │   ├── get_games/
│   │   │   └── lambda_function.py
│   │   ├── get_game/
│   │   │   └── lambda_function.py
│   │   ├── get_plays/
│   │   │   └── lambda_function.py      # Has deduplication logic
│   │   └── get_players/
│   │       └── lambda_function.py      # Fetches bios
│   ├── template.yaml                   # SAM template
│   └── samconfig.toml
├── scripts/
│   ├── fetch_schedule.py
│   ├── fetch_game_details.py           # Main data ingestion (has venue extraction)
│   ├── analyze_patterns.py             # ⚠️ NEEDS UPDATE - uses old schema
│   ├── replay_game.py                  # Old replay script (deprecated)
│   └── cleanup_plays_only.py           # Utility to delete duplicate plays
└── docs/
    ├── DECISION_LOG.md
    └── IMPLEMENTATION_TIMELINE.md
```

---

## Completed Features

### This Session:
1. ✅ **Score Flow Chart** (`ScoreFlowChart.tsx`)
   - Recharts LineChart with stepAfter
   - Period markers (Q2, Q3, Q4, OT)
   - Overtime support with "OT", "2OT" labels
   - Fixed duplicate key warning: use `key={period-${marker.period}-${marker.playIndex}}`

2. ✅ **Venue Display** (`ScoreBoard.tsx`)
   - Updated `fetch_game_details.py` with `parse_venue()` function
   - Extracts from `gameInfo.venue` in ESPN API
   - Shows: "📍 Carver-Hawkeye Arena, Iowa City, IA"

3. ✅ **Play-by-Play Ordering** (`PlayByPlay.tsx`)
   - Newest plays at top for both modes
   - Fixed on line 30-32: `const visiblePlays = [...chronologicalPlays].reverse();`

4. ✅ **Player Bios Display** (`PlayerDetailPage.tsx`)
   - Header shows: #55 • G • 5-4 • Sophomore
   - Transfer badge if `previous_school` exists
   - About section with bio, quick facts, accolades

5. ✅ **Duplicate Plays Cleaned**
   - Used `cleanup_plays_only.py` to delete ~12,000 duplicate PLAY# records
   - Re-ran `fetch_game_details.py --force` for both seasons

### Previously Completed:
- Season/game navigation
- Box scores
- Replay mode
- Player statistics aggregation

---

## Next Session: Features To Implement

### 1. Pattern Detection Display (Priority 1)
**Problem:** `analyze_patterns.py` uses OLD schema:
- Uses uppercase `PK`/`SK` (should be lowercase `pk`/`sk`)
- Uses old game ID format `GAME#2024-11-21#IOWA-HAWKEYES-BAYLOR-BEARS`
- Should use `GAME#401713556` format

**Tasks:**
1. Update `analyze_patterns.py` to use correct schema
2. Run analysis on all games to populate patterns
3. Create Lambda endpoint `get_patterns` (or add to `get_game`)
4. Display patterns in GamePage Overview tab

**Pattern Structure (target):**
```json
{
  "pk": "GAME#401713556",
  "sk": "PATTERN#scoring_run#001",
  "pattern_type": "scoring_run",
  "team": "Iowa Hawkeyes",
  "points_for": 12,
  "points_against": 2,
  "description": "Iowa on a 12-2 run",
  "quarter": 2,
  "start_play": 45,
  "end_play": 62
}
```

### 2. Splits Tab (Priority 2)
**Goal:** Show player stats split by:
- Home vs Away
- Conference vs Non-Conference
- By opponent

**Tasks:**
1. Create new Lambda or extend `get_players`
2. Add "Splits" tab to `PlayerDetailPage.tsx`
3. Display comparison tables

### 3. AI Game Summaries + Reddit Sentiment (Priority 3)
**Goal:** Unique differentiator - combine stats with fan sentiment

**Tasks:**
1. Bedrock integration (Claude Haiku) for game summaries
2. Reddit API (PRAW) for r/NCAAW or r/IowaHawkeyes game threads
3. Sentiment analysis of fan comments
4. Display: "📊 AI Analysis" + "🗣️ Fan Pulse" sections

---

## Files To Upload Next Session

### Required:
1. `scripts/analyze_patterns.py` - needs schema update
2. `frontend/src/pages/GamePage.tsx` - add pattern display
3. `frontend/src/pages/PlayerDetailPage.tsx` - add splits tab
4. `frontend/src/types/index.ts` - type definitions
5. `backend/template.yaml` - SAM template for new Lambdas

### Helpful Context:
6. `scripts/fetch_game_details.py` - reference for correct schema
7. `backend/lambdas/get_players/lambda_function.py` - reference for Lambda patterns
8. This summary file

---

## Key Commands

### Backend Deployment:
```bash
cd ~/Desktop/AWS/AWS\ Projects/03-AWS-Courtvision-AI/backend
sam build --use-container && sam deploy
```

### Frontend Development:
```bash
cd ~/Desktop/AWS/AWS\ Projects/03-AWS-Courtvision-AI/frontend
npm run dev
```

### Database Queries:
```bash
# Check game metadata
curl -s "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/games/401703034"

# Count plays for a game
aws dynamodb query \
  --table-name courtvision-games \
  --key-condition-expression "pk = :pk AND begins_with(sk, :play)" \
  --expression-attribute-values '{":pk": {"S": "GAME#401703034"}, ":play": {"S": "PLAY#"}}' \
  --select COUNT \
  --region us-east-1

# Scan for patterns (currently empty)
aws dynamodb scan \
  --table-name courtvision-games \
  --filter-expression "begins_with(sk, :pattern)" \
  --expression-attribute-values '{":pattern": {"S": "PATTERN#"}}' \
  --region us-east-1
```

### Re-fetch Game Data:
```bash
cd ~/Desktop/AWS/AWS\ Projects/03-AWS-Courtvision-AI/scripts
python3 fetch_game_details.py --season 2025 --force
python3 fetch_game_details.py --season 2026 --force
```

---

## Lessons Learned This Session

1. **Always check existing data before updates** - We added duplicate plays by running ingestion twice

2. **Database schema matters** - lowercase `pk`/`sk` vs uppercase `PK`/`SK` caused issues

3. **Venue data location** - ESPN has venue in `gameInfo.venue`, not in competition header

4. **Provide targeted edit instructions** - Instead of rewriting 500-line files, describe:
   - File name
   - Line number or function name
   - Exact code to find
   - Exact replacement code

5. **Test incrementally** - Check database contents after each change

---

## Questions For Next Session

1. Should patterns be stored as separate items (`PATTERN#...`) or embedded in game metadata?
2. For splits, calculate on-the-fly or pre-aggregate?
3. Reddit API - use official API (requires app registration) or unofficial?

---

**End of Summary**