#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { IngestionStack } from '../lib/stacks/ingestion-stack';
import { ProcessingStack } from '../lib/stacks/processing-stack';

const app = new cdk.App();

// Deploy Ingestion Stack (contains DynamoDB, S3, Kinesis, Ingestion Lambda)
const ingestionStack = new IngestionStack(app, 'CourtVisionIngestionStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// Deploy Processing Stack (contains Processing Lambda with Kinesis trigger)
const processingStack = new ProcessingStack(app, 'CourtVisionProcessingStack', {
  playStream: ingestionStack.playStream,
  gamesTable: ingestionStack.gamesTable,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// Processing stack depends on Ingestion stack
processingStack.addDependency(ingestionStack);