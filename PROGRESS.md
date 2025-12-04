# CourtVision AI - Development Progress Log

## Day 1 - Project Setup ✅ (Completed)

### What We Built
- CDK project initialized with TypeScript
- Empty ingestion stack deployed successfully
- AWS credentials configured with `courtvision-dev` IAM user

### File Structure
```
courtvision-ai/
├── bin/
│   └── courtvision-ai.ts          # Main CDK app entry point
├── lib/
│   └── stacks/
│       ├── ingestion-stack.ts     # Main stack (currently deployed)
│       ├── processing-stack.ts    # Empty (not created yet)
│       ├── ai-stack.ts           # Empty (not created yet)
│       └── frontend-stack.ts     # Empty (not created yet)
├── lambda/                        # Empty folders (not used yet)
│   ├── ingestion/
│   ├── processing/
│   └── ai/
├── frontend/                      # Empty (not used yet)
├── tests/                         # Empty (not used yet)
└── Blueprint.md                   # Project spec
```

### AWS Resources Deployed
- Stack: `CourtVisionIngestionStack`
- Region: `us-east-1` (or your default)
- Account: `811230534980`
- IAM User: `courtvision-dev`

### Key Configuration
- CDK bootstrapped: ✅
- AWS Profile: `courtvision-dev`
- Node version: [your version]
- CDK version: [run `cdk --version`]

### Git Status
- Committed: Initial CDK setup

---

## Day 2 - DynamoDB Table ✅ (Completed)

### What We Built
- DynamoDB table: `courtvision-games`
- Partition key: `PK` (String)
- Sort key: `SK` (String)
- Billing: On-demand
- Streams: Enabled (NEW_AND_OLD_IMAGES)
- Removal policy: RETAIN

### File Changes
- Updated: `lib/stacks/ingestion-stack.ts` (added DynamoDB table)

### AWS Resources Deployed
- DynamoDB Table: `courtvision-games`
- Table ARN: [from cdk output]

### Next Steps (Day 2 continued)
- Add GSI (Global Secondary Index)
- Test manual item creation

### AWS Resources Deployed (Updated)
- DynamoDB Table: `courtvision-games`
  - Partition key: PK, Sort key: SK
  - GSI1: GSI1PK (partition), GSI1SK (sort) ✅
  - Streams: Enabled
  - Billing: On-demand

### Day 2 Complete ✅
- DynamoDB table created and verified
- GSI added for date-based queries
- Test item creation confirmed

---

## Day 3 - S3 Buckets ✅ (Completed - After troubleshooting)

### What We Built
- S3 bucket for game recordings: `courtvision-recordings-811230534980`
  - Versioning: Enabled ✅
  - Lifecycle: Move to IA after 30 days
  - Region: us-east-1
- S3 bucket for frontend: `courtvision-frontend-811230534980`
  - Static website hosting: Enabled ✅
  - Region: us-east-1

### File Changes
- Updated: `lib/stacks/ingestion-stack.ts` (added S3 buckets)

### AWS Resources Deployed (All in us-east-1)
- DynamoDB Table: `courtvision-games` ✅
- S3 Bucket: `courtvision-recordings-811230534980` ✅
- S3 Bucket: `courtvision-frontend-811230534980` ✅

### Lessons Learned
- Environment variables (`AWS_REGION`) override AWS CLI profile settings
- S3 bucket names are globally unique - deletion has eventual consistency (5-10 min wait)
- DynamoDB `RETAIN` policy can create orphaned resources during failed deployments
- Always clean orphaned resources before redeploying

### Day 3 Complete ✅
**All infrastructure foundation in place!**

---

## Day 4 - Ingestion Lambda (ESPN Fetcher) ✅ (Completed)

### What We Built
- Lambda function that fetches ESPN scoreboard data
- Parser that converts ESPN format to our internal format
- Successfully tested with 7 completed games

### Files Created
- `lambda/ingestion/handler.py` - Main Lambda handler
- `lambda/ingestion/requirements.txt` - Python dependencies
- `lambda/ingestion/.venv/` - Virtual environment (gitignored)

### Functions Implemented
- `fetch_espn_scoreboard()` - Fetches from ESPN API ✅
- `parse_game_data()` - Parses ESPN game data ✅
- `handler()` - Main Lambda entry point ✅

### Test Results
- ESPN API connection: ✅ Working
- Data parsing: ✅ 7/7 games parsed successfully
- Status detection: ✅ Correctly identifies game state

### Day 4 Complete ✅
**Checkpoint:** Lambda runs locally, parses ESPN JSON correctly

---

## Day 5 - Ingestion Lambda (Deploy to AWS) ✅ (Completed)

### What We Built
- Lambda function successfully deployed to AWS via CDK
- DynamoDB write logic working: stores game metadata and current scores
- Manual Lambda invocation tested and verified
- 4 games ingested from ESPN API and stored in DynamoDB (8 items total)

### Files Created/Modified
- `lambda/ingestion/handler.py` - Added DynamoDB storage functions
- `lambda/ingestion/lambda-package.zip` - Deployment package with dependencies
- `lambda/ingestion/requirements.txt` - Python dependencies (requests, boto3)
- `lib/stacks/ingestion-stack.ts` - Added Lambda function definition with IAM permissions
- `bin/courtvision-ai.ts` - Main CDK app (stack name: CourtVisionIngestionStack)

### AWS Resources Deployed
- **Lambda Function:** `courtvision-ingest`
  - Runtime: Python 3.12
  - Memory: 256MB
  - Timeout: 30 seconds
  - Environment variables: DATA_SOURCE, DYNAMODB_TABLE, S3_BUCKET
- **IAM Role:** Automatic permissions for DynamoDB read/write and S3 read/write
- **CloudWatch Log Group:** `/aws/lambda/courtvision-ingest`

