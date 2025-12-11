# CourtVision AI - Data Collection Scripts

Scripts to fetch Iowa Hawkeyes Women's Basketball data from ESPN API.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Collect all 2024-25 season data (schedule + play-by-play)
python collect_iowa_data.py --season 2025

# Or run individual scripts:
python fetch_iowa_schedule.py --season 2025
python fetch_playbyplay.py --from-schedule ./data/iowa_schedule_2025.json
```

## Scripts

### `collect_iowa_data.py`
All-in-one data collection. Fetches schedule and play-by-play for all completed games.

```bash
python collect_iowa_data.py --season 2025
python collect_iowa_data.py --season 2025 --skip-pbp  # Schedule only
```

### `fetch_iowa_schedule.py`
Fetches season schedule including regular season AND March Madness games.

```bash
python fetch_iowa_schedule.py --season 2025
# Output: ./data/iowa_schedule_2025.json
```

### `fetch_playbyplay.py`
Fetches detailed play-by-play data for games.

```bash
# Single game
python fetch_playbyplay.py --game-id 401746037

# All games from schedule file
python fetch_playbyplay.py --from-schedule ./data/iowa_schedule_2025.json
# Output: ./data/games/game_401746037.json (one per game)
```

## Output Format

### Schedule JSON
```json
{
  "fetched_at": "2025-12-11T18:30:00Z",
  "team_id": "2294",
  "season_year": 2025,
  "total_games": 34,
  "games": [
    {
      "game_id": "401713556",
      "date": "2024-11-07T00:30Z",
      "season_type": "Regular Season",
      "iowa": { "score": "91", "winner": true },
      "opponent": { "abbreviation": "NIU", "score": "73" }
    }
  ]
}
```

### Game JSON (Play-by-Play)
```json
{
  "game_id": "401713556",
  "play_count": 245,
  "iowa": { "score": "91", "home_away": "home" },
  "opponent": { "abbreviation": "NIU", "score": "73" },
  "boxscore": { ... },
  "player_stats": { ... },
  "plays": [
    {
      "play_id": "12345",
      "period": 1,
      "clock": "9:45",
      "type": "Three Point Jumper",
      "text": "Lucy Olsen made Three Point Jumper",
      "scoring_play": true,
      "score_value": 3
    }
  ]
}
```

## ESPN API Notes

- **Team ID**: 2294 (Iowa Hawkeyes)
- **Season Parameter**: Use ending year (2025 = 2024-25 season)
- **Season Types**: 
  - Type 2 = Regular Season
  - Type 3 = Postseason (NCAA Tournament)
- **Rate Limiting**: Scripts include 1 second delay between requests

## Next Steps

After collecting data:
1. Upload to DynamoDB using `upload_to_dynamodb.py` (coming soon)
2. Or manually import via AWS Console