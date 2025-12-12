# CourtVision AI - Backend

AWS SAM-based serverless API for Iowa Hawkeyes basketball analytics.

## Structure

```
backend/
├── template.yaml          # SAM configuration
├── lambdas/
│   ├── get_games/         # GET /games
│   ├── get_game_detail/   # GET /games/{gameId}
│   └── get_plays/         # GET /games/{gameId}/plays
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /games | List all games for a season |
| GET | /games/{gameId} | Game details and boxscore |
| GET | /games/{gameId}/plays | Play-by-play data |

### Query Parameters

**GET /games**
- `season` - Season year (default: 2025)

**GET /games/{gameId}/plays**
- `period` - Filter by period (1-4)
- `scoring_only` - If "true", only scoring plays
- `limit` - Max plays to return

## Deployment

### First-time setup

```bash
cd backend

# Build the application
sam build

# Deploy (guided mode for first time)
sam deploy --guided
```

During guided deploy, use these settings:
- Stack Name: `courtvision-api`
- Region: `us-east-1`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to samconfig.toml: `Y`

### Subsequent deployments

```bash
sam build && sam deploy
```

## Local Testing

```bash
# Start local API
sam local start-api

# Test endpoints
curl http://localhost:3000/games
curl http://localhost:3000/games/401713556
curl http://localhost:3000/games/401713556/plays
```

## After Deployment

The output will show your API URL:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

Test with:
```bash
curl https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/games
```