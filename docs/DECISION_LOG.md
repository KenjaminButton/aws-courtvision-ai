# CourtVision AI - Decision Log

**Purpose:** Document all major technical and architectural decisions for future reference and interview preparation.

---

## Project Pivot Decision
**Date:** December 11, 2024  
**Decision:** Change from "all women's college basketball games" to "Iowa Hawkeyes only, historical analysis"

### Context
Original plan was to track ALL women's college basketball games in real-time during the season. This had several problems:
- Dependent on basketball season (Nov-April)
- Can't demo during off-season
- Too broad - surface-level insights
- Real-time complexity without added value

### Decision
Focus exclusively on Iowa Hawkeyes with historical analysis:
- All games from 2024-25 season (and potentially 2023-24)
- Deep per-player analytics
- Season-long trends
- Always demo-able

### Rationale
1. **Better storytelling:** "I know Iowa basketball intimately" vs "I track random games"
2. **Richer insights:** Season-long player tracking vs one-game snapshots
3. **Always demo-able:** Historical data always available
4. **Simpler architecture:** No real-time complexity for MVP
5. **More impressive:** Deep analysis beats surface coverage

### Trade-offs
- ❌ Lost: Real-time "wow factor" of live updates
- ❌ Lost: Breadth across many teams
- ✅ Gained: Depth of analysis
- ✅ Gained: Reliability for demos
- ✅ Gained: Manageable scope

### Status: ✅ Confirmed

---

## Tech Stack Decisions

### Frontend: Plain React vs Next.js
**Date:** December 11, 2024  
**Decision:** Use Plain React (not Next.js)

### Context
Next.js is trendy and looks good on resumes, but the project will be hosted on AWS (S3 + CloudFront), not Vercel.

### Options Considered

**Option A: Next.js with SSR on AWS**
- Requires: Amplify or EC2/Fargate running Node.js
- Cost: $20-50/month
- Complexity: High
- Value: SSR/SSG not needed for this app

**Option B: Next.js Static Export**
- Deploy to S3 like React
- Problem: Loses all Next.js benefits
- Why use Next.js if not using its features?

**Option C: Plain React + TypeScript**
- Deploy to S3 + CloudFront
- Cost: $4/month
- Shows AWS architecture skills
- Perfect fit for client-side data viz

### Decision: Plain React + TypeScript

### Rationale
1. **Better AWS story:** "I built serverless architecture on AWS" > "I deployed to Vercel"
2. **Cost-effective:** $4/month vs $20-50/month
3. **Right tool:** No need for SSR in data visualization dashboard
4. **AWS skills showcase:** Full serverless stack shows more technical depth

### Interview Talking Point
> "I chose React over Next.js because the app is a client-side data visualization tool deployed on AWS. I wanted to showcase AWS serverless architecture (S3, CloudFront, API Gateway, Lambda, DynamoDB) rather than abstract it behind a framework. This gave me more control and demonstrated full-stack AWS knowledge."

### Status: ✅ Confirmed

---

### State Management: No Redux
**Date:** December 11, 2024  
**Decision:** Use React Context + hooks (no Redux)

### Rationale
- App state is simple (current season, selected game)
- Data flows from API → components
- No complex state interactions
- Redux would be overkill

### Status: ✅ Confirmed

---

## Backend Decisions

### Language: Python (not Node.js)
**Date:** December 11, 2024  
**Decision:** Python for all Lambda functions

### Rationale
1. **Pattern detection:** Python is better for data analysis
2. **boto3:** Native AWS SDK for Python is excellent
3. **Consistency:** All backend code in one language
4. **Personal preference:** You're more comfortable in Python

### Status: ✅ Confirmed

---

### Database: DynamoDB Single-Table Design
**Date:** December 11, 2024  
**Decision:** Use single-table design in DynamoDB

### Context
Could have used:
- Multiple DynamoDB tables (games, players, patterns)
- RDS (PostgreSQL)
- DocumentDB (MongoDB-compatible)

### Decision: Single-table DynamoDB

### Rationale
1. **Cost:** On-demand pricing, pay per request
2. **Scalability:** Auto-scales infinitely
3. **Serverless:** No database management
4. **Access patterns:** Well-defined, predictable queries
5. **Industry standard:** Common pattern for sports data

