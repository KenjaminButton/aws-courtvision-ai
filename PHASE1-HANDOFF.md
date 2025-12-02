# Phase 1 → Phase 2 Handoff

## What's Built (Phase 1 Complete)

### AWS Resources Deployed
- **Lambda:** `courtvision-ingest` (Python 3.12, 256MB, 30s timeout)
- **DynamoDB:** `courtvision-games` (on-demand, streams enabled)
- **S3:** `courtvision-recordings-811230534980`
- **EventBridge:** 5-minute schedule (currently disabled)
- **CloudWatch:** Logs at `/aws/lambda/courtvision-ingest`

### Data Flow (Current)
```
EventBridge → Lambda (courtvision-ingest) → DynamoDB + S3
                                           ↓
                                      Play-by-play
```

### DynamoDB Schema (Single-Table Design)

**Access Patterns:**
| PK | SK | Data |
|----|----|----|
| `GAME#2025-12-02#TEAM1-TEAM2` | `METADATA` | Game info |
| `GAME#2025-12-02#TEAM1-TEAM2` | `SCORE#CURRENT` | Current score |
| `GAME#2025-12-02#TEAM1-TEAM2` | `PLAY#<timestamp>#<playId>` | Individual play |

**Current Stats:**
- 11 games tracked
- 357 total items
- 335 plays stored (from 1 completed game)

### Environment Variables (Lambda)
```
DATA_SOURCE=live
DYNAMODB_TABLE=courtvision-games
S3_BUCKET=courtvision-recordings-811230534980
SCHEDULE_ENABLED=false
```

### Key Implementation Details

**ESPN API:**
- Base URL: `https://site.api.espn.com/.../womens-college-basketball`
- Endpoints: `/scoreboard`, `/summary?event={gameId}`
- Polling: Every 5 minutes (conservative for unofficial API)

**Retry Logic:**
- 3 attempts with exponential backoff (1s, 2s, 4s)
- Handles: Timeout, HTTPError, RequestException

**S3 Structure:**
```
courtvision-recordings-{accountId}/
├── scoreboard/raw_espn/{timestamp}.json
└── {date}-{matchup}/parsed_game/{timestamp}.json
```

## What Phase 2 Needs to Build

### New AWS Resources
1. **Kinesis Data Stream** - Buffer play-by-play events
2. **Processing Lambda** - Parse plays, update game state
3. **API Gateway WebSocket** - Real-time client connections
4. **WebSocket Lambda** - Push updates to clients

### New Data Flow (Target)
```
EventBridge → Ingestion Lambda → Kinesis Stream
                                      ↓
                                Processing Lambda → DynamoDB
                                                        ↓
                                                  DynamoDB Streams
                                                        ↓
                                                  WebSocket Lambda
                                                        ↓
                                                  API Gateway WS
                                                        ↓
                                                  React Frontend
```

### New DynamoDB Items (Phase 2 Will Add)
- `WS#CONNECTION` + `{connectionId}` - WebSocket connections
- More to come in later phases (AI outputs, patterns, etc.)

## Quick Start Commands (Phase 2)

### Deploy New Stack
```bash
cd ~/Desktop/AWS/AWS\ Projects/03-AWS-Courtvision-AI
cdk deploy ProcessingStack --profile courtvision-dev
```

### Update Existing Lambda
```bash
cd lambda/ingestion
rm -rf package lambda-package.zip && mkdir package
pip install --platform manylinux2014_x86_64 --target ./package requests
cp handler.py ./package/
cd package && zip -r ../lambda-package.zip . && cd ..
aws lambda update-function-code --function-name courtvision-ingest --zip-file fileb://lambda-package.zip --region us-east-1 --profile courtvision-dev
```

### Check DynamoDB
```bash
aws dynamodb scan --table-name courtvision-games --select COUNT --region us-east-1 --profile courtvision-dev
```

### Check S3
```bash
aws s3 ls s3://courtvision-recordings-811230534980/ --recursive --summarize --region us-east-1 --profile courtvision-dev
```

## Important Notes for Phase 2

1. **Don't modify ingestion Lambda** - It's working. Build new Lambdas for processing.
2. **DynamoDB Streams already enabled** - Ready to trigger Processing Lambda
3. **Use us-east-1** - All resources in this region
4. **AWS Profile:** `courtvision-dev`
5. **Account ID:** 811230534980

## Phase 2 Day 11 Starting Point

Begin with creating Kinesis Data Stream:
```typescript
const playStream = new kinesis.Stream(this, 'PlayStream', {
  streamName: 'courtvision-plays',
  shardCount: 1,
});
```

Then modify ingestion Lambda to send plays to Kinesis (instead of direct DynamoDB).

## Files to Reference

- `Blueprint.md` - Full architecture
- `implementation-timeline.md` - Phase 2 days 11-20
- `PROGRESS.md` - Days 1-10 completed
- `lambda/ingestion/handler.py` - Current ingestion code
- `lib/stacks/ingestion-stack.ts` - Current CDK infrastructure

## Contact Context

- Region: Santa Clara, California, US
- Project goal: Portfolio project for job interviews
- Demo strategy: Use replay mode (not live polling)
- Token budget: Start new chat with ~190k tokens