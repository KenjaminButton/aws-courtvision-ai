

1. Check Commentary logs when games start
aws logs tail /aws/lambda/CourtVisionAiStack-CommentaryLambda6E85C950-UOXz9T5ecwrQ --follow

2. Look for natural commentary without errors

#### Start Virtual Environment:
```
source .venv/bin/activate
```


### Frontend Tree for CLI without unnecessary files
```
tree -L 3 frontend -I 'node_modules|build|dist|coverage|.cache|*.log'
```

#### CDK Deploy no changes
```
rm -rf cdk.out
cdk deploy --all


rm -rf cdk.out
cdk deploy --all
```

### Manual Lambda Code Update:

Manual Lambda Code Update
Step 1: Package the Lambda code
```
bashcd lambda/ingestion
zip -r /tmp/ingestion.zip .
cd ../..
```
Step 2: Update the Lambda function directly
```
bashaws lambda update-function-code \
  --function-name courtvision-ingest \
  --zip-file fileb:///tmp/ingestion.zip \
  --region us-east-1
```



### Manual Control Commands

** Disable Eventbridge Rule**
```
aws events disable-rule \
  --name CourtVisionIngestionStack-IngestionSchedule30858612-5Stq77YxdH7A \
  --region us-east-1
```

**Manually Fetch Updates**
```
aws lambda invoke --function-name courtvision-ingest --region us-east-1 output.json
```


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