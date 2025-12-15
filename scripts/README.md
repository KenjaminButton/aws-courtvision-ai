# CourtVision AI - Data Pipeline Scripts

These scripts fetch Iowa Hawkeyes game data from ESPN and store it in DynamoDB.

## Quick Start

```bash
# Install dependencies
pip install boto3 requests

# Make sure AWS credentials are configured
aws configure

# Run the full pipeline for current season (2025-26)
cd scripts
python3 run_pipeline.py
```

## Scripts Overview

| Script | Purpose | Run Frequency |
|--------|---------|---------------|
| `run_pipeline.py` | Main pipeline - runs all steps | Daily or before games |
| `fetch_season_games.py` | Sync game schedule from ESPN | Daily |
| `fetch_game_details.py` | Fetch plays & box scores | After games complete |
| `analyze_patterns.py` | Detect scoring runs, hot streaks | After fetching details |

---

## Individual Script Usage

### 1. fetch_season_games.py - Sync Schedule

Fetches the season schedule and **only adds/updates games that changed**.

```bash
# Current season (2025-26)
python3 fetch_season_games.py

# Specific season
python3 fetch_season_games.py --season 2025   # 2024-25 season
python3 fetch_season_games.py --season 2026   # 2025-26 season

# Force update all games (even unchanged)
python3 fetch_season_games.py --force
```

**What it does:**
- Fetches schedule from ESPN
- Compares with existing data in DynamoDB
- Adds new games (scheduled)
- Updates games that completed since last run
- Skips unchanged games

**Output:**
```
🏀 Syncing Iowa Hawkeyes 2025-26 Season (value: 2026)
============================================================
📡 Fetching from ESPN...
📊 Found 34 games on ESPN schedule
💾 Found 30 games already in database

📝 Processing games...
------------------------------------------------------------
   ⏭️  SKIPPED: 2025-11-07 vs NIU (no changes)
   ⏭️  SKIPPED: 2025-11-10 vs VT (no changes)
   🔄 UPDATED: 2025-12-14 vs TENN → W 72-68
   ✨ ADDED:   2025-12-21 vs MICH (scheduled)
```

---

### 2. fetch_game_details.py - Fetch Plays & Box Score

Fetches detailed data (play-by-play, box score) for completed games.

```bash
# Fetch all pending games
python3 fetch_game_details.py

# Fetch specific game
python3 fetch_game_details.py --game 401713556

# Limit number of games (useful for testing)
python3 fetch_game_details.py --limit 3

# Specific season
python3 fetch_game_details.py --season 2025
```

**What it does:**
- Finds completed games without detailed data
- Fetches play-by-play from ESPN
- Fetches box score / player stats
- Stores in DynamoDB
- Marks game as processed (won't re-fetch)

---

### 3. run_pipeline.py - Full Pipeline

Runs all steps in order.

```bash
# Full pipeline for current season
python3 run_pipeline.py

# Specific season
python3 run_pipeline.py --season 2025

# Skip steps
python3 run_pipeline.py --skip-details    # Only sync schedule
python3 run_pipeline.py --skip-patterns   # Skip pattern detection

# Force refresh everything
python3 run_pipeline.py --force
```

---

## DynamoDB Schema

The scripts use a single-table design:

### Season Games
```
PK: SEASON#2026
SK: GAME#2025-12-14#401713556
```

| Field | Type | Description |
|-------|------|-------------|
| game_id | String | ESPN game ID |
| date | String | ISO date |
| short_name | String | "NIU @ IOWA" |
| status_completed | Boolean | Is game finished? |
| iowa_score | String | "72" |
| iowa_won | Boolean | Did Iowa win? |
| opponent_abbrev | String | "NIU" |
| details_fetched | Boolean | Have we fetched plays? |

### Game Details
```
PK: GAME#401713556
SK: DETAILS
```

### Plays
```
PK: GAME#401713556
SK: PLAY#0001
SK: PLAY#0002
...
```

---

## Automation

### Option 1: Cron Job (Local/EC2)

```bash
# Edit crontab
crontab -e

# Run daily at 6am
0 6 * * * cd /path/to/scripts && python3 run_pipeline.py >> /var/log/courtvision.log 2>&1

# Run every 2 hours on game days (Saturday/Sunday)
0 */2 * * 0,6 cd /path/to/scripts && python3 run_pipeline.py >> /var/log/courtvision.log 2>&1
```

### Option 2: AWS Lambda + EventBridge

Create a Lambda function that runs the pipeline:

1. Package scripts as Lambda layer
2. Create Lambda function with 5-minute timeout
3. Create EventBridge rule to trigger daily

---

## Troubleshooting

### "No games found on ESPN"
- ESPN may not have released the schedule yet
- Check if the season parameter is correct
- Try visiting the ESPN URL directly

### "DynamoDB access denied"
- Check AWS credentials: `aws sts get-caller-identity`
- Ensure IAM role has DynamoDB access
- Check table name matches

### "Game details not showing in frontend"
- Verify `details_fetched` is True for the game
- Check API returns plays: `/games/{gameId}/plays`
- Look for errors in CloudWatch logs

---

## Season Values

| Season | Value | ESPN Season |
|--------|-------|-------------|
| 2024-25 | 2025 | 2024 |
| 2025-26 | 2026 | 2025 |
| 2026-27 | 2027 | 2026 |

The `--season` parameter uses the ending year.

---

## Rate Limiting

The scripts include delays to be respectful to ESPN:
- 1 second between game detail fetches
- No parallelization

If you get rate limited, wait a few minutes and try again.
