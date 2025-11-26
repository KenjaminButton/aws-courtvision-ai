#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { IngestionStack } from '../lib/stacks/ingestion-stack';

const app = new cdk.App();

new IngestionStack(app, 'CourtVisionIngestionStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'CourtVision AI - Data Ingestion Stack',
});