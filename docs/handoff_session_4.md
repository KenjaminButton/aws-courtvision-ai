# CourtVision AI - Session 3 Handoff Document
**Date:** December 16, 2024
**Project:** Iowa Hawkeyes Women's Basketball Analytics Platform

---

## 🎯 CRITICAL INSTRUCTIONS FOR NEXT SESSION

**READ THIS FIRST, CLAUDE:**
1. **Take SMALL steps** - One file, one feature at a time
2. **Verify before changing** - Always `cat` or `grep` the actual file before editing
3. **Don't guess field names** - Query DynamoDB to confirm schema
4. **Test each change** - Don't stack multiple untested changes
5. **Ask before major changes** - User prefers discussion over implementation

---

## 📋 SESSION 3 PRIORITIES

### Priority 1: Player Splits Tab (IN PROGRESS)
Files created but need verification and deployment:
- `lambda_function_with_splits.py` → needs to replace `backend/lambdas/get_players/lambda_function.py`
- `SplitsTab_component.tsx` → needs to replace SplitsTab function in `PlayerDetailPage.tsx`

**Before deploying, verify fields exist:**
```bash
aws dynamodb get-item \
  --table-name courtvision-games \
  --key '{"pk": {"S": "GAME#401818635"}, "sk": {"S": "METADATA"}}' \
  --region us-east-1 \
  | jq '{iowa_home_away: .Item.iowa.M.home_away, conference: .Item.conference_competition}'
```

If fields missing, check `fetch_game_details.py` to ensure `home_away` and `conference_competition` are captured.

---

### Priority 2: Update New Games (2 games since last session)
Two games have been played. Need to:
1. Fetch game details from ESPN
2. Run pattern detection
3. Add Reddit thread URLs
4. Add YouTube post-game video URLs
5. Generate AI summaries (NEW FEATURE)

**Commands to update games:**
```bash
cd scripts

# 1. Fetch new games to schedule
python3 fetch_schedule.py --season 2026

# 2. Fetch game details for new games
python3 fetch_game_details.py --season 2026

# 3. Run pattern detection
python3 analyze_patterns_v2.py --season 2026

# 4. Add media links (user will provide URLs)
python3 add_game_media.py --game {GAME_ID} \
  --reddit "{REDDIT_URL}" \
  --youtube "{YOUTUBE_URL}"
```

---

### Priority 3: AI Game Summary Feature (NEW)
Generate narrative summaries using AWS Bedrock (Claude Sonnet).

**Architecture:**
```
User visits game page
    ↓
Frontend checks if ai_summary exists in METADATA
    ↓
If not: Call new Lambda → Bedrock → Generate summary → Store in DynamoDB
    ↓
Display summary card on game page
```

**Implementation Steps:**
1. Enable Bedrock in AWS Console (Claude Sonnet model)
2. Create `generate_game_summary` Lambda
3. Update `get_game_detail` Lambda to return `ai_summary`
4. Create `AISummary.tsx` component
5. Add to GamePage.tsx

**Lambda Pseudo-code:**
```python
def generate_summary(game_id):
    # Fetch game metadata, patterns, box score
    # Build prompt with game context
    # Call Bedrock Claude Sonnet
    # Store summary in METADATA
    # Return summary
```

---

### Priority 4: Reddit Sentiment Feature (NEW)
Analyze fan reactions from game thread.

**Reddit API (no auth needed):**
```
https://www.reddit.com/r/NCAAW/comments/{thread_id}/.json
```

**Implementation Steps:**
1. Create `analyze_reddit_sentiment` Lambda
2. Fetch Reddit JSON, extract top 30-50 comments
3. Send to Bedrock for sentiment analysis
4. Return: sentiment_score, themes[], sample_quotes[]
5. Create `RedditSentiment.tsx` component

---

### Priority 5: Light/Dark Mode Toggle
Add theme switching to the app.

**Implementation Approach:**
1. Create `ThemeContext.tsx` with `theme` state ('dark' | 'light')
2. Store preference in localStorage
3. Add CSS variables for colors in both themes
4. Add toggle button in Header
5. Update Tailwind config for theme support

**Files to modify:**
- `frontend/src/contexts/ThemeContext.tsx` (new)
- `frontend/src/components/Header.tsx` (add toggle)
- `frontend/src/index.css` (CSS variables)
- `tailwind.config.js` (dark mode config)

**Tailwind dark mode setup:**
```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // Enable class-based dark mode
  // ...
}
```

---

### Priority 6: CI/CD Pipeline
Automate deployments for the rest of the season.

**Recommended: GitHub Actions**

**Workflow triggers:**
- Push to `main` → Deploy to production
- Push to `develop` → Deploy to staging (optional)

**`.github/workflows/deploy.yml`:**
```yaml
name: Deploy CourtVision AI

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/setup-sam@v2
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: cd backend && sam build && sam deploy --no-confirm-changeset

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci && npm run build
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: aws s3 sync frontend/dist s3://${{ secrets.S3_BUCKET }} --delete
      - run: aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} --paths "/*"
```

**GitHub Secrets needed:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`
- `CF_DISTRIBUTION_ID`

---

### Priority 7: Production Deployment (AWS)

**Architecture:**
```
User → Route 53 (DNS) → CloudFront (CDN) → S3 (Static Files)
                              ↓
                        API Gateway → Lambda → DynamoDB
```

**Step-by-step Setup:**

#### 1. Create S3 Bucket for Frontend
```bash
aws s3 mb s3://courtvision-ai-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://courtvision-ai-frontend \
  --index-document index.html \
  --error-document index.html