### Test Results
- ✅ Lambda invoked successfully via AWS CLI
- ✅ 4 games parsed from ESPN API
- ✅ 8 DynamoDB items created (METADATA + SCORE#CURRENT for each game)
- ✅ Data structure matches blueprint schema

### Problems Encountered & Solutions

#### Problem 1: Environment Variable Override
**Symptom:** CDK kept deploying to us-west-2 despite CLI configured for us-east-1  
**Root Cause:** `AWS_REGION=us-west-2` environment variable was set in terminal (likely from previous project)  
**Solution:** `unset AWS_REGION` to remove the override  
**Prevention:** Always check `echo $AWS_REGION` before deploying. Environment variables override AWS CLI config.

#### Problem 2: Early Validation Errors
**Symptom:** `AWS::EarlyValidation::ResourceExistenceCheck` failures  
**Root Cause:** Stack in `REVIEW_IN_PROGRESS` state with orphaned resources (DynamoDB table, S3 buckets) existing without CloudFormation management  
**Solution:** 
1. Delete stuck stack: `aws cloudformation delete-stack`
2. Delete orphaned resources manually
3. Wait 60 seconds for AWS propagation
4. Deploy fresh with `cdk deploy`

**Prevention:** 
- Never manually delete AWS resources - use `cdk destroy` instead
- If stack gets stuck, always delete the stack BEFORE deleting resources
- Check stack status: `aws cloudformation list-stacks --query "StackSummaries[?contains(StackName, 'YourStack') && StackStatus!='DELETE_COMPLETE']"`

#### Problem 3: Docker Bundling Issues
**Symptom:** Docker malware warnings, connection failures  
**Root Cause:** macOS Gatekeeper blocking Docker components  
**Solution:** Manual bundling with `pip install --platform manylinux2014_x86_64` and zip deployment package  
**Outcome:** Works perfectly for pure Python packages like `requests` and `boto3`

### Key Lessons Learned
1. **Environment variables take precedence** over AWS CLI configuration - always verify with `echo $AWS_REGION`
2. **Stack state matters** - A stack in `REVIEW_IN_PROGRESS` or `ROLLBACK_COMPLETE` blocks new deployments
3. **Order matters** when cleaning up - Delete stack first, then resources, then wait for propagation
4. **Proper workflow** - Use `cdk destroy` instead of manual resource deletion to avoid orphaned resources

### Prevention Checklist for Future CDK Deploys
```bash
# Before any CDK deploy, run these checks:
echo $AWS_REGION          # Should be empty or correct region
aws configure get region  # Verify CLI region
aws cloudformation list-stacks --region us-east-1 \
  --query "StackSummaries[?StackStatus!='DELETE_COMPLETE']"  # No stuck stacks
```

### Day 5 Complete ✅
**Checkpoint:** Manual Lambda invoke writes game data to DynamoDB

---

## Day 6 - Ingestion Lambda (S3 Recording) ✅ (Completed)

### What We Built
- Added S3 recording logic to Lambda
- Records raw ESPN responses and parsed game data for replay capability
- Successfully tested locally and in AWS

### Files Modified
- `lambda/ingestion/handler.py` - Added `record_to_s3()` function

### Functions Added
- `record_to_s3(game_id, data_type, data, timestamp)` - Saves JSON to S3
  - Creates folder structure: `{date}-{matchup}/{data_type}/{timestamp}.json`
  - Records scoreboard to: `scoreboard/raw_espn/{timestamp}.json`

### Key Code Changes in handler.py
1. **Added import:** `from datetime import datetime, timezone` (not just `datetime`)
2. **Removed line 14:** `table = dynamodb.Table(DYNAMODB_TABLE)` (causes errors during local testing)
3. **Fixed functions:** `store_game_metadata(game)` and `store_current_score(game)` now initialize table inside function
4. **Added PK field:** `parse_game_data()` now includes `'PK': f"GAME#{date_str}#{matchup}"` in parsed_game

### Test Results
- ✅ Local test: 3 files created in S3 (1 scoreboard + 2 games)
- ✅ AWS Lambda: 3 more files created (total 6 files)
- ✅ CloudWatch logs show all "✅ Recorded to S3" messages
- ✅ Package size: 1.1MB (correctly sized)

### Problems & Solutions

**Problem 1:** `ValueError: Required parameter name not set` on import  
**Solution:** Removed global `table = dynamodb.Table(DYNAMODB_TABLE)` initialization

**Problem 2:** Lambda package was 15MB instead of 1MB  
**Solution:** Clean package directory before zipping:
```bash
rm -rf package && mkdir package
pip install --platform manylinux2014_x86_64 --target ./package requests
cp handler.py ./package/
cd package && zip -r ../lambda-package.zip . && cd ..
```

**Problem 3:** Region defaulted to us-west-2 again  
**Solution:** Always add `--region us-east-1` to AWS CLI commands

### Day 6 Complete ✅
**Checkpoint:** Each Lambda run creates files in S3

---

## Day 7 - EventBridge Schedule ✅ (Completed)

### What We Built
- EventBridge rule that triggers Lambda every 5 minutes
- Manual enable/disable control (starts disabled)
- Tested automatic polling with 2 successful executions

### Files Modified
- `lib/stacks/ingestion-stack.ts` - Added EventBridge rule and imports

### Code Added
```typescript
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';

// EventBridge rule
const ingestionSchedule = new events.Rule(this, 'IngestionSchedule', {
  schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
  description: 'Trigger ingestion Lambda every minute during games',
  enabled: false, // Start disabled
});
ingestionSchedule.addTarget(new targets.LambdaFunction(ingestionLambda));
```

### AWS Resources Deployed
- **EventBridge Rule:** `CourtVisionIngestionStack-IngestionSchedule30858612-5Stq77YxdH7A`
  - Schedule: `rate(5 minutes)`
  - State: DISABLED (manual control)
  - Target: courtvision-ingest Lambda

### Manual Control Commands
**Enable (start automatic polling):**
```bash
aws events enable-rule \
  --name CourtVisionIngestionStack-IngestionSchedule30858612-5Stq77YxdH7A \
  --region us-east-1 \
  --profile courtvision-dev
```

**Disable (stop automatic polling):**
```bash
aws events disable-rule \
  --name CourtVisionIngestionStack-IngestionSchedule30858612-5Stq77YxdH7A \
  --region us-east-1 \
  --profile courtvision-dev
```

**Check status:**
```bash
aws events describe-rule \
  --name CourtVisionIngestionStack-IngestionSchedule30858612-5Stq77YxdH7A \
  --region us-east-1 \
  --profile courtvision-dev \
  --query 'State' \
  --output text
```

### Test Results
- ✅ First execution: 21:38:32
- ✅ Second execution: 21:43:31 (exactly 5 minutes later)
- ✅ DynamoDB items: 22 (accumulated data)
- ✅ S3 recordings: Multiple files created automatically

### Key Decision: 5 Minutes + Replay Mode Strategy

**Why 5 minutes (not 1-2 minutes):**
- ESPN API is **unofficial/undocumented** - no published rate limits
- 5 minutes = 12 API calls/hour (very conservative, safe from blocking)
- 2 minutes = 30 calls/hour (moderate risk)
- 1 minute = 60 calls/hour (high risk for unofficial API)

**Production Strategy:**
- **Development:** Manually enable for 1-2 hour testing sessions, record interesting games to S3
- **Demos/Interviews:** Use replay mode exclusively (play recorded games at 5x-10x speed)
- **If deployed to production:** Use time-based cron (6pm-11pm EST only) at 2-minute intervals

**Benefits of this approach:**
- Minimal ESPN API usage (avoid getting blocked)
- Better demos (control which games to show, faster than real-time)
- Interview talking point: "Used 5 minutes for unofficial API; with paid API like Sportradar, would use 30-60 seconds"

### Day 7 Complete ✅
**Checkpoint:** Data automatically appears in DynamoDB every 5 minutes when schedule is enabled

---

## Day 8 - Game Summary Endpoint ✅ (Completed)

### What We Built
- Added `fetch_game_summary()` to get play-by-play data from ESPN
- Added `parse_play_data()` to convert ESPN plays to our format
- Added `store_play()` to save individual plays to DynamoDB
- Integration only fetches summaries for active/completed games (status = 'in' or 'post')

### Files Modified
- `lambda/ingestion/handler.py` - Added 3 new functions + integration logic

### Functions Added
- `fetch_game_summary(game_id)` - Fetches detailed game data including plays
- `parse_play_data(espn_play, game_id)` - Parses individual play into DynamoDB format
- `store_play(play)` - Stores single play to DynamoDB

### Play Data Structure
```python
{
  'PK': 'GAME#2024-11-30#TEAM1-TEAM2',
  'SK': 'PLAY#{timestamp}#{playId}',
  'playId': '101904701',
  'quarter': 1,
  'gameClock': '9:52',
  'text': 'Player made shot',
  'scoringPlay': True/False,
  'homeScore': 0,
  'awayScore': 0,
  'teamId': '26',
  'playType': 'JumpShot'
}
```

### Test Results
- ✅ Tested with completed game (UCLA vs Fresno State, 11/30/2024)
- ✅ Fetched 335 plays successfully
- ✅ Stored 335/335 plays to DynamoDB
- ✅ Verified in DynamoDB: 335 play items + 22 existing = 357 total items
- ⏱️ Storage time: ~10-15 seconds for 335 plays (335 individual DynamoDB writes)

### Key Implementation Details
- Only fetches summaries for games with `statusState` = 'in' or 'post'
- Pre-game (status = 'pre') skips summary fetch (no plays exist yet)
- Each play stored individually (not batched - good for streaming updates)

### Day 8 Complete ✅
**Checkpoint:** Play-by-play data stored with each ingestion cycle

---

## Day 9 - Error Handling + Retry Logic ✅ (Completed)

### What We Built
- Added `fetch_with_retry()` function with exponential backoff
- Updated `fetch_espn_scoreboard()` and `fetch_game_summary()` to use retry logic
- Tested with simulated failures and real API calls

### Files Modified
- `lambda/ingestion/handler.py` - Added retry function, updated 2 fetch functions

### Retry Logic Implementation
```python
def fetch_with_retry(url, max_retries=3, timeout=10):
    # Exponential backoff: 1s, 2s, 4s
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (Timeout, HTTPError, RequestException):
            wait_time = 2 ** attempt
            time.sleep(wait_time)
    raise Exception(f"Failed after {max_retries} attempts")
```

### Test Results
- ✅ Simulated timeout recovery: Succeeded after 3 attempts (waited 1s, 2s)
- ✅ Simulated complete failure: Failed gracefully after 3 attempts
- ✅ Real API calls: Succeed on first attempt (no retries needed)
- ✅ Deployed to Lambda: Working in production

### CloudWatch Logs Confirmation
```
Fetching ... (attempt 1/3)
✅ ESPN API returned 2 games
Duration: 640.99 ms
```

### Day 9 Complete ✅
**Checkpoint:** Lambda handles ESPN outages gracefully

---

---

## Day 10 - Phase 1 Review + Cleanup ✅ (Completed)

### What We Reviewed
- DynamoDB data structure verification
- S3 recordings completeness check
- Code cleanup (no hardcoded values)
- CDK code backup
- AWS Console screenshots

### DynamoDB Verification
- **Total items:** 357
- **METADATA items:** 11 (unique games tracked)
- **SCORE#CURRENT items:** 11 (one per game)
- **PLAY# items:** 335 (from completed game)
- **Data structure:** ✅ Single-table design working correctly

### S3 Recordings Verification
- **Total files:** 21 (~502KB)
- **Scoreboard snapshots:** 7 (raw ESPN data)
- **Parsed game files:** 14 (7 snapshots × 2 games)
- **Folder structure:** ✅ Organized by game and data type

### Code Cleanup
- ✅ No hardcoded values found
- ✅ All configuration uses environment variables
- ✅ ESPN API URLs are public (not account-specific)

### Backup Created
```bash
backups/phase1-complete/
├── lib/           # CDK infrastructure code
├── bin/           # CDK app entry point
├── package.json   # CDK dependencies
├── cdk.json       # CDK configuration
└── handler.py     # Lambda ingestion code
```

### Git Commit
- Committed all Phase 1 work
- Message: "Phase 1 complete: Data ingestion pipeline with error handling"

### Screenshots Taken
1. ✅ DynamoDB table with items
2. ✅ S3 bucket folder structure
3. ✅ Lambda function configuration
4. ✅ EventBridge rule (disabled)
5. ✅ CloudWatch logs (successful execution)

### Day 10 Complete ✅
**Checkpoint:** All Phase 1 deliverables met

---

## 🎉 PHASE 1 COMPLETE! 🎉

### Phase 1 Deliverables (All Met ✅)
- ✅ ESPN data flows into DynamoDB automatically
- ✅ Every fetch is recorded to S3
- ✅ Error handling prevents crashes

### What Works Now
1. **EventBridge Schedule:** Triggers Lambda every 5 minutes (when enabled)
2. **ESPN API Integration:** Fetches scoreboard and game summaries with retry logic
3. **DynamoDB Storage:** Stores game metadata, scores, and play-by-play
4. **S3 Recording:** Records all data for replay mode
5. **Error Handling:** Exponential backoff retry for API failures

### Architecture Built
```
EventBridge (5 min) → Lambda (Ingestion) → DynamoDB + S3
                                          ↓
                                    Play-by-play data
```

### Phase 1 Statistics
- **Days:** 10
- **Files created:** 15+
- **AWS services:** 5 (Lambda, DynamoDB, S3, EventBridge, CloudWatch)
- **Lines of code:** ~350 (handler.py)
- **DynamoDB items:** 357
- **S3 files:** 21

### Key Decisions Made
1. **5-minute polling interval** (conservative for unofficial ESPN API)
2. **Single-table DynamoDB design** (PK/SK pattern)
3. **S3 folder structure** by game and data type
4. **Retry logic** with exponential backoff (3 attempts, 1s/2s/4s)

### Next: Phase 2 - Data Processing + WebSocket
- Set up Kinesis Data Stream
- Build Processing Lambda
- Create WebSocket API
- Build React frontend
- Display live scores in browser

---

### Day 11: Kinesis Data Stream ✅
**Completed:** December 1, 2025
**Time:** 2-3 hours

- ✅ Created Kinesis stream in CDK (`courtvision-plays`, 1 shard, 24hr retention)
- ✅ Modified Ingestion Lambda to send plays to Kinesis
- ✅ Deployed successfully
- ✅ Verified 138 plays sent to Kinesis with no errors

**Checkpoint:** Kinesis stream receives play records ✅

---

### Day 12: Processing Lambda - Setup ✅
**Completed:** December 1, 2025
**Time:** 2-3 hours

- ✅ Created Processing Lambda (`courtvision-process`, Python 3.12, 512MB, 60s timeout)
- ✅ Created ProcessingStack in CDK with Kinesis event source (batch size 10)
- ✅ Updated main CDK app to connect Processing and Ingestion stacks
- ✅ Deployed successfully (new stack: CourtVisionProcessingStack)
- ✅ Verified Processing Lambda triggers on Kinesis records (processed 138 plays in batches of 10)

**Checkpoint:** Processing Lambda triggers on Kinesis records ✅

---

### Day 13: Processing Lambda - Game State ✅
**Completed:** December 1, 2025
**Time:** 3-4 hours

- ✅ Added DynamoDB client to Processing Lambda
- ✅ Implemented update_current_score() function with DynamoDB UpdateItem
- ✅ Implemented store_play() function with DynamoDB PutItem
- ✅ Updated handler to call both functions for each play
- ✅ Deployed and tested - verified plays stored and scores updated in DynamoDB

**Checkpoint:** Game state updates correctly in DynamoDB ✅

---

### Ingestion Lambda Fix: Player ID Extraction ✅
**Completed:** December 1, 2025
**Time:** 30 minutes

**Issue:** Original parse_play_data function wasn't capturing player IDs from ESPN API

**Investigation:**
- Checked ESPN API directly: `curl https://site.api.espn.com/.../summary?event=401825729`
- Confirmed ESPN provides player data in `participants` array for women's college basketball

**ESPN Data Structure for Plays:**
```json
{
  "participants": [
    {
      "athlete": {
        "id": "5174764"  // ← Player ID
      }
    }
  ],
  "scoreValue": 2,  // Points scored (2 or 3)
  "coordinate": {
    "x": 23,  // Shot location
    "y": 5
  }
}
```

**Fix Applied:**
- Enhanced `parse_play_data()` to extract `playerId` from `participants[0].athlete.id`
- Added `pointsScored` from `scoreValue` for scoring plays
- Added `shotX` and `shotY` from `coordinate` for shot chart data

**Verified:** New plays now contain playerId field (e.g., "4899446", "5239485")

---

### Day 14: Processing Lambda - Player Stats ✅
**Date:** December 1, 2025
**Time:** ~3-4 hours

**What I Built:**
- Added player statistics tracking to Processing Lambda
- Implemented `update_player_stats()` function
- Uses DynamoDB ADD operation for accumulating points

**Technical Details:**
- PK: `PLAYER#{playerId}`
- SK: `GAME#{date}#{matchup}`
- Currently tracks: points (will expand to rebounds, assists, fouls later)
- Integrated into processing pipeline after play storage

**Verification:**
- Player 4607456: 20 points tracked ✅
- Player 5312737: 11 points tracked ✅
- CloudWatch logs show successful updates

**Checkpoint:** ✅ Player stats accumulate correctly during games

---

### Day 15: API Gateway WebSocket - Setup ✅
**Date:** December 1, 2025
**Time:** ~3-4 hours

**What I Built:**
- Created WebSocket API Gateway for real-time client connections
- Built WebSocket Lambda handler with $connect, $disconnect, and $default routes
- Implemented connection storage in DynamoDB with automatic TTL (24 hours)
- Added subscribe action to associate connections with specific games

**Technical Details:**
- Lambda: `CourtVisionWebSocketStack-WebSocketHandler47C0AA1A-fL5S5U0A8qCy`
- WebSocket URL: `wss://x54f0p0ve2.execute-api.us-east-1.amazonaws.com/prod`
- API Gateway V2 (required for WebSocket support)
- Connection schema: PK: `WS#CONNECTION`, SK: `{connectionId}`
- Fixed region mismatch issue (CDK defaulting to us-west-2 instead of us-east-1)

**Verification:**
- Connected via wscat successfully ✅
- Connection stored in DynamoDB with connectionId ✅
- Subscribe action updated gameId field ✅
- Disconnect properly removed connection from DynamoDB ✅
- CloudWatch logs showed all route handlers working correctly ✅

**Checkpoint:** ✅ WebSocket API deployed, clients can connect and subscribe to games

---

### Day 16: WebSocket - Subscribe to Games ✅
**Date:** December 1, 2025
**Time:** ~3-4 hours

**What I Built:**
- Added WebSocket push capability using API Gateway Management API
- Implemented get_current_game_state() to fetch metadata and current score from DynamoDB
- Modified subscribe handler to return current game state to client after subscription
- Added IAM permission for execute-api:ManageConnections

**Technical Details:**
- send_to_connection(): Uses apigatewaymanagementapi.post_to_connection() to push data
- get_current_game_state(): Fetches METADATA and SCORE#CURRENT items, returns JSON
- Returns game state including: homeTeam, awayTeam, status, quarter, scores, gameClock, lastUpdated
- IAM policy added: `execute-api:ManageConnections` on WebSocket API connections
- Game state type: `{"type": "game_state", ...}`

**Verification:**
- Connected via wscat and sent subscribe message ✅
- Received full game state JSON back through WebSocket ✅
- CloudWatch logs showed: "✅ Retrieved game state" and "✅ Sent data to connection" ✅
- Game state included: Villanova 81, West Virginia 59, final status ✅

**Checkpoint:** ✅ Client can subscribe to specific games and receive current game state

---

### Day 17: WebSocket - Push Updates ✅
**Date:** December 1, 2025
**Time:** ~3-4 hours

**What I Built:**
- Created Push Lambda triggered by DynamoDB Streams for real-time updates
- Fixed GSI1 population to enable querying connections by gameId
- Implemented get_game_connections() using GSI1 to find all subscribed clients
- Added push_to_connection() with API Gateway Management API
- Implemented stale connection cleanup (handles GoneException)

**Technical Details:**
- Lambda: `CourtVisionWebSocketStack-PushHandler50B0D49E-CpvpZnvGNmIh`
- Trigger: DynamoDB Streams on courtvision-games table
- Filter: Only processes SCORE#CURRENT updates for GAME# items
- GSI1 structure: GSI1PK = gameId, GSI1SK = connectionId
- Push data type: `{"type": "score_update", "homeScore": X, "awayScore": Y, ...}`
- Error handling: Automatically deletes stale connections on 410 GoneException

**Verification:**
- Connected client via wscat and subscribed to game ✅
- Manually updated score in DynamoDB (85-60 with "TEST" clock) ✅
- Push Lambda triggered by DynamoDB Streams ✅
- Found 1 connection via GSI1 query ✅
- Successfully pushed update to connected client ✅
- Client received real-time score update in wscat ✅

**Full Pipeline Tested:**
```
DynamoDB Update → Streams → Push Lambda → GSI1 Query → WebSocket Push → Client Receives
```

**Checkpoint:** ✅ Score changes push to connected WebSocket clients in real-time

---

### Day 18: React Frontend - Setup ✅
**Date:** December 1, 2025
**Time:** ~3-4 hours

**What I Built:**
- Created React app with TypeScript template
- Installed and configured Tailwind CSS v3 with PostCSS
- Set up custom color palette based on Paris 2024 Olympics theme
- Created basic page structure with React Router
- Configured environment variables for API endpoints

**Technical Details:**
- Framework: React 18 with TypeScript
- Styling: Tailwind CSS v3
- Routing: React Router v6
- Custom colors in tailwind.config.js:
  * cv-pink: #e7b4dd
  * cv-beige: #d6cabc
  * cv-teal: #70cfcb
  * cv-blue: #067adf
  * cv-navy: #01608e (background)
- Routes: `/` (Dashboard), `/game/:gameId` (GameView)
- Environment variables: REACT_APP_WEBSOCKET_URL, REACT_APP_API_URL

**Verification:**
- App runs on localhost:3000 ✅
- Tailwind styling applied with custom colors ✅
- Dashboard route accessible at / ✅
- GameView route accessible at /game/:gameId ✅
- Environment variables load correctly ✅

**Checkpoint:** ✅ React app runs locally with Tailwind styling and routing

---

### Day 19 Extended: REST API for ESPN ID Lookups

**Why:** Clean, shareable URLs using ESPN's numeric game IDs instead of encoded internal keys.

**What We Built:**
- REST API Gateway: `https://i0ui9626c5.execute-api.us-east-1.amazonaws.com/prod/`
- API Lambda: Queries GSI2 by `espnGameId`, returns full game data
- React integration: Fetches game by ESPN ID, then subscribes to WebSocket

**Flow:**
1. User visits `/game/401825729`
2. React calls `GET /game/401825729`
3. API queries GSI2, returns full gameId + metadata
4. React subscribes to WebSocket with full gameId
5. Real-time updates work as before

**Key Files:**
- `lambda/api/handler.py` - REST API Lambda
- `lib/stacks/websocket-stack.ts` - Added REST API Gateway
- `frontend/src/pages/GameView.tsx` - Fetch-then-subscribe pattern

**Verified:** ✅ Clean URLs, ✅ Real-time updates working

---

### Day 19 Extended: REST API for ESPN ID Lookups

**Completed:** December 1-2, 2025

**What We Built:**
- REST API Gateway for game lookups by ESPN ID
- API Lambda queries GSI2, returns full game data
- React integration: fetch game metadata, then subscribe to WebSocket
- Clean URLs: `/game/401825729` instead of URL-encoded internal keys

**Key Achievement:** Professional URL structure with ESPN's numeric game IDs

**Files:**
- `lambda/api/handler.py` - REST API Lambda with GSI2 queries
- `lib/stacks/websocket-stack.ts` - Added REST API Gateway
- `frontend/src/pages/GameView.tsx` - Fetch-then-subscribe pattern

---

### Day 20: Pipeline Testing + ESPN API Investigation

**Completed:** December 2, 2025

**What We Tested:**
- ✅ Full pipeline: ESPN → DynamoDB → WebSocket → React
- ✅ Real-time updates working (< 2 seconds)
- ✅ REST API + WebSocket integration
- ✅ Clean ESPN ID URLs

**ESPN API Investigation:**
- Discovered: Public API returns Top 25 games only (~2-4 games/day)
- Verified: Both ranked team games appear (Washington #21, West Virginia #25)
- Conclusion: Sufficient for portfolio demo; production would need ESPN partnership

**Phase 2 Status:** ✅ **COMPLETE**

---

## Phase 2 Summary

**Deliverables Achieved:**
✅ Live scores display in React  
✅ WebSocket push updates in < 2 seconds  
✅ End-to-end pipeline working  
✅ REST API for clean URLs  
✅ Real-time score changes verified  

**Architecture:**
- EventBridge triggers Lambda every 60 seconds
- Ingestion → Kinesis → Processing → DynamoDB
- DynamoDB Streams → Push Lambda → WebSocket → React
- REST API for initial game lookup via ESPN ID

**Next Phase:** Phase 3 - AI Features (Win Probability + Commentary)

---

## Day 21: Bedrock Setup ✅
**Date:** December 2, 2025
**Duration:** ~1 hour

### Tasks Completed
1. ✅ Verified AWS Bedrock region (us-east-1)
2. ✅ Created `test_bedrock.py` - local Bedrock API test script
3. ✅ Fixed model ID to use inference profile (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`)
4. ✅ Successfully tested Bedrock API call - confirmed working
5. ✅ Added Bedrock IAM permissions to Processing Lambda in CDK

### Key Decisions
- **Model ID:** Using `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (cross-region inference profile)
- **No manual model access needed:** AWS auto-enables models on first invoke
- **Bedrock permissions added but not deployed yet:** Will deploy with AI Lambda functions in Day 22+

### Files Modified
- Created: `test_bedrock.py`
- Modified: `lib/stacks/processing-stack.ts` (added Bedrock IAM policy)

### Test Results
```
✅ Bedrock API call successful!
Response: Bedrock is working
📊 Token Usage: 27 input / 8 output tokens
```

### Next Steps
- Day 22: Create AI Orchestrator Lambda (DynamoDB Streams trigger)

---

## Day 22: AI Orchestrator Lambda ✅
**Date:** December 2, 2025
**Duration:** ~2 hours

### Tasks Completed
1. ✅ Created AI Orchestrator Lambda (`courtvision-ai-orchestrator`)
2. ✅ Implemented "should analyze" logic for event detection
3. ✅ Created AI Stack in CDK with DynamoDB Streams trigger
4. ✅ Deployed AI Stack successfully
5. ✅ Verified Orchestrator detects score updates and routes correctly

### Key Decisions
- **Trigger conditions:** Scoring plays, score updates, game completion
- **Routing logic:** Maps trigger types to specific AI Lambda functions
- **Performance:** 2ms execution time, 88MB memory usage

### Files Created
- `lambda/ai/orchestrator/handler.py`
- `lib/stacks/ai-stack.ts`

### Files Modified
- `bin/03-aws-courtvision-ai.ts` (added AI Stack)

### Test Results
```
✅ Score update detected
📊 Trigger types: ['score_update']
→ Would invoke: Win Probability Lambda
✅ Orchestrator processed 1 AI-worthy events
Duration: 2.03 ms
```

### Next Steps
- Day 23: Win Probability - Prompt Engineering

---

## Day 23: Win Probability - Prompt Engineering ✅
**Date:** December 2, 2025
**Duration:** ~2 hours

### Tasks Completed
1. ✅ Submitted Anthropic use case form - approved instantly
2. ✅ Created `test_win_probability.py` with comprehensive test scenarios
3. ✅ Designed win probability prompt with structured JSON output
4. ✅ Tested 4 game scenarios: close game, tied, blowout, nail-biter
5. ✅ Verified JSON consistency and probability accuracy

### Test Results
- **Close Game (Q3, 6pt lead):** 78% - 22% ✅
- **Tied Game (Q4 start):** 58% - 42% ✅
- **Blowout (Q4, 23pt lead):** 99.9% - 0.1% ✅
- **Nail-biter (Q4, <1min, 2pt lead):** 68% - 32% ✅

All probabilities sum to 1.0, reasoning is contextually appropriate

### Key Decisions
- **Prompt format:** Structured with game state parameters and JSON response
- **Context included:** Score, time, momentum, shooting percentages
- **Reasoning required:** 2-3 sentence explanation of key factors
- **No iteration needed:** First prompt version is production-ready

### Files Created
- `test_win_probability.py`

### Next Steps
- Day 24: Build Win Probability Lambda

---

## Day 24: Win Probability Lambda ✅
**Date:** December 2, 2025
**Duration:** ~3 hours

### Tasks Completed
1. ✅ Created Win Probability Lambda (`courtvision-ai-winprob`)
2. ✅ Implemented game context gathering from DynamoDB
3. ✅ Integrated Bedrock API for probability calculation
4. ✅ Fixed cross-region inference profile permissions (wildcard resources)
5. ✅ Updated Orchestrator to invoke Win Prob Lambda on score updates
6. ✅ Deployed and tested end-to-end flow with live ESPN data
7. ✅ Verified DynamoDB storage (CURRENT + historical records)

### Test Results
```
Game: South Florida Bulls 0 - UConn Huskies 0
✅ Win Probability: 35.0% - 65.0%
✅ Stored win probability in DynamoDB
Duration: 4.7 seconds
```

### Key Decisions
- **Model:** `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (cross-region inference profile)
- **Permissions:** Wildcard for cross-region routing (`arn:aws:bedrock:*::foundation-model/*`)
- **Storage:** Both CURRENT (latest) and timestamped historical records
- **Invocation:** Async (`InvocationType='Event'`) to avoid blocking Orchestrator

### Files Created
- `lambda/ai/winprob/handler.py`

### Files Modified
- `lib/stacks/ai-stack.ts` (added Win Prob Lambda, Bedrock permissions)
- `lambda/ai/orchestrator/handler.py` (added invocation logic)

### Issues Resolved
- ❌ Initial: Direct model ID not allowed → Must use inference profile
- ❌ Cross-region routing: Profile routed to us-west-2 → Used wildcard permissions
- ✅ Final: Working with wildcard Bedrock permissions

### Next Steps
- Day 25: Win Probability - Frontend display


---

## Day 25: Win Probability - Frontend ✅
**Date:** December 2, 2025
**Duration:** ~3 hours

### Tasks Completed
1. ✅ Created `WinProbabilityBar.tsx` component with animated gradient bar
2. ✅ Created `WinProbabilityReasoning.tsx` component with AI analysis display
3. ✅ Integrated components into `GameView.tsx`
4. ✅ Updated `useWebSocket.ts` to handle win probability messages
5. ✅ Fixed Push Lambda double GAME# prefix bug
6. ✅ Deployed and tested end-to-end flow
7. ✅ **Verified real-time win probability display working**

### UI Features
- **Gradient Bar:** Blue (home) to red (away) with percentages
- **Smooth Animations:** 700ms transitions when probability updates
- **AI Analysis Box:** Lightbulb icon, reasoning text, timestamp
- **Team Labels:** Clear home/away team identification

### Bug Fixes
- **Push Lambda:** Fixed double `GAME#` prefix in `get_connections_for_game()`
  - Was: `f'GAME#{game_id}'` (created `GAME#GAME#...`)
  - Now: `game_id` (already has `GAME#` prefix)

### Test Results
```
Game: Pennsylvania Quakers 63 - Texas Longhorns 81 (Final)
Win Probability: 99% - 1%
Reasoning: "18+ point leads maintained 99% of the time in Q1"
WebSocket: Connected, messages received in <1 second
```

### Files Created
- `frontend/src/components/WinProbabilityBar.tsx`
- `frontend/src/components/WinProbabilityReasoning.tsx`

### Files Modified
- `frontend/src/pages/GameView.tsx` (integrated components)
- `frontend/src/hooks/useWebSocket.ts` (handle win_probability messages)
- `lambda/push/handler.py` (fixed double GAME# prefix bug)

### Next Steps
3. Dashboard / Game Listings 🏠
Current state: Dashboard is a placeholder (just says "Game list will go here")
The question: Should we build the dashboard now or later?
Option A: Build Dashboard Now (Recommended)
Pros:

Makes the app actually usable
Can see and click on today's games
Better for demos/interviews
Only takes ~2 hours

When: Could do this as "Day 25.5" before moving to Day 26
What it involves:

Fetch today's games from REST API
Display as clickable cards
Filter by status (live, upcoming, completed)

---

## Day 26: Win Probability Historical Graph ✅
**Date:** December 2, 2025
**Duration:** ~2 hours

### Tasks Completed
1. ✅ Added `get_win_prob_history()` function to API Lambda
2. ✅ Created REST API route `/game/{espnGameId}/win-probability`
3. ✅ Updated CDK websocket-stack.ts with new API Gateway route
4. ✅ Fixed API Gateway auto-deployment issue (permanent fix)
5. ✅ Created WinProbabilityGraph.tsx component with Recharts
6. ✅ Integrated graph into GameView.tsx
7. ✅ Implemented smart conditional rendering (bar vs graph)

### API Endpoint Test Results
```bash
curl "https://i0ui9626c5.execute-api.us-east-1.amazonaws.com/prod/game/401817387/win-probability"

Response: 40 historical probability records
- Game start: 35% - 65%
- Q1 lead: 12% - 88%
- Q3 dominance: 2% - 98%
- Q4 finish: 0.01% - 99.99%
```

### Key Features
- **Timeline Graph:** Recharts line chart with 300px height
- **Dual Lines:** Blue (home) and red (away) win percentages
- **Reference Line:** 50% marker showing even odds
- **Responsive:** Full-width container with proper scaling
- **Smart Display:** Graph always shows if history exists; bar+analysis only for live games
- **Data Count:** Shows "X probability calculations during game" below graph

### Files Created
- `frontend/src/components/WinProbabilityGraph.tsx` - Recharts timeline component

### Files Modified
- `lambda/api/handler.py` - Added `get_win_prob_history()` function and route handler
- `lib/stacks/websocket-stack.ts` - Added win-probability resource and auto-deploy config
- `frontend/src/pages/GameView.tsx` - Integrated graph with conditional rendering

### Issues Resolved
**Problem:** API Gateway routes configured but not deployed to `prod` stage
- **Symptom:** 404 "Missing Authentication Token" despite route existing in configuration
- **Root Cause:** CDK updates routes but doesn't auto-deploy without `deploy: true` setting
- **Solution 1 (immediate):** Manual deployment via `aws apigateway create-deployment`
- **Solution 2 (permanent):** Added `deploy: true` and `deployOptions` to RestApi in CDK
- **Prevention:** All future route changes will auto-deploy to prod stage

### CDK Auto-Deploy Fix
Added to `websocket-stack.ts`:
```typescript
const restApi = new apigateway.RestApi(this, 'GameApi', {
  // ... existing config
  deploy: true,  // NEW
  deployOptions: {  // NEW
    stageName: 'prod',
  },
});
```

### Display Logic
**Live Games (winProbability exists):**
- Win Probability bar with current percentages
- AI Analysis with reasoning and timestamp
- Historical timeline graph

**Completed Games (no current winProbability):**
- Historical timeline graph only
- Shows full game story from start to finish

### Next Steps
- Day 27: AI Commentary - Prompt Engineering
---

### Day 27: AI Commentary - Prompt Engineering ✅
**Date:** December 2, 2025  
**Time Spent:** ~3 hours

#### Tasks Completed:
1. ✅ Created commentary prompt based on blueprint specifications
2. ✅ Manual testing in AWS Bedrock Console with 3 diverse play types
3. ✅ Refined prompt to reduce hallucinations and enforce sentence limits
4. ✅ Built automated test script (`tests/test-commentary.py`)
5. ✅ Tested against live USC vs Saint Mary's game (54 scoring plays)
6. ✅ Calibrated excitement levels (0.3-0.9 range working well)

#### Test Results:
- **85% pass rate** (46/54 plays passed validation)
- **Tested play types:** Three-pointers, layups, dunks, free throws
- **Issues found:** 8 plays had minor issues (3 sentences, clichés like "from downtown")
- **No hallucinations** in final prompt version (player stats, positions)

#### Key Prompt Rules:
```python
CRITICAL RULES:
1. MAXIMUM 2 sentences. No exceptions.
2. DO NOT invent player details (year, position, etc.) not provided
3. DO NOT use clichés: "ice water in veins", "nothing but net", "from downtown"
4. Only mention facts explicitly provided in the data
5. Match excitement to play significance (0.3-0.5 routine, 0.7-0.9 clutch)
```

#### Files Created:
- `tests/test-commentary.py` - Automated testing script
- `tests/live-game-data.json` - Live game data for testing
- `tests/.venv/` - Virtual environment for local testing

#### Sample Output:
```json
{
  "commentary": "Kara Dunn knocks down the triple! Great dish from Malia Samuels to set up the three-pointer.",
  "excitement": 0.5
}
```

#### Issues Resolved:
- Prompt initially generated 3 sentences consistently
- Added explicit "MAXIMUM 2 sentences" rule
- Removed player class/position hallucinations
- Blocked common basketball clichés

#### Next Steps:
- Day 28: Build Commentary Lambda to generate commentary for live games
- Integrate prompt with DynamoDB Streams trigger
- Push commentary to WebSocket for real-time display

---

## Day 28: AI Commentary Lambda (December 2, 2025)

**Goal:** Build Lambda function to generate AI commentary for scoring plays

**Status:** ✅ COMPLETE

### Tasks Completed:
1. ✅ Created Commentary Lambda (`lambda/ai/commentary/handler.py`)
2. ✅ Implemented Bedrock integration with Claude 3 Sonnet
3. ✅ Added validation to prevent hallucinations
4. ✅ Connected DynamoDB Stream trigger (scoring plays only)
5. ✅ Implemented commentary storage in DynamoDB
6. ✅ Added WebSocket push functionality
7. ✅ Deployed and tested end-to-end

### Files Created/Modified:
- `lambda/ai/commentary/handler.py` - Full Lambda implementation
- `lib/stacks/ai-stack.ts` - Added Commentary Lambda to CDK

### Key Features:
- **Prompt Engineering:** Uses Day 27 tested prompt with strict validation rules
- **Validation:** Blocks hallucinations (class years, positions not provided)
- **Bedrock Model:** anthropic.claude-3-sonnet-20240229-v1:0
- **Trigger:** DynamoDB Streams (INSERT events on PLAY# items with scoringPlay=true)
- **Storage:** Stores in DynamoDB with SK pattern `AI#COMMENTARY#{timestamp}`
- **WebSocket:** Pushes commentary to connected clients in real-time

### Test Results:
- ✅ Lambda triggers correctly on scoring plays
- ✅ Bedrock generates 2-sentence commentary
- ✅ Validation blocks hallucinations (tested with "guard" example)
- ✅ Commentary stored successfully in DynamoDB
- ✅ WebSocket push attempted (0 connections during test - expected)
- ✅ Excitement calibration working (0.6-0.7 range for test plays)

### Sample Output:
```json
{
  "commentary": "Third Player from Santa Clara splashes home the three-ball! The Broncos have taken the lead, now up 15-12 over San Jose State.",
  "excitement": 0.7
}
```

### Known Limitations:
- Player stats show 0 PTS/REB/AST (not tracked yet - Day 28.5 will fix)
- No player milestone detection yet
- No foul trouble context yet

### Next Steps:
- Day 28.5: Add player stats tracking in Processing Lambda
- Day 29: Build frontend commentary display component

### AWS Resources:
- Lambda: `courtvision-ai-commentary` (not explicitly named, CDK auto-generates)
- Trigger: DynamoDB Stream on `courtvision-games` table
- Permissions: Bedrock InvokeModel, DynamoDB Read/Write, WebSocket Execute

---

## Day 28.5: Player Stats Tracking (December 3, 2025)

**Goal:** Track minimal player statistics in Processing Lambda so Commentary Lambda can reference real game stats

**Status:** ✅ COMPLETE

### Tasks Completed:
1. ✅ Added `calculate_stats_delta()` function to Processing Lambda
2. ✅ Updated `update_player_stats()` to store accumulated stats
3. ✅ Added `get_player_stats()` function to Commentary Lambda
4. ✅ Updated commentary prompt to include real player stats
5. ✅ Fixed missing `playerId` bug in `extract_play_from_stream()`
6. ✅ Tested end-to-end with multiple plays from same player

### Files Modified:
- `lambda/processing/handler.py` - Added stats calculation and storage
- `lambda/ai/commentary/handler.py` - Added stats fetching, fixed playerId bug

### Stats Tracked:
- **Points** - Total points scored
- **FG Made/Attempted** - Field goals for shooting percentages
- **3PT Made/Attempted** - Three-pointers for hot shooting detection
- **Fouls** - For foul trouble context

### DynamoDB Schema:
```json
{
  "PK": "PLAYER#99999",
  "SK": "GAME#2025-12-03#TEST-GAME#STATS",
  "playerId": "99999",
  "playerName": "Stats Test Player",
  "team": "Santa Clara",
  "gameId": "GAME#2025-12-03#TEST-GAME",
  "points": 13,
  "fgMade": 5,
  "fgAttempted": 5,
  "threeMade": 2,
  "threeAttempted": 2,
  "fouls": 0,
  "lastUpdated": "2025-12-03T21:17:24.033638Z"
}
```

### Test Results:
- ✅ Stats accumulate correctly across multiple plays (8→11→13 points)
- ✅ Processing Lambda logs show per-play deltas (+3 pts, +2 pts)
- ✅ Commentary Lambda logs show accumulated totals (13 PTS, 5-5 FG)
- ✅ AI commentary references stats subtly ("hot shooting", "two more")
- ✅ Missing attributes (fouls=0) handled gracefully with defaults

### Sample Commentary Output:
```
Stats Test Player converts the layup for two more! The Broncos have ridden her hot shooting to build a double-digit lead over San Jose State.
```

**Prompt includes:** "13 PTS, 5-5 FG, 2-2 3PT, 0 Fouls"

### Bug Fixed:
- Commentary Lambda was passing `playerId=None` to `get_player_stats()`
- Added missing `playerId` extraction from DynamoDB Stream record
- Now correctly fetches accumulated stats for each player

### Architecture Notes:
- Processing Lambda writes stats (via Kinesis trigger)
- Commentary Lambda reads stats (via DynamoDB get_item)
- Clear separation of concerns: write vs read
- Stats persist per game with pattern `PLAYER#{id}/GAME#{id}#STATS`

### Known Limitations:
- Commentary could be more explicit about stats (e.g., "That's her 13th point!")
- Prompt tuning needed for better stat mentions (Day 30)
- Not tracking rebounds/assists yet (future enhancement)

### Next Steps:
- Day 29: Build frontend commentary display component
- Day 30: Tune commentary quality for better stat references

---

### Day 29: AI Commentary Frontend + Critical Bug Fixes ✅
**Date: December 3-4, 2025**
**Time: ~8 hours (extended session)**

#### What We Built:
- ✅ Created AICommentary.tsx React component
  - Auto-scrolling feed with newest commentary at top
  - Excitement-based styling (3 levels: high/medium/low)
  - Gradient backgrounds and animations
  - Empty state message
- ✅ Added historical commentary loading via REST API
  - GET /game/{espnGameId}/commentary endpoint
  - Returns last 50 commentary items, newest first
  - Frontend loads on page mount
- ✅ WebSocket integration for live commentary
  - Real-time updates pushed from Lambda
  - Duplicate prevention by playId

#### Critical Bugs Fixed:
1. **"Unknown" Player Names Bug**
   - **Problem:** ESPN API has no `action` field; Processing Lambda checked ghost field
   - **Root Cause:** Ingestion Lambda stores `playType` and `text`, not `action`
   - **Fix:** Changed Processing Lambda to check `text` field instead
   - **Files Modified:** `lambda/processing/handler.py` (lines 28-63)

2. **Player Stats Triple-Counting Bug**
   - **Problem:** Zee Spearman showing 38 points instead of 13 (3x accumulation)
   - **Root Cause:** Processing Lambda used `ADD` without deduplication; multiple ingestion runs counted same plays
   - **Fix:** Added `play_already_processed()` check before processing
   - **Files Modified:** `lambda/processing/handler.py` (added lines 115-130, modified handler function)

3. **Missed Shots Not Tracked Bug**
   - **Problem:** Players showing perfect shooting % (21-21 FG instead of 4-11)
   - **Root Cause:** Processing Lambda checked `action` field for "miss" but field doesn't exist
   - **Fix:** Changed to check `text` field (e.g., "Lara Somfai missed Jumper.")
   - **Files Modified:** `lambda/processing/handler.py` (lines 56-63)

4. **Dashboard Showing 0-0 Scores Bug**
   - **Problem:** Dashboard fetched from METADATA (initial scores)
   - **Fix:** API Lambda now also fetches SCORE#CURRENT for each game
   - **Files Modified:** `lambda/api/handler.py` (get_todays_games function)

5. **React Key Warnings**
   - **Problem:** Duplicate playIds when same play processed multiple times
   - **Fix:** Changed key from `playId` to `${playId}-${timestamp}`
   - **Files Modified:** `frontend/src/components/AICommentary.tsx`

#### Testing & Verification:
- Deleted all DynamoDB data (3600+ items)
- Re-ingested with fixes applied
- Verified Zee Spearman stats: 13 PTS, 4-11 FG, 1-3 3PT ✅ (matches ESPN)
- Confirmed commentary shows realistic player stats
- No more duplicate key warnings in React

#### Issues Identified (Not Fixed):
- Win Probability X-axis uses "calculation count" instead of game minutes (addressed in Day 30)
- Win Probability not triggering consistently for all games

**Checkpoint Achieved:** ✅ AI Commentary displays with correct player names and realistic stats!

**Files Modified:**
- `lambda/processing/handler.py` (major refactor)
- `lambda/api/handler.py` (dashboard scores)
- `lambda/ingestion/handler.py` (player name extraction)
- `frontend/src/components/AICommentary.tsx` (new component)
- `frontend/src/hooks/useWebSocket.ts` (commentary handling)
- `frontend/src/pages/GameView.tsx` (historical commentary fetch)
- `frontend/tailwind.config.js` (slideIn animation)

**Deployment:**
- Manual Lambda updates via AWS CLI (CDK caching issues)
- Processing Lambda timeout increased to 120 seconds

---



---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---

---



---