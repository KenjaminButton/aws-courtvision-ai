# CourtVision AI - Session Handoff Document
**Date:** December 16, 2024
**Project:** Iowa Hawkeyes Women's Basketball Analytics Platform

---

## 🎯 CRITICAL INSTRUCTIONS FOR NEXT SESSION

**READ THIS FIRST, CLAUDE:**
1. **Take SMALL steps** - One file, one feature at a time
2. **Verify before changing** - Always `cat` or `grep` the actual file before editing
3. **Don't guess field names** - Query DynamoDB to confirm schema
4. **Test each change** - Don't stack multiple untested changes
5. **Ask before major changes** - User prefers discussion over surprise rewrites

---

## 📁 Project Structure

```
~/Desktop/AWS/AWS Projects/03-AWS-Courtvision-AI/
├── frontend/                     # React + TypeScript + Vite
│   └── src/
│       ├── components/           # UI components
│       │   ├── BoxScore.tsx
│       │   ├── GameCard.tsx
│       │   ├── Header.tsx
│       │   ├── LoadingStates.tsx
│       │   ├── PatternBadge.tsx
│       │   ├── PlayByPlay.tsx
│       │   ├── ScoreBoard.tsx
│       │   └── ScoreFlowChart.tsx
│       ├── contexts/
│       │   └── SeasonContext.tsx  # Season selector (2025 or 2026)
│       ├── hooks/
│       │   └── useApi.ts          # Data fetching hooks
│       ├── pages/
│       │   ├── GamePage.tsx       # Individual game view
│       │   ├── HomePage.tsx       # Games list
│       │   ├── PlayerDetailPage.tsx
│       │   ├── PlayersPage.tsx
│       │   └── StatsPage.tsx      # NEW - Season stats
│       ├── services/
│       │   └── api.ts             # API client
│       └── types/
│           └── index.ts           # TypeScript types
│
├── backend/                       # AWS SAM
│   ├── template.yaml              # SAM template
│   └── lambdas/
│       ├── get_games/
│       ├── get_game_detail/
│       ├── get_plays/
│       ├── get_players/
│       └── get_season_stats/      # NEW
│
├── scripts/                       # Python scripts
│   ├── fetch_schedule.py          # Fetch Iowa schedule from ESPN
│   ├── fetch_game_details.py      # Fetch play-by-play from ESPN
│   └── analyze_patterns_v2.py     # Detect scoring runs & hot streaks
│
└── docs/
    ├── DECISION_LOG.md
    └── IMPLEMENTATION_TIMELINE.md
```

---

## 🗄️ DynamoDB Schema

**Table:** `courtvision-games` (us-east-1)
**Keys:** lowercase `pk`, `sk`

### Record Types:

**SEASON Index:**
```
pk: SEASON#2026
sk: GAME#2025-11-04#401818626
Fields: game_id, iowa_score, opponent_score, iowa_won, opponent_abbrev, 
        short_name, status_completed, details_fetched, reddit_thread_url*, youtube_postgame_url*
```
*Fields to be added for next feature

**GAME Metadata:**
```
pk: GAME#401818635
sk: METADATA
Fields: game_id, iowa{}, opponent{}, venue{}, boxscore{}, player_stats{},
        conference_competition, play_count, date, status
```

**PLAY Records:**
```
pk: GAME#401818635
sk: PLAY#0001 (or PLAY#115810692 for some games)
Fields: game_id, sequence, period, clock, text, player_name, player_id,
        team_id, home_score, away_score, scoring_play, coordinate_x/y
```

**PATTERN Records:**
```
pk: GAME#401818635
sk: PATTERN#scoring_run#001 or PATTERN#hot_streak#001
Fields: pattern_type, team, team_id, is_iowa, description, period,
        [scoring_run]: points_for, points_against
        [hot_streak]: player_name, player_id, consecutive_makes
```

---

## 🌐 API Endpoints

**Base URL:** `https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod`

| Endpoint | Lambda | Description |
|----------|--------|-------------|
| GET /games?season=2026 | get_games | List all games for season |
| GET /games/{gameId} | get_game_detail | Game metadata + patterns |
| GET /games/{gameId}/plays | get_plays | All plays for game |
| GET /players?season=2026 | get_players | Aggregated player stats |
| GET /stats?season=2026 | get_season_stats | Season stats, splits, patterns |

---

## ✅ What We Accomplished This Session

1. **Fixed Pattern Detection**
   - Updated `fetch_game_details.py` to extract player names from play text
   - Updated `analyze_patterns_v2.py` with text extraction fallback
   - Re-ingested all games with proper player_name field

2. **Fixed ScoreFlowChart Bug**
   - Changed sorting from sequence-only to period-first, then sequence
   - Fixed duplicate/interleaved plays appearing in chart

3. **Changed Hot Streak Display**
   - Changed dash to colon: "Hannah Stuelke: 4 consecutive makes"
   - Changed orange to red-orange gradient for "fire" effect

4. **Built Season Stats Page**
   - New Lambda: `get_season_stats` with splits, trends, pattern insights
   - New frontend: `StatsPage.tsx` with hero stats, charts, game grid
   - Works for both 2024-25 and 2025-26 seasons

---

## 🎯 Next Feature: AI + Reddit + YouTube Integration

### Overview
Add to each game page:
1. **AI Game Summary** - Claude analyzes play-by-play and generates narrative
2. **Reddit Fan Sentiment** - Fetch game thread, Claude summarizes fan reaction
3. **YouTube Embed** - Post-game video player

