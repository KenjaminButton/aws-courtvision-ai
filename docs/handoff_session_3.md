# CourtVision AI - Session 3 Handoff Document
**Date:** December 17, 2024
**Project:** Iowa Hawkeyes Women's Basketball Analytics Platform

---

## 🎯 CRITICAL INSTRUCTIONS FOR NEXT SESSION

**READ THIS FIRST, CLAUDE:**
1. **Take SMALL steps** - One file, one feature at a time
2. **Verify before changing** - Always check the actual file before editing
3. **Test each change** - Don't stack multiple untested changes
4. **Ask before major changes** - User prefers discussion over surprise rewrites

---

## ✅ What We Accomplished This Session

### Phase A: Media URLs + YouTube Embeds
1. ✅ Updated `add_game_media.py` with `--highlights` and `--postgame` flags
2. ✅ Added media URLs to Lindenwood game (401818635)
3. ✅ Updated `get_game_detail` Lambda to return media URLs
4. ✅ Created `YouTubeEmbed.tsx` component with `GameMedia` wrapper
5. ✅ Added `GameMedia` to `GamePage.tsx` Overview tab
6. ✅ Updated TypeScript types for media URLs

### Phase C: AI Game Summary
1. ✅ Tested Bedrock locally (confirmed working)
2. ✅ Extensively tested and refined AI prompt with Claude Sonnet
3. ✅ Created `ai_game_summary` Lambda with:
   - Full Iowa roster with class years and positions
   - Comprehensive rules to prevent hallucinations
   - Game context support for per-game storylines
4. ✅ Added `--context` flag to `add_game_media.py`
5. ✅ Deployed Lambda - API working at `/games/{gameId}/summary`
6. ✅ Caching implemented (summaries stored in DynamoDB)

---

## 🏗️ What Needs To Be Done Next

### Immediate (This Next Session)
1. **Create `AISummary.tsx`** - Frontend component to display AI summary
2. **Add to `GamePage.tsx`** - Integrate into Overview tab
3. **Update TypeScript types** - Add summary response type
4. **Test end-to-end** - Verify summary displays on game page

### After That
1. **Reddit Sentiment Lambda** - Fetch Reddit comments, analyze with Haiku
2. **Create `RedditSentiment.tsx`** - Display fan sentiment analysis
3. **Integrate both components** - Complete the Overview tab

---

## 📁 Project Structure (Relevant Files)

```
~/Desktop/AWS/AWS Projects/03-AWS-Courtvision-AI/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── YouTubeEmbed.tsx      # ✅ NEW - YouTube + GameMedia
│       │   └── [other components]
│       ├── pages/
│       │   └── GamePage.tsx          # Has GameMedia, needs AISummary
│       ├── types/
│       │   └── index.ts              # Needs summary types
│       └── hooks/
│           └── useApi.ts             # May need summary hook
│
├── backend/
│   ├── template.yaml                 # Has AI summary Lambda
│   └── lambdas/
│       ├── ai_game_summary/          # ✅ NEW
│       │   └── lambda_function.py
│       └── get_game_detail/
│           └── lambda_function.py    # Returns media URLs
│
└── scripts/
    └── add_game_media.py             # ✅ UPDATED - has --context flag
```

---

## 🌐 API Endpoints

**Base URL:** `https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod`

| Endpoint | Description | Response |
|----------|-------------|----------|
| GET /games?season=2026 | List all games | Games array |
| GET /games/{gameId} | Game detail + patterns + media URLs | GameDetail |
| GET /games/{gameId}/plays | Play-by-play | Plays array |
| GET /games/{gameId}/summary | **NEW** AI summary | `{ summary, generated_at, cached }` |
| GET /players?season=2026 | Player stats | Players array |
| GET /stats?season=2026 | Season stats | Stats object |

### AI Summary Response Format
```json
{
  "summary": "The #11 ranked Iowa Hawkeyes dominated...",
  "generated_at": "2025-12-18T06:08:37.372745Z",
  "cached": true
}
```

---

## 🔧 Key Technical Decisions

### AI Model Choice
- **Using:** Claude 3.5 Sonnet v1 (`anthropic.claude-3-5-sonnet-20240620-v1:0`)
- **Why:** Haiku hallucinated too much (fake quotes, wrong class years, wrong coach)
- **Cost:** ~$0.01-0.02 per summary generation
- **Caching:** Summaries stored in DynamoDB, only generated once per game

### Prompt Structure
The Lambda has hardcoded:
- IOWA HAWKEYES FACTS (coach, arena, conference)
- Full ROSTER (14 players with class years and positions)
- IMPORTANT RULES (prevent hallucinations)

