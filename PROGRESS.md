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