### Implementation Plan

#### Step 1: Add Media URLs to Database

**Option A: Direct DynamoDB Console (Simplest)**
1. Go to AWS Console → DynamoDB → courtvision-games
2. Find item: pk=`GAME#401818635`, sk=`METADATA`
3. Add attributes:
   - `reddit_thread_url` (String): `https://www.reddit.com/r/NCAAW/comments/1pltt4k/...`
   - `youtube_postgame_url` (String): `https://www.youtube.com/watch?v=1TxfYlAL3Z0`

**Option B: Script (Better for multiple games)**
Create `scripts/add_game_media.py`:
```python
import boto3
import argparse

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

def add_media(game_id: str, reddit_url: str = None, youtube_url: str = None):
    update_expr = []
    expr_values = {}
    
    if reddit_url:
        update_expr.append('reddit_thread_url = :reddit')
        expr_values[':reddit'] = reddit_url
    if youtube_url:
        update_expr.append('youtube_postgame_url = :youtube')
        expr_values[':youtube'] = youtube_url
    
    if not update_expr:
        print("No URLs provided")
        return
    
    table.update_item(
        Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'},
        UpdateExpression='SET ' + ', '.join(update_expr),
        ExpressionAttributeValues=expr_values
    )
    print(f"✅ Updated GAME#{game_id}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', required=True, help='Game ID (e.g., 401818635)')
    parser.add_argument('--reddit', help='Reddit thread URL')
    parser.add_argument('--youtube', help='YouTube post-game URL')
    args = parser.parse_args()
    
    add_media(args.game, args.reddit, args.youtube)
```

Usage:
```bash
python3 scripts/add_game_media.py --game 401818635 \
  --reddit "https://www.reddit.com/r/NCAAW/comments/1pltt4k/game_thread_lindenwood_at_9_iowa_300_pm_et_on_b1g/" \
  --youtube "https://www.youtube.com/watch?v=1TxfYlAL3Z0"
```

#### Step 2: Update get_game_detail Lambda
Return `reddit_thread_url` and `youtube_postgame_url` in response if they exist.

#### Step 3: Create Reddit Sentiment Lambda
New Lambda that:
1. Takes Reddit URL as input
2. Fetches `{url}.json` to get comments
3. Extracts top 30-50 comments
4. Sends to Bedrock Claude for sentiment analysis
5. Returns: sentiment_score, themes[], sample_quotes[]

#### Step 4: Create AI Game Summary Lambda
New Lambda that:
1. Fetches game metadata, patterns, box score
2. Sends to Bedrock Claude with prompt
3. Returns narrative summary (150-200 words)

#### Step 5: Frontend Components
- `YouTubeEmbed.tsx` - Simple iframe wrapper
- `RedditSentiment.tsx` - Sentiment card with themes
- `AISummary.tsx` - Narrative summary card
- Add to `GamePage.tsx` Overview tab

---

## 📝 Practical Workflow for Adding Media Links

**When a game finishes:**
1. Find Reddit game thread at r/NCAAW
2. Find YouTube post-game video (Iowa athletics channel)
3. Run: `python3 scripts/add_game_media.py --game {ID} --reddit {URL} --youtube {URL}`
4. Refresh game page to see new content

**Current games without media (to backfill):**
- 401818635 (Lindenwood) - Reddit + YouTube available
- 401818634 (Iowa State) - Probably has both
- Other games - Check r/NCAAW and YouTube

---

## 🔧 Commands Reference

```bash
# Deploy backend
cd backend && sam build --use-container && sam deploy

# Run frontend
cd frontend && npm run dev

# Re-analyze patterns
cd scripts
python3 analyze_patterns_v2.py --season 2026 --clear
python3 analyze_patterns_v2.py --season 2025 --clear

# Re-fetch game details (if needed)
python3 fetch_game_details.py --season 2026 --force

# Test API endpoints
curl "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/stats?season=2026" | jq
curl "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/games/401818635" | jq
```

---

## ⚠️ Known Issues / Gotchas

1. **ESPN sequence numbers vary** - Some games use 4-digit, some use 9-digit sequences
2. **Sort by period first** - ScoreFlowChart must sort by period, THEN sequence
3. **Player names in text** - Some plays have empty `player_name`, extract from `text` field
4. **Reddit API rate limits** - Add caching, don't fetch on every page load

---

## 🎯 Session Priorities

**Recommended order for next session:**

1. **Create `add_game_media.py` script** (10 min)
2. **Add sample URLs to Lindenwood game** (5 min)
3. **Update get_game_detail Lambda** to return new fields (15 min)
4. **Create YouTube embed component** (15 min) - Quick win, visible result
5. **Setup AWS Bedrock** (20 min) - One-time setup
6. **Create AI Summary Lambda** (30 min)
7. **Create Reddit Sentiment Lambda** (30 min)
8. **Frontend integration** (30 min)

**Total: ~2.5 hours if no blockers**

---

## 📌 Key Files to Reference

When starting, ask user to upload:
- `frontend/src/pages/GamePage.tsx` - Where new components go
- `backend/template.yaml` - For adding new Lambdas
- `backend/lambdas/get_game_detail/lambda_function.py` - To add new fields

---

## 💡 User Preferences (From This Session)

- Prefers **Option B** (more work but cleaner) over quick fixes
- Likes **discussion before implementation**
- Wants **small, verified steps** - not bulk changes
- Uses **manual data entry** for Reddit/YouTube links (acceptable for portfolio)
- Appreciates **verification commands** after changes

---

**End of Handoff Document**