```

#### 2. Create CloudFront Distribution
- Origin: S3 bucket
- Default root object: `index.html`
- Error pages: 403/404 → `/index.html` (for SPA routing)
- HTTPS: Redirect HTTP to HTTPS
- Price class: Use only North America and Europe (cheaper)

#### 3. Route 53 (Optional - requires domain)
- Register domain or transfer existing
- Create hosted zone
- Add A record pointing to CloudFront

**If no custom domain:** Just use CloudFront URL (e.g., `d1234abcd.cloudfront.net`)

#### 4. Build and Deploy Frontend
```bash
cd frontend

# Update .env.production with API URL
echo "VITE_API_URL=https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod" > .env.production

# Build
npm run build

# Deploy to S3
aws s3 sync dist/ s3://courtvision-ai-frontend --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

---

## 📁 Current Project Structure

```
~/Desktop/AWS/AWS Projects/03-AWS-Courtvision-AI/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── BoxScore.tsx
│       │   ├── GameCard.tsx
│       │   ├── Header.tsx
│       │   ├── LoadingStates.tsx
│       │   ├── PatternBadge.tsx
│       │   ├── PlayByPlay.tsx
│       │   ├── ScoreBoard.tsx
│       │   └── ScoreFlowChart.tsx
│       ├── contexts/
│       │   └── SeasonContext.tsx
│       ├── hooks/
│       │   └── useApi.ts
│       ├── pages/
│       │   ├── GamePage.tsx
│       │   ├── HomePage.tsx
│       │   ├── PlayerDetailPage.tsx
│       │   ├── PlayersPage.tsx
│       │   └── StatsPage.tsx ← NEW
│       ├── services/
│       │   └── api.ts
│       └── types/
│           └── index.ts
│
├── backend/
│   ├── template.yaml
│   └── lambdas/
│       ├── get_games/
│       ├── get_game_detail/
│       ├── get_plays/
│       ├── get_players/
│       └── get_season_stats/ ← NEW
│
├── scripts/
│   ├── fetch_schedule.py
│   ├── fetch_game_details.py
│   ├── analyze_patterns_v2.py
│   └── add_game_media.py ← NEW
│
└── docs/
    ├── DECISION_LOG.md
    ├── IMPLEMENTATION_TIMELINE.md
    └── HANDOFF_SESSION_3.md ← THIS FILE
```

---

## 🗄️ DynamoDB Schema

**Table:** `courtvision-games` (us-east-1)
**Keys:** lowercase `pk`, `sk`

| Record Type | PK | SK | Key Fields |
|-------------|----|----|------------|
| Season Index | `SEASON#2026` | `GAME#2025-11-04#401818626` | game_id, iowa_score, opponent_score, iowa_won |
| Game Metadata | `GAME#401818635` | `METADATA` | iowa{}, opponent{}, boxscore{}, player_stats{}, reddit_thread_url*, youtube_postgame_url*, ai_summary* |
| Play | `GAME#401818635` | `PLAY#0001` | period, clock, text, player_name, scoring_play |
| Pattern | `GAME#401818635` | `PATTERN#scoring_run#001` | pattern_type, team, is_iowa, description |
| Player Bio | `PLAYER#4682968` | `BIO#2026` | height, hometown, class_year |

*Fields to be added

---

## 🌐 API Endpoints

**Base URL:** `https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod`

| Endpoint | Description |
|----------|-------------|
| GET /games?season=2026 | List all games |
| GET /games/{gameId} | Game detail + patterns |
| GET /games/{gameId}/plays | All plays |
| GET /players?season=2026 | Player stats + splits |
| GET /stats?season=2026 | Season stats |

---

## ✅ What Was Accomplished in Session 2

1. **Fixed Pattern Detection** - Player names now extracted from play text
2. **Fixed ScoreFlowChart** - Sort by period first, then sequence
3. **Built StatsPage** - Season stats with splits, trends, pattern insights
4. **Created add_game_media.py** - Script to add Reddit/YouTube URLs
5. **Started Player Splits** - Lambda and component created (needs deployment)

---

## 🔧 Quick Reference Commands

```bash
# Deploy backend
cd backend && sam build --use-container && sam deploy

# Run frontend locally
cd frontend && npm run dev

# Fetch new games
cd scripts && python3 fetch_schedule.py --season 2026

# Re-analyze patterns
python3 analyze_patterns_v2.py --season 2026 --clear

# Add media to game
python3 add_game_media.py --game 401818635 --reddit "URL" --youtube "URL"

# List games with media status
python3 add_game_media.py --list 2026

# Test API
curl "https://5fgtvgqe65.execute-api.us-east-1.amazonaws.com/prod/stats?season=2026" | jq
```

---

## 💡 User Preferences

- Prefers **discussion before implementation**
- Wants **small, verified steps**
- Uses **manual data entry** for Reddit/YouTube links
- Appreciates **verification commands** after changes
- Wants light mode as **optional toggle** (dark mode default)

---

## 📌 Files Created This Session (Need to be Applied)

1. **lambda_function_with_splits.py** → `backend/lambdas/get_players/lambda_function.py`
2. **SplitsTab_component.tsx** → Replace SplitsTab in `PlayerDetailPage.tsx`
3. **add_game_media.py** → `scripts/add_game_media.py`
4. **StatsPage.tsx** → `frontend/src/pages/StatsPage.tsx` (already applied)

---

## 🎯 Suggested Session Order

1. ✅ Verify and deploy Player Splits (finish in-progress work)
2. Update 2 new games (fetch, analyze, add media)
3. Build AI Summary feature (Bedrock)
4. Build Reddit Sentiment feature
5. Add Light/Dark mode toggle
6. Set up CI/CD (GitHub Actions)
7. Deploy to production (S3 + CloudFront)

---

**End of Handoff Document**