### Schema Design
```
PK: Entity type + identifier
SK: Sorting key

Examples:
- SEASON#2024-25 / GAME#{date}#{matchup}
- GAME#{date}#{matchup} / METADATA
- GAME#{date}#{matchup} / PLAY#{timestamp}
- PLAYER#{id} / GAME#{date}#{matchup}#STATS
- PLAYER#{id} / SEASON#2024-25#SUMMARY
```

### Trade-offs
- ❌ Less flexible than SQL for ad-hoc queries
- ❌ Must design access patterns upfront
- ✅ Extremely fast for known queries
- ✅ Cost-effective
- ✅ No database maintenance

### Status: ✅ Confirmed

---

### Real-Time Pipeline: Kinesis vs SQS
**Date:** December 11, 2024  
**Decision:** Keep Kinesis (already set up)

### Context
For processing play-by-play events, could use:
- Kinesis Data Streams
- SQS (Simple Queue Service)
- Direct Lambda invocation

### Decision: Kinesis Data Streams

### Rationale
1. **Already built:** Infrastructure exists
2. **Ordered processing:** Kinesis guarantees order (important for play sequence)
3. **Replay capability:** Can replay stream if needed
4. **Future-proof:** If we add real-time later, Kinesis ready

### Trade-offs
- Kinesis: $15/month (1 shard)
- SQS: Would be ~$2/month
- Decision: Keep Kinesis for ordering guarantees

### Status: ✅ Confirmed

---

## Data Processing Decisions

### Pattern Detection: Deterministic Algorithms
**Date:** December 11, 2024  
**Decision:** Use rule-based pattern detection (not ML)

### Context
Could have used:
- Rule-based algorithms (if score 8-0 in window → pattern)
- Machine learning (train model to detect patterns)
- AI-only (just ask Claude to find patterns)

### Decision: Rule-based algorithms + AI enrichment

### Rationale
1. **Explainable:** Can explain exactly why pattern was detected
2. **Reliable:** Deterministic, no training needed
3. **Fast:** Real-time capable
4. **AI for enrichment:** Use Claude to add context/description

### Patterns Detected
1. **Scoring Runs:** Multi-window analysis (25, 50, 75, 120 plays)
2. **Hot Streaks:** 3+ consecutive made field goals
3. ~~**Momentum Shifts:**~~ Removed (redundant with scoring runs)

### Status: ✅ Confirmed

---

### Momentum Shift: Removed
**Date:** December 11, 2024  
**Decision:** Remove "momentum shift" pattern type

### Context
Initially had three pattern types:
1. Scoring runs
2. Hot streaks
3. Momentum shifts (lead changes)

### Problem
"Momentum shift" was just detecting lead changes (41-42, 42-44), which isn't meaningful. True momentum shifts ARE scoring runs.

### Decision
Remove momentum shift detection. Scoring runs already capture this.

### Example
Iowa down 35-30 → Goes on 12-2 run → Now up 42-37
- This IS a momentum shift
- Already detected as "Iowa 12-2 run"
- No need for separate pattern type

### Status: ✅ Confirmed

---

## AI Integration Decisions

### AI Model: Claude via Bedrock
**Date:** December 11, 2024  
**Decision:** Use AWS Bedrock (Claude 3 Sonnet)

### Context
Could use:
- OpenAI API (GPT-4)
- AWS Bedrock (Claude)
- Local model (Ollama)

### Decision: AWS Bedrock (Claude)

### Rationale
1. **AWS-native:** Integrates seamlessly with Lambda
2. **No API keys:** IAM roles handle auth
3. **Cost:** Similar to OpenAI
4. **Quality:** Claude excels at structured output
5. **Compliance:** Data stays in AWS

### Use Cases
1. **Game summaries:** Post-game analysis (200 words)
2. **Player insights:** Season efficiency analysis
3. **Pattern enrichment:** Add context to detected patterns

### Status: ✅ Confirmed

---

### AI Feature Scope
**Date:** December 11, 2024  
**Decision:** AI for insights, not predictions

### Context
Could build:
- Win probability predictor
- Score predictions
- Player performance predictions

### Decision: Insights only (no predictions)

### Rationale
1. **Explainability:** Insights are descriptive, easier to validate
2. **No training data:** Predictions need lots of historical data
3. **Better storytelling:** "AI found Iowa went on 20-4 run" beats "58% win probability"
4. **Scope:** Focus on making insights great, not predictions adequate

### Status: ✅ Confirmed

---

## Architecture Decisions

### Data Flow: Offline vs Real-Time
**Date:** December 11, 2024  
**Decision:** Offline analysis (historical), with replay simulation

