# CourtVision AI - Implementation Timeline

## Overview

This timeline breaks the project into **6 phases** across **12 weeks**. Each phase is a natural stopping point where you should **start a new chat session** with Claude.

**Why new chats matter:**
- Context windows fill up and Claude forgets early decisions
- Fresh chats let you upload the latest code as context
- Each phase has a clear deliverable you can verify before moving on
- Easier to debug when context is focused on one problem domain

---

## Phase Summary

| Phase | Duration | Focus | Deliverable | New Chat? |
|-------|----------|-------|-------------|-----------|
| Phase 1 | Days 1-10 | Infrastructure + Ingestion | Data flowing from ESPN to DynamoDB | ✅ Start fresh |
| Phase 2 | Days 11-20 | Processing + WebSocket | Live scores in React via WebSocket | ✅ Start fresh |
| Phase 3 | Days 21-35 | AI Features (Core) | Win probability + Commentary working | ✅ Start fresh |
| Phase 4 | Days 36-50 | AI Features (Extended) | Patterns + Shot charts + Summary | ✅ Start fresh |
| Phase 5 | Days 51-65 | Replay Mode + Polish | Mode 2 working, error handling | ✅ Start fresh |
| Phase 6 | Days 66-84 | Production + Demo | Deployed, documented, demo-ready | ✅ Start fresh |

---

## Phase 1: Infrastructure + Data Ingestion
**Days 1-10 | ~2 weeks**

### Goal
Get data flowing from ESPN API into DynamoDB and S3 (for recording).

### Chat Session Strategy
Start ONE chat for this entire phase. Upload the blueprint at the start.

**Opening prompt:**
> "I'm building CourtVision AI. Here's my blueprint [attach file]. Let's start Phase 1: Infrastructure + Data Ingestion. Walk me through Day 1 tasks."

---

### Day 1: Project Setup
**Time: 2-3 hours**

- [x] Create new GitHub repository
- [x] Initialize CDK project (TypeScript)
  ```bash
  mkdir courtvision-ai && cd courtvision-ai
  npx cdk init app --language typescript
  ```
- [x] Set up project structure:
  ```
  courtvision-ai/
  ├── lib/
  │   ├── stacks/
  │   │   ├── ingestion-stack.ts
  │   │   ├── processing-stack.ts
  │   │   ├── ai-stack.ts
  │   │   └── frontend-stack.ts
  │   └── constructs/
  ├── lambda/
  │   ├── ingestion/
  │   ├── processing/
  │   └── ai/
  ├── frontend/
  └── tests/
  ```
- [x] Configure AWS credentials for dev account
- [x] First CDK deploy (empty stack, just verify it works)

**Checkpoint:** `cdk deploy` succeeds with empty stack

---

### Day 2: DynamoDB Table
**Time: 2-3 hours**

- [x] Create DynamoDB table in CDK:
  - Table name: `courtvision-games`
  - Partition key: `PK` (String)
  - Sort key: `SK` (String)
  - Billing: On-demand
  - Stream: NEW_AND_OLD_IMAGES
- [x] Add GSI for date-based queries
- [x] Deploy and verify in AWS Console
- [x] Test manual item creation via Console

**Checkpoint:** DynamoDB table visible in Console, can create/read items

---

### Day 3: S3 Buckets
**Time: 1-2 hours**

- [x] Create S3 bucket for game recordings
  - Bucket name: `courtvision-recordings-{account-id}`
  - Enable versioning
  - Lifecycle rule: Move to IA after 30 days
- [x] Create S3 bucket for frontend (later)
  - Bucket name: `courtvision-frontend-{account-id}`
  - Static website hosting enabled
- [x] Deploy and verify

**Checkpoint:** Both S3 buckets visible in Console

---

### Day 4: Ingestion Lambda - ESPN Fetcher
**Time: 3-4 hours**

- [x] Create Lambda function: `courtvision-ingest`
- [x] Write ESPN API fetch logic:
  ```python
  def fetch_scoreboard():
      url = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard"
      response = requests.get(url)
      return response.json()
  ```
