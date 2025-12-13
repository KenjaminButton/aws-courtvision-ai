# CourtVision AI - Progress Tracker

## Current Status
**Phase 1, Day 5** - Ready to begin Lambda API development

## Completed (Days 1-4)
- [x] Project structure created
- [x] AWS resources verified (us-east-1)
- [x] ESPN API tested and working (Team ID: 2294)
- [x] Data collection scripts built (scripts/ folder)
- [x] 2024-25 season data collected (34 games, 12,504 plays)
- [x] Local data organized: `scripts/data/2025/`
- [x] DynamoDB table created: `courtvision-games`
- [x] All data uploaded to DynamoDB

## Next Step
Build Lambda functions to query DynamoDB:
- GET /games - List all games
- GET /games/{id} - Game details + plays
- GET /games/{id}/plays - Play-by-play data

## Key Files
- `scripts/` - Data collection (runs locally in venv)
- `backend/` - Lambda functions (to be built)
- `frontend/` - React app (to be built)

## DynamoDB Schema
- Table: `courtvision-games` (us-east-1)
- PK: `GAME#{id}` or `SCHEDULE#{year}`
- SK: `METADATA`, `PLAY#0001`, etc.


## Phase 2:

```
backend/
├── lambdas/
│   ├── get_games/
│   │   └── lambda_function.py
│   ├── get_game_detail/
│   │   └── lambda_function.py
│   └── get_plays/
│   │   └── lambda_function.py
└── README.md
```

## Completed
- [x] Project structure created
- [x] ESPN API scripts (schedule + play-by-play)
- [x] 2024-25 season data: 34 games, 12,504 plays
- [x] DynamoDB table: `courtvision-games`
- [x] Lambda functions deployed via SAM
- [x] API Gateway live with 3 endpoints

## API Endpoints
Base URL in `.env.local`

| Endpoint | Description |
|----------|-------------|
| GET /games | List all games |
| GET /games/{id} | Game details + boxscore |
| GET /games/{id}/plays | Play-by-play data |

## Next Step
Phase 3: React frontend to display games and analytics

## Key Files
- `scripts/` - Data collection (local)
- `backend/` - SAM + Lambda (deployed)
- `frontend/` - React app (to build)
```

**Git commit:**
```
feat: complete Phase 2 - Lambda API deployed

- SAM template with 3 Lambda functions
- API Gateway endpoints for games/plays
- Security: samconfig.toml and .env.local gitignored