### Two Modes

**Mode 1: Offline Bulk Analysis** (Primary)
```
1. Download all games from ESPN
2. Replay → Store in DynamoDB
3. Analyze patterns → Store results
4. Frontend queries stored data
```

**Mode 2: Interactive Replay** (Secondary)
```
User clicks "Replay Game"
  ↓
Frontend queries all plays from DynamoDB
  ↓
Displays in sequence with timing
  ↓
Shows patterns at their timestamps
```

### Rationale
1. **Always demo-able:** Data always ready
2. **Fast queries:** Pre-computed results
3. **No real-time complexity:** Simpler architecture
4. **Better UX:** Instant page loads

### Future Enhancement
Can add real-time EventBridge later for live games.

### Status: ✅ Confirmed

---

### Project Structure: Monorepo
**Date:** December 11, 2024  
**Decision:** Monorepo with separate frontend/backend folders

### Structure
```
courtvision-ai/
├── frontend/    # React app
├── backend/     # Lambda functions  
├── scripts/     # Analysis scripts
└── docs/        # Documentation
```

### Rationale
1. **Single repo:** Easier to manage
2. **Clear separation:** Each folder has distinct purpose
3. **Independent deployment:** Frontend/backend deploy separately
4. **Industry standard:** Common for full-stack projects

### Status: ✅ Confirmed

---

## Data Source Decisions

### ESPN Hidden API
**Date:** December 11, 2024  
**Decision:** Use ESPN's undocumented API

### Context
Could get data from:
- Official NCAA API (limited, hard to access)
- ESPN's hidden API (reverse-engineered)
- Manual data entry (terrible idea)
- Web scraping (fragile)

### Decision: ESPN Hidden API

### Endpoints
```
Team Schedule:
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/teams/2294/schedule

Game Summary (play-by-play):
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={gameId}
```

### Rationale
1. **Comprehensive:** Play-by-play, stats, shot locations
2. **Reliable:** ESPN's production API
3. **Free:** No authentication required
4. **Well-structured:** JSON format

### Risks
- API could change without notice
- No official support
- Rate limiting possible

### Mitigation
- Cache all data in S3
- Can re-fetch if API changes
- Be respectful with request rate (1-2 second delays)

### Status: ✅ Confirmed

---

### Iowa Team ID: 2294
**Date:** December 11, 2024  
**Confirmed:** Iowa Hawkeyes Women's Basketball team ID is `2294`

### Status: ✅ Confirmed

---

## Feature Prioritization

### MVP Features (Must Have)
**Date:** December 11, 2024

1. ✅ Season game list
2. ✅ Individual game view with patterns
3. ✅ Player box scores
4. ✅ Interactive game replay
5. ✅ Player season dashboard
6. ✅ Shot charts
7. 🚧 AI game summaries

### Post-MVP Features (Nice to Have)

1. **Player Comparison**
   - Head-to-head stats
   - Shot chart overlays

2. **Trend Detection**
   - Improving/declining performance
   - Hot/cold streaks over multiple games

3. **Opponent Analysis**
   - How Iowa performs vs specific teams
   - Common patterns vs opponent styles

4. **Export Features**
   - Download stats as CSV
   - Generate PDF reports

5. **Live Game Mode**
   - EventBridge for real-time games
   - Only in-season (Nov-April)

### Status: MVP prioritized

---

## Bug Fixes & Learnings

### ESPN Data Quirks
**Date:** December 11, 2024

**Issue:** ESPN's `scoreValue` field is confusing

**Learning:**
- `scoreValue` = potential points (2 for layup attempt, 3 for three attempt)
- `scoringPlay` boolean = whether shot was actually made
- Must check `scoringPlay`, not `scoreValue` for actual scoring

**Fix:** Changed detection logic to trust `scoringPlay` flag

### Status: ✅ Fixed

---

### Free Throw Detection
**Date:** December 11, 2024

**Issue:** Free throws counted in "hot streak" (consecutive field goals)

**Problem:** Action was `'madefreethrow'` (no space/underscore)

**Fix:** Changed detection from `'free_throw' not in action` to `'free' in action.lower()`

### Status: ✅ Fixed

---

### Point Totals Mismatch
**Date:** December 11, 2024

**Issue:** Replay showed 161-153 score, actual was 79-36

**Root cause:** Counted missed shots as scoring because `scoreValue > 0`

**Fix:** Changed to only count when `scoringPlay == True`