- [x] Parse ESPN response into internal format
- [x] Add environment variables:
  - `DATA_SOURCE`: "live"
  - `DYNAMODB_TABLE`: table name
  - `S3_BUCKET`: recordings bucket
- [x] Local testing with sample ESPN response

**Checkpoint:** Lambda runs locally, parses ESPN JSON correctly

---

### Day 5: Ingestion Lambda - DynamoDB Write
**Time: 3-4 hours**

- [x] Add DynamoDB write logic to Lambda
- [x] Implement game metadata storage:
  ```python
  def store_game_metadata(game):
      table.put_item(Item={
          'PK': f"GAME#{game['date']}#{game['matchup']}",
          'SK': 'METADATA',
          'homeTeam': game['homeTeam'],
          'awayTeam': game['awayTeam'],
          # ... other fields
      })
  ```
- [x] Implement current score storage
- [x] Deploy Lambda to AWS
- [x] Test with manual invocation

**Checkpoint:** Manual Lambda invoke writes game data to DynamoDB

---

### Day 6: Ingestion Lambda - S3 Recording
**Time: 2-3 hours**

- [x] Add S3 recording logic:
  ```python
  def record_to_s3(game_id, raw_response):
      s3.put_object(
          Bucket=RECORDINGS_BUCKET,
          Key=f"{game_id}/raw/{timestamp}.json",
          Body=json.dumps(raw_response)
      )
  ```
- [x] Record both raw ESPN response and parsed data
- [x] Test recording during Lambda execution
- [x] Verify files appear in S3

**Checkpoint:** Each Lambda run creates files in S3

---

### Day 7: EventBridge Schedule
**Time: 2-3 hours**

- [x] Create EventBridge rule in CDK:
  ```typescript
  new events.Rule(this, 'IngestionSchedule', {
    schedule: events.Schedule.rate(Duration.minutes(5)),
    targets: [new targets.LambdaFunction(ingestionLambda)],
  });
  ```
