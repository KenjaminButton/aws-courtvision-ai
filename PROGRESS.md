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

## CRITICAL: AWS Region Permanent Fix

**Issue:** Region keeps defaulting to us-west-2 despite wanting us-east-1

**Quick Fix (run these now):**
```bash
# 1. Set CLI default region
aws configure set region us-east-1 --profile courtvision-dev

# 2. Verify it's set
aws configure get region --profile courtvision-dev  # Should show: us-east-1

# 3. Always add --region flag to AWS CLI commands
aws lambda invoke --region us-east-1 --profile courtvision-dev ...
```

**CDK Fix:** Edit `bin/courtvision-ai.ts`, add explicit region:
```typescript
new CourtVisionIngestionStack(app, 'CourtVisionIngestionStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1'  // ← ADD THIS
  }
});
```

---