User provides via `--context`:
- STARTERS THIS GAME (5 players)
- GAME NOTES (storylines, injuries, etc.)

### DynamoDB Schema for AI Summary
```
pk: GAME#401818635
sk: AI_SUMMARY
Fields: game_id, summary, generated_at, model
```

---

## 📝 Game Context Template

When adding context for a new game:

```bash
python3 add_game_media.py --game {GAME_ID} --context "Iowa (#{RANK}) {hosts/visits} {opponent rank/status} {opponent} in a {game type}.

STARTERS THIS GAME:
- {Player 1} ({Class}, {Position})
- {Player 2} ({Class}, {Position})
- {Player 3} ({Class}, {Position})
- {Player 4} ({Class}, {Position})
- {Player 5} ({Class}, {Position})

GAME NOTES:
{Storylines, injuries, what to watch for, upcoming schedule context, etc.}"
```

### Example (Lindenwood game):
```bash
python3 add_game_media.py --game 401818635 --context "Iowa (#11) hosts unranked Lindenwood in a non-conference tune-up game.

STARTERS THIS GAME:
- Hannah Stuelke (Senior, Forward)
- Ava Heiden (Sophomore, Center)
- Taylor McCabe (Senior, Guard)
- Kylie Feuerbach (Graduate Student, Guard)
- Chazadi \"Chit Chat\" Wright (Sophomore, Guard)

GAME NOTES:
This is Iowa's final home game before the holiday break, before traveling to Brooklyn to face #1 ranked UConn Huskies next Saturday. The Hawkeyes used this game to get bench players extended minutes. Chazadi Wright left early - saving her for UConn. Breakout game for Hannah Stuelke."
```

---

## 🏀 Iowa Hawkeyes Roster (2025-26)

For reference when writing game context:

| Player | Class | Position |
|--------|-------|----------|
| Hannah Stuelke | Senior | Forward |
| Taylor McCabe | Senior | Guard |
| Jada Gyamfi | Senior | Forward |
| Kylie Feuerbach | Graduate Student | Guard |
| Kennise Johnson | Junior | Guard |
| Ava Heiden | Sophomore | Center |
| Chazadi "Chit Chat" Wright | Sophomore | Guard |
| Emely Rodriguez | Sophomore | Guard |
| Teagan Mallegni | Sophomore | Guard |
| Taylor Stremlow | Sophomore | Guard |
| Callie Levin | Sophomore | Guard |
| Layla Hays | Freshman | Center |
| Addie Deal | Freshman | Guard |
| Journey Houston | Freshman | Forward |

---

## 🔧 Commands Reference

```bash
# Deploy backend
cd backend && sam build --use-container && sam deploy

# Run frontend
cd frontend && npm run dev

# Add game context
python3 scripts/add_game_media.py --game {ID} --context "..."

# View current context
python3 scripts/add_game_media.py --game {ID} --show-context

# List games with media/context status
python3 scripts/add_game_media.py --list 2026

# Test AI summary API
curl "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/games/401818635/summary" | jq

# Test game detail API (includes media URLs)
curl "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/games/401818635" | jq '{reddit_thread_url, youtube_highlights_url, youtube_postgame_url}'
```

---

## 📌 Files to Upload for Next Session

1. **GamePage.tsx** - Where AISummary component needs to be added
2. **types/index.ts** - Needs summary response type
3. **useApi.ts** - May need hook for fetching summary
4. **YouTubeEmbed.tsx** - For reference on component structure
5. **This handoff document**

---

## 🎯 Next Session Priorities

**Recommended order:**

1. **Create `AISummary.tsx`** (20 min)
   - Fetch from `/games/{gameId}/summary`
   - Display summary text
   - Show "Generated at" timestamp
   - Loading state

2. **Update TypeScript types** (5 min)
   - Add `AISummaryResponse` type

3. **Add to GamePage.tsx** (10 min)
   - Import AISummary
   - Add to Overview tab

4. **Test end-to-end** (10 min)
   - Visit Lindenwood game page
   - Verify summary displays

5. **Reddit Sentiment Lambda** (45 min)
   - Fetch Reddit thread JSON
   - Extract top 100 comments
   - Send to Haiku for sentiment analysis
   - Store in DynamoDB

6. **Create RedditSentiment.tsx** (30 min)
   - Display sentiment score
   - Show key themes
   - Link to full thread

---

## 💡 User Preferences

- Prefers **discussion before implementation**
- Wants **small, verified steps** - not bulk changes
- Uses **Claude Sonnet** for game summaries (not Haiku - too many hallucinations)
- Acceptable to use **Haiku for Reddit sentiment** (it's analyzing opinions, not facts)
- **Manual context entry** is fine for ~30 games/season

---

**End of Handoff Document**