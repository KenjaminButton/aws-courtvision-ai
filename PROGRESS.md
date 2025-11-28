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