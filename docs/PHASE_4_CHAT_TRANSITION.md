#### Tree Command for Entire Project
```Bash
tree -L 3 -I 'node_modules|build|dist|coverage|.cache|*.log|.git|cdk.out|*.zip|__pycache__|*.pyc|.DS_Store|.venv|.env'
```

#### Manual Deploy Commands (When CDK Fails)
```Bash
# Win Probability Lambda
cd lambda/ai/winprob && zip -r /tmp/winprob.zip . && cd ../../..
aws lambda update-function-code --function-name courtvision-ai-winprob --zip-file fileb:///tmp/winprob.zip --region us-east-1

# Commentary Lambda
cd lambda/ai/commentary && zip -r /tmp/commentary.zip . && cd ../../..
aws lambda update-function-code --function-name CourtVisionAiStack-CommentaryLambda6E85C950-UOXz9T5ecwrQ --zip-file fileb:///tmp/commentary.zip --region us-east-1

# Processing Lambda
cd lambda/processing && zip -r /tmp/processing.zip . && cd ../../..
aws lambda update-function-code --function-name CourtVisionAiStack-ProcessingLambda[YOUR-HASH] --zip-file fileb:///tmp/processing.zip --region us-east-1

# Ingestion Lambda
cd lambda/ingestion && zip -r /tmp/ingestion.zip . && cd ../../..
aws lambda update-function-code --function-name courtvision-ingest --zip-file fileb:///tmp/ingestion.zip --region us-east-1
```

#### Find actual lambda names:
```bash
(.venv) kenjaminbutton@Kenjamins-MacBook-Pro 03-AWS-Courtvision-AI % aws lambda list-functions --region us-east-1 --query 'Functions[?contains(FunctionName, `CourtVision`) || contains(FunctionName, `courtvision`)].FunctionName' --output table
---------------------------------------------------------------------
|                           ListFunctions                           |
+-------------------------------------------------------------------+
|  CourtVisionWebSocketStack-WebSocketHandler47C0AA1A-fL5S5U0A8qCy  |
|  CourtVisionAiStack-CommentaryLambda6E85C950-UOXz9T5ecwrQ         |
|  courtvision-ai-winprob                                           |
|  CourtVisionWebSocketStack-ApiHandler5E7490E8-XvY36k8sqzgj        |
|  CourtVisionWebSocketStack-PushHandler50B0D49E-CpvpZnvGNmIh       |
|  courtvision-process                                              |
|  courtvision-ai-orchestrator                                      |
|  courtvision-ingest                                               |
+-------------------------------------------------------------------+
```




## Manual Deploy Commands

**Backend Lambdas (Current - Use These):**
```bash
# Find Lambda names
aws lambda list-functions --region us-east-1 --query 'Functions[?contains(FunctionName, `CourtVision`)].FunctionName' --output table

# Deploy Lambda (example)
cd lambda/ai/[lambda-name] && zip -r /tmp/[name].zip . && cd ../../..
aws lambda update-function-code --function-name [ACTUAL-NAME] --zip-file fileb:///tmp/[name].zip --region us-east-1
```

**Frontend (Development - Current):**
```bash
cd frontend
npm start
# Runs on localhost:3000
```

**Frontend (Production - Phase 6, Not Yet Implemented):**
```bash
# Will implement CloudFront distribution in Phase 6
cd frontend
npm run build
aws s3 sync build/ s3://[BUCKET-NAME] --delete
```