- [x] Add enable/disable flag (don't run 24/7 during dev)
- [x] Deploy and monitor CloudWatch logs
- [x] Verify data accumulates in DynamoDB

**Checkpoint:** Data automatically appears in DynamoDB every minute

---

### Day 8: Game Summary Endpoint
**Time: 3-4 hours**

- [x] Add ESPN game summary fetch:
  ```python
  def fetch_game_summary(game_id):
      url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}"
      response = requests.get(url)
      return response.json()
  ```
- [x] Parse play-by-play data
- [x] Store individual plays in DynamoDB
- [x] Handle shot location data for shot charts

**Checkpoint:** Play-by-play data stored with each ingestion cycle

---

### Day 9: Error Handling + Retry Logic
**Time: 2-3 hours**

- [x] Add try/catch around ESPN API calls
- [x] Implement exponential backoff:
  ```python
  def fetch_with_retry(url, max_retries=3):
      for attempt in range(max_retries):
          try:
              response = requests.get(url, timeout=10)
              response.raise_for_status()
              return response.json()
          except Exception as e:
              wait_time = 2 ** attempt
              time.sleep(wait_time)
      raise Exception(f"Failed after {max_retries} attempts")
  ```
- [x] Add CloudWatch alarms for failures
- [x] Test with simulated failures

**Checkpoint:** Lambda handles ESPN outages gracefully

---

### Day 10: Phase 1 Review + Cleanup
**Time: 2-3 hours**

- [x] Review all DynamoDB data structure
- [x] Verify S3 recordings are complete
- [x] Clean up any hardcoded values
- [x] Document what's built so far
- [x] **CRITICAL:** Export/save current CDK code
- [x] Take screenshots of working AWS Console views

**Phase 1 Deliverable:** 
- ESPN data flows into DynamoDB automatically
- Every fetch is recorded to S3
- Error handling prevents crashes

---

## Phase 2: Data Processing + WebSocket
**Days 11-20 | ~2 weeks**

### Goal
Process raw data into game state and push live updates to a React frontend.

### Chat Session Strategy
**START A NEW CHAT.** Upload:
1. The blueprint
2. Your current CDK code (zip or key files)
3. A summary: "Phase 1 complete. Data flows from ESPN to DynamoDB. Now starting Phase 2: Processing + WebSocket."

---

### Day 11: Kinesis Data Stream
**Time: 2-3 hours**

- [x] Create Kinesis stream in CDK:
  ```typescript
  const playStream = new kinesis.Stream(this, 'PlayStream', {
    streamName: 'courtvision-plays',
    shardCount: 1,
  });
  ```
- [x] Modify Ingestion Lambda to send plays to Kinesis
- [x] Deploy and verify records appear in stream

**Checkpoint:** Kinesis stream receives play records

---

### Day 12: Processing Lambda - Setup
**Time: 2-3 hours**

- [x] Create Lambda function: `courtvision-process`
- [x] Configure Kinesis trigger:
  ```typescript
  processingLambda.addEventSource(
    new KinesisEventSource(playStream, {
      startingPosition: StartingPosition.LATEST,
      batchSize: 10,
    })
  );
  ```
- [x] Basic handler that logs incoming records
- [x] Deploy and verify logs show Kinesis data

**Checkpoint:** Processing Lambda triggers on Kinesis records

---

### Day 13: Processing Lambda - Game State
**Time: 3-4 hours**

- [x] Parse Kinesis records into plays
- [x] Update current score in DynamoDB:
  ```python
  def update_score(play):
      table.update_item(
          Key={'PK': play['gameId'], 'SK': 'SCORE#CURRENT'},
          UpdateExpression='SET homeScore = :h, awayScore = :a, lastUpdated = :t',
          ExpressionAttributeValues={
              ':h': play['homeScore'],
              ':a': play['awayScore'],
              ':t': play['timestamp']
          }
      )
  ```
- [x] Store individual plays
- [x] Test with sample data

**Checkpoint:** Game state updates correctly in DynamoDB

---

### Day 14: Processing Lambda - Player Stats
**Time: 3-4 hours**

- [ ] Aggregate player statistics:
  ```python
  def update_player_stats(play):
      if play.get('scoringPlay'):
          table.update_item(
              Key={'PK': f"PLAYER#{play['playerId']}", 'SK': play['gameId']},
              UpdateExpression='ADD points :p',
              ExpressionAttributeValues={':p': play['pointsScored']}
          )
  ```
- [ ] Track: points, rebounds, assists, fouls, minutes
- [ ] Handle all play types from ESPN

**Checkpoint:** Player stats accumulate correctly during games

---

### Day 15: API Gateway WebSocket - Setup
**Time: 3-4 hours**

- [x] Create WebSocket API in CDK:
  ```typescript
  const webSocketApi = new apigatewayv2.WebSocketApi(this, 'GameSocket', {
    connectRouteOptions: { integration: new WebSocketLambdaIntegration('ConnectIntegration', connectHandler) },
    disconnectRouteOptions: { integration: new WebSocketLambdaIntegration('DisconnectIntegration', disconnectHandler) },
    defaultRouteOptions: { integration: new WebSocketLambdaIntegration('DefaultIntegration', defaultHandler) },
  });
  ```
- [x] Create connection handler Lambda
- [x] Store connections in DynamoDB
- [x] Deploy and test with wscat

**Checkpoint:** Can connect to WebSocket, connection stored in DynamoDB

---

### Day 16: WebSocket - Subscribe to Games
**Time: 3-4 hours**

- [x] Create subscribe route handler:
  ```python
  def handle_subscribe(event):
      connection_id = event['requestContext']['connectionId']
      body = json.loads(event['body'])
      game_id = body['gameId']
      
      # Store subscription
      table.put_item(Item={
          'PK': 'WS#CONNECTION',
          'SK': connection_id,
          'gameId': game_id,
          'connectedAt': datetime.now().isoformat()
      })
  ```
- [x] Return current game state on subscribe
- [x] Test subscription flow

**Checkpoint:** Client can subscribe to specific games

---

### Day 17: WebSocket - Push Updates
**Time: 3-4 hours**

- [x] Create push Lambda triggered by DynamoDB Streams
- [x] Find all connections for a game:
  ```python
  def get_game_connections(game_id):
      response = table.query(
          IndexName='GSI1',
          KeyConditionExpression='GSI1PK = :gid',
          ExpressionAttributeValues={':gid': game_id}
      )
      return response['Items']
  ```
- [x] Push updates to all connected clients
- [x] Handle stale connections (GoneException)

**Checkpoint:** Score changes push to connected WebSocket clients

---

### Day 18: React Frontend - Setup
**Time: 3-4 hours**

- [x] Create React app:
  ```bash
  npx create-react-app frontend --template typescript
  cd frontend
  npm install tailwindcss recharts
  ```
- [x] Set up Tailwind CSS
- [x] Create basic page structure:
  - Dashboard (game list)
  - Game view
- [x] Configure environment variables for API endpoints

**Checkpoint:** React app runs locally with Tailwind styling

---

### Day 19: React Frontend - WebSocket Integration
**Time: 4-5 hours**

- [ ] Create useWebSocket hook:
  ```typescript
  export function useWebSocket(gameId: string) {
    const [score, setScore] = useState({ home: 0, away: 0 });
    
    useEffect(() => {
      const ws = new WebSocket(WS_ENDPOINT);
      ws.onopen = () => {
        ws.send(JSON.stringify({ action: 'subscribe', gameId }));
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'score') {
          setScore(data.score);
        }
      };
      return () => ws.close();
    }, [gameId]);
    
    return { score };
  }
  ```
- [ ] Create LiveScore component
- [ ] Display real-time score updates
- [ ] Handle reconnection

**Checkpoint:** React app shows live scores updating via WebSocket

---

### Day 20: Phase 2 Review + Deploy Frontend
**Time: 3-4 hours**

- [ ] Deploy frontend to S3 + CloudFront
- [ ] Test full flow: ESPN → DynamoDB → WebSocket → React
- [ ] Document Phase 2 architecture
- [ ] Clean up and commit code
- [ ] **Record a demo video of live scores working**

**Phase 2 Deliverable:**
- Live scores display in React
- Updates push via WebSocket in < 2 seconds
- End-to-end pipeline working

---

## Phase 3: AI Features (Core)
**Days 21-35 | ~2.5 weeks**

### Goal
Add AI-powered win probability and commentary.

### Chat Session Strategy
**START A NEW CHAT.** Upload:
1. The blueprint (AI prompts section specifically)
2. Current Lambda code for reference
3. Summary: "Phase 2 complete. Live scores working in React. Now starting Phase 3: AI Features."

---

### Day 21: Bedrock Setup
**Time: 2-3 hours**

- [x] Enable Bedrock in AWS Console
- [x] Request access to Claude 3 Sonnet
- [x] Create IAM role for Bedrock access
- [x] Test Bedrock API from local script:
  ```python
  bedrock = boto3.client('bedrock-runtime')
  response = bedrock.invoke_model(
      modelId='anthropic.claude-3-sonnet-20240229-v1:0',
      body=json.dumps({
          'anthropic_version': 'bedrock-2023-05-31',
          'max_tokens': 200,
          'messages': [{'role': 'user', 'content': 'Hello!'}]
      })
  )
  ```

**Checkpoint:** Can invoke Claude via Bedrock locally

---

### Day 22: AI Orchestrator Lambda
**Time: 3-4 hours**

- [x] Create Lambda: `courtvision-ai-orchestrator`
- [x] Trigger from DynamoDB Streams
- [x] Implement "should analyze" logic:
  ```python
  def should_trigger_ai(record):
      sk = record['SK']
      
      # Trigger on scoring plays
      if sk.startswith('PLAY#') and record.get('scoringPlay'):
          return True
      
      # Trigger on significant score changes
      if sk == 'SCORE#CURRENT':
          if lead_changed(record) or big_run_detected(record):
              return True
      
      return False
  ```
- [x] Route to appropriate AI Lambda

**Checkpoint:** Orchestrator correctly identifies AI trigger events

---

### Day 23: Win Probability - Prompt Engineering
**Time: 3-4 hours**

- [ ] Create win probability prompt (from blueprint)
- [ ] Test prompt with various game states
- [ ] Iterate on prompt for consistent JSON output
- [ ] Handle edge cases:
  - Tied games
  - Blowouts (>20 points)
  - Final minutes
  - Overtime

**Checkpoint:** Prompt returns valid JSON with reasonable probabilities

---

### Day 24: Win Probability Lambda
**Time: 3-4 hours**

- [ ] Create Lambda: `courtvision-ai-winprob`
- [ ] Gather game state for prompt:
  ```python
  def get_game_context(game_id):
      # Fetch current score, shooting stats, recent plays
      return {
          'home_score': ...,
          'away_score': ...,
          'quarter': ...,
          'time_remaining': ...,
          'home_fg_pct': ...,
          'recent_trend': ...
      }
  ```
- [ ] Call Bedrock with prompt
- [ ] Parse response and store in DynamoDB
- [ ] Push update via WebSocket

**Checkpoint:** Win probability calculates and stores on scoring plays

---

### Day 25: Win Probability - Frontend
**Time: 3-4 hours**

- [x] Create WinProbabilityBar component:
  ```tsx
  const WinProbabilityBar = ({ home, away, homePct }) => (
    <div className="flex h-8 rounded-full overflow-hidden">
      <div 
        className="bg-blue-600 flex items-center justify-end pr-2"
        style={{ width: `${homePct * 100}%` }}
      >
        <span className="text-white text-sm">{Math.round(homePct * 100)}%</span>
      </div>
      <div className="bg-red-600 flex items-center pl-2 flex-1">
        <span className="text-white text-sm">{Math.round((1 - homePct) * 100)}%</span>
      </div>
    </div>
  );
  ```
- [x] Display AI reasoning below bar
- [x] Animate transitions smoothly

**Checkpoint:** Win probability bar updates in real-time

---

### Day 26: Win Probability - Historical Graph
**Time: 3-4 hours**

- [x] Store historical probability in DynamoDB
- [x] Create API endpoint for probability history
- [x] Build Recharts line graph:
  ```tsx
  <LineChart data={probabilityHistory}>
    <XAxis dataKey="timestamp" />
    <YAxis domain={[0, 1]} />
    <Line type="monotone" dataKey="homePct" stroke="#2563eb" />
    <ReferenceLine y={0.5} stroke="#666" strokeDasharray="3 3" />
  </LineChart>
  ```
- [x] Add game clock labels on X-axis

**Checkpoint:** Graph shows probability swings over time

---

### Day 27: AI Commentary - Prompt Engineering
**Time: 3-4 hours**

- [x] Create commentary prompt (from blueprint)
- [x] Test with various play types:
  - Three-pointers
  - Layups
  - Blocks
  - Turnovers
  - Free throws
- [x] Calibrate excitement levels
- [x] Ensure no hallucinated names/stats

**Checkpoint:** Commentary prompt generates varied, accurate text

---

### Day 28: AI Commentary Lambda
**Time: 3-4 hours**

- [x] Create Lambda: `courtvision-ai-commentary`
- [x] Build play context for prompt:
  ```python
  def get_play_context(play, game_state):
      player_stats = get_player_game_stats(play['playerId'], play['gameId'])
      return {
          'player_name': play['playerName'],
          'action': play['action'],
          'player_points': player_stats['points'],
          'player_rebounds': player_stats['rebounds'],
          'recent_context': get_recent_plays_summary(play['gameId'], 5)
      }
  ```
- [x] Store commentary in DynamoDB
- [x] Push to WebSocket

**Checkpoint:** Commentary generates for each scoring play

---

## Day 28.5: Player Stats Tracking

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

---

### Day 29: AI Commentary - Frontend
**Time: 3-4 hours**

- [x] Create AICommentary component
- [x] Scrolling feed of recent commentary
- [x] Style based on excitement level:
  ```tsx
  const excitementClass = excitement > 0.8 
    ? 'text-xl font-bold text-yellow-500' 
    : excitement > 0.5 
    ? 'text-lg font-semibold' 
    : 'text-base';
  ```
- [x] Animate new commentary appearing

**Checkpoint:** Commentary feed updates in real-time with varied styling

---

### Day 30: Commentary Quality Tuning
**Time: 2-3 hours**

- [x] Review generated commentary from test games
- [x] Identify repetitive patterns
- [x] Add variety instructions to prompt
- [x] Test milestone scenarios (20 pts, 30 pts, double-double)
- [x] Adjust excitement calibration

**Checkpoint:** Commentary feels natural and varied

---

### Day 31-33: Integration Testing
**Time: 3 days**

- [x] Day 31: Test full AI flow during live game
- [x] Day 32: Fix bugs, tune prompts based on real data
- [x] Day 33: Performance optimization (reduce Bedrock latency)

**Checkpoint:** AI features work reliably during live games

---

### Day 34-35: Phase 3 Review
**Time: 2 days**

- [x] Document AI prompts and tuning decisions
- [x] Review costs (Bedrock usage)
- [x] Clean up code
- [x] **Record demo video of AI features**

**Phase 3 Deliverable:**
- Win probability updates on significant events
- AI commentary generates for plays
- Both display in React with real-time updates

---

## Phase 4: AI Features (Extended)
**Days 36-50 | ~2.5 weeks**

### Goal
Add pattern detection, shot charts, and post-game summaries.

### Chat Session Strategy
**START A NEW CHAT.** Upload:
1. Blueprint (pattern detection + shot chart sections)
2. Current AI Lambda code
3. Summary: "Phase 3 complete. Win probability and commentary working. Now adding patterns, shot charts, summaries."

---

### Day 36-38: Pattern Detection
**Time: 3 days**

- [ ] Day 36: Implement scoring run detection algorithm
- [ ] Day 37: Implement hot streak + momentum shift detection
- [ ] Day 38: Create pattern alert Lambda, store in DynamoDB

**Checkpoint:** Patterns detected and stored during games

---

### Day 39-40: Pattern Detection - Frontend
**Time: 2 days**

- [ ] Create PatternAlert component (toast notifications)
- [ ] Add pattern history to game view
- [ ] Style alerts by significance level

**Checkpoint:** Pattern alerts appear in real-time

---

### Day 41-43: Shot Charts
**Time: 3 days**

- [ ] Day 41: Parse shot location data from ESPN
- [ ] Day 42: Build D3.js court component with shot markers
- [ ] Day 43: Add player filter, made/missed toggle

**Checkpoint:** Shot chart displays with real shot data

---

### Day 44-46: Post-Game Summary
**Time: 3 days**

- [ ] Day 44: Create summary prompt, test with completed games
- [ ] Day 45: Build summary Lambda, trigger on game completion
- [ ] Day 46: Create summary page in frontend

**Checkpoint:** AI summary generates when games end

---

### Day 47-50: Integration + Polish
**Time: 4 days**

- [ ] Test all features together during live games
- [ ] Fix edge cases
- [ ] Performance optimization
- [ ] **Record comprehensive demo video**

**Phase 4 Deliverable:**
- All 5 AI features working
- Full game view with all components
- Post-game summary page

---

## Phase 5: Replay Mode + Polish
**Days 51-65 | ~2.5 weeks**

### Goal
Build Mode 2 (replay) and add production polish.

### Chat Session Strategy
**START A NEW CHAT.** Upload:
1. Blueprint (replay mode section)
2. Ingestion Lambda code
3. Summary: "Phase 4 complete. All features working in live mode. Now building replay mode."

---

### Day 51-53: Replay Data Loader
**Time: 3 days**

- [ ] Day 51: Build S3 game data reader
- [ ] Day 52: Implement play sequencer with timing
- [ ] Day 53: Add speed control (1x, 5x, 10x)

**Checkpoint:** Can replay recorded games from S3

---

### Day 54-56: Replay Mode Integration
**Time: 3 days**

- [ ] Day 54: Add DATA_SOURCE environment variable switching
- [ ] Day 55: Test all features in replay mode
- [ ] Day 56: Fix any mode-specific bugs

**Checkpoint:** Replay mode indistinguishable from live mode

---

### Day 57-59: Error Handling + Edge Cases
**Time: 3 days**

- [ ] Day 57: WebSocket reconnection logic
- [ ] Day 58: Handle missing data gracefully
- [ ] Day 59: Rate limiting, timeout handling

**Checkpoint:** App handles failures gracefully

---

### Day 60-62: Performance + Cost Optimization
**Time: 3 days**

- [ ] Day 60: Add caching for AI responses
- [ ] Day 61: Optimize DynamoDB queries
- [ ] Day 62: Review and reduce Bedrock calls

**Checkpoint:** Cost per game < $1

---

### Day 63-65: UI Polish
**Time: 3 days**

- [ ] Day 63: Loading states, skeletons
- [ ] Day 64: Mobile responsiveness
- [ ] Day 65: Accessibility improvements

**Phase 5 Deliverable:**
- Replay mode working perfectly
- Production-quality error handling
- Polished UI

---

## Phase 6: Production + Documentation
**Days 66-84 | ~3 weeks**

### Goal
Deploy to production, document everything, prepare for interviews.

### Chat Session Strategy
**START A NEW CHAT.** Upload:
1. Blueprint (architecture section)
2. Summary: "App complete. Now deploying to production and documenting."

---

### Day 66-70: Production Deployment
**Time: 5 days**

- [ ] Set up production AWS account/environment
- [ ] Configure custom domain
- [ ] Set up CloudWatch dashboards
- [ ] Implement alerting
- [ ] Security review

**Checkpoint:** App running in production

---

### Day 71-75: Documentation
**Time: 5 days**

- [ ] README with setup instructions
- [ ] Architecture diagram (draw.io or Excalidraw)
- [ ] API documentation
- [ ] Cost analysis document
- [ ] Lessons learned document

**Checkpoint:** Complete documentation in repo

---

### Day 76-80: Demo Preparation
**Time: 5 days**

- [ ] Record 3-minute demo video
- [ ] Create demo script/talking points
- [ ] Build "interview game library" (5+ recorded games)
- [ ] Practice explaining architecture decisions

**Checkpoint:** Demo-ready for any interview

---

### Day 81-84: Final Polish
**Time: 4 days**

- [ ] Final bug fixes
- [ ] Portfolio website integration
- [ ] LinkedIn/resume updates
- [ ] **Celebrate!** 🎉

**Phase 6 Deliverable:**
- Production deployment
- Complete documentation
- Interview-ready demo

---

## Chat Session Cheat Sheet

| When to Start | What to Upload | Opening Message |
|---------------|----------------|-----------------|
| Day 1 | Blueprint | "Starting CourtVision AI Phase 1. Help me set up CDK infrastructure." |
| Day 11 | Blueprint + current code | "Phase 1 complete. Data flows to DynamoDB. Starting Phase 2: WebSocket." |
| Day 21 | Blueprint + Lambda code | "Phase 2 complete. Live scores in React. Starting Phase 3: AI features." |
| Day 36 | Blueprint + AI code | "Phase 3 complete. Win prob + commentary working. Adding patterns/charts." |
| Day 51 | Blueprint + ingestion code | "Phase 4 complete. All features working. Building replay mode." |
| Day 66 | Blueprint + architecture notes | "Phase 5 complete. App works. Deploying to production." |

---

## Time Estimates Summary

| Phase | Days | Hours (estimated) |
|-------|------|-------------------|
| Phase 1 | 10 | 25-30 hours |
| Phase 2 | 10 | 30-35 hours |
| Phase 3 | 15 | 40-50 hours |
| Phase 4 | 15 | 35-45 hours |
| Phase 5 | 15 | 35-40 hours |
| Phase 6 | 19 | 30-40 hours |
| **Total** | **84 days** | **195-240 hours** |

At 2-3 hours per day, this is a **12-week project**.
At 4-5 hours per day, this is a **6-8 week project**.

---

## Tips for Success

1. **Don't skip checkpoints.** Each one verifies something works before building on it.

2. **Commit frequently.** At minimum, commit at every checkpoint.

3. **Record demos early.** Don't wait until the end. Record each phase's deliverable.

4. **Start new chats at phase boundaries.** Fresh context = better help.

5. **Keep a "decisions log."** Write down why you made architectural choices.

6. **Test with real games.** Don't just use test data—watch actual basketball while developing.

7. **Budget for debugging.** The timeline includes buffer, but bugs happen.

Good luck! 🏀