### Status: ✅ Fixed

---

## Cost Optimization Decisions

### DynamoDB: On-Demand vs Provisioned
**Decision:** On-demand capacity

**Rationale:**
- Unpredictable query patterns during development
- Low volume (< 1000 requests/day)
- On-demand cheaper at this scale

**When to switch:** If queries exceed 10K/day consistently

### Status: ✅ On-demand

---

### Kinesis: 1 Shard
**Decision:** Single shard sufficient

**Rationale:**
- Processing one game at a time
- ~500 plays per game
- 1 shard handles 1000 records/second

**When to scale:** If doing real-time with multiple simultaneous games

### Status: ✅ 1 shard

---

### Lambda Memory: Right-sized
**Decision:** 
- Ingestion: 256MB
- Processing: 512MB
- API: 256MB

**Rationale:**
- Testing showed these sizes sufficient
- Can increase if cold starts too slow
- Cost scales with memory × duration

### Status: ✅ Right-sized

---

## Documentation Decisions

### Decision Log (This File)
**Date:** December 11, 2024  
**Decision:** Maintain this decisions log

**Rationale:**
1. **Interview prep:** Can explain every choice
2. **Context for new chats:** Claude understands reasoning
3. **Learning record:** Document what worked/didn't
4. **Professional practice:** Industry standard

### Status: ✅ Maintained

---

## Future Decisions to Make

### Questions for Later

1. **Add 2023-24 season?**
   - Would need to handle Caitlin Clark separately (she graduated)
   - More data for trends
   - Decision: After MVP working

2. **Add opponent comparison?**
   - "Iowa vs Michigan State: Last 5 games"
   - Requires more complex queries
   - Decision: Post-MVP

3. **Enable live games?**
   - EventBridge schedule during season
   - Real-time updates via WebSocket
   - Decision: After historical analysis perfect

4. **Multiple teams?**
   - Add other Big Ten teams
   - Comparison features
   - Decision: Way post-MVP

---

## Interview Preparation

### Key Talking Points

**"Why Iowa only?"**
> "I chose to focus on Iowa because depth of insight is more valuable than breadth of coverage. By analyzing every Iowa game, I can track player performance over time, identify season-long trends, and provide contextual insights that wouldn't be possible with surface-level tracking of many teams. This also makes the project always demo-able, unlike a live tracker dependent on game schedules."

**"Why not use Next.js?"**
> "I chose React over Next.js because this is a client-side data visualization tool deployed on AWS serverless architecture. I wanted to showcase my AWS skills (S3, CloudFront, API Gateway, Lambda, DynamoDB, Kinesis, Bedrock) rather than abstract them behind a framework. Next.js's SSR capabilities aren't needed for a dashboard that queries pre-analyzed data."

**"Why DynamoDB over RDS?"**
> "DynamoDB's single-table design is perfect for this use case. I have well-defined access patterns (get game, list player stats, query patterns), auto-scaling, and pay-per-request pricing. The flexibility to store different entity types in one table (games, plays, patterns, player stats) with consistent query performance made it ideal. Plus, it's fully serverless with zero database maintenance."

**"How do you detect patterns?"**
> "I use rule-based algorithms with multiple window sizes (25, 50, 75, 120 plays) to catch both short bursts and quarter-long dominance. For example, a 25-play window catches an 8-0 run, while a 120-play window catches sustained dominance like a 20-8 quarter. These are deterministic and explainable, which is critical for sports analytics. I then use Claude via Bedrock to enrich these patterns with contextual analysis."

**"What was the hardest bug?"**
> "ESPN's data structure was tricky. Their `scoreValue` field represents potential points (2 or 3), not actual points scored. I was initially using this to detect scoring, which gave me inflated scores. The real indicator is the `scoringPlay` boolean. This taught me to never trust field names at face value—always validate with actual data."

**"How would you scale this?"**
> "The architecture is already designed to scale. DynamoDB and Lambda scale automatically. The bottleneck would be the Kinesis stream, which I'd scale by adding shards. For global distribution, CloudFront already handles CDN. The main optimization would be aggressive caching—since historical data doesn't change, I could cache API responses for 24 hours and reduce Lambda invocations by 90%."

---

## Conclusion

This decision log captures the "why" behind every major choice. Update it as you make new decisions.

**For your next chat with Claude:**
Upload this file along with the blueprint and timeline so Claude understands your reasoning.

**Last Updated:** December 11, 2024