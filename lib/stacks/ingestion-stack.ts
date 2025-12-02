import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as kinesis from 'aws-cdk-lib/aws-kinesis';

export class IngestionStack extends cdk.Stack {
  public readonly gamesTable: dynamodb.Table;
    public readonly recordingsBucket: s3.Bucket;
    public readonly frontendBucket: s3.Bucket;
    public readonly playStream: kinesis.Stream;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.gamesTable = new dynamodb.Table(this, 'GamesTable', {
      tableName: 'courtvision-games',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI1 - For WebSocket connections by gameId (EXISTING - keep it!)
    this.gamesTable.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // GSI2 - For ESPN Game ID lookups (NEW - adding it!)
    this.gamesTable.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'espnGameId', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // S3 bucket for game recordings
    this.recordingsBucket = new s3.Bucket(this, 'RecordingsBucket', {
      bucketName: `courtvision-recordings-${cdk.Stack.of(this).account}`,
      versioned: true, // Enable versioning
      lifecycleRules: [
        {
          id: 'MoveToIA',
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
          ],
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN, // Don't delete bucket if stack deleted
      autoDeleteObjects: false,
    });

    // S3 bucket for frontend
    this.frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `courtvision-frontend-${cdk.Stack.of(this).account}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html', // For React Router

      removalPolicy: cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: false,
    });

    // Kinesis Data Stream for buffering play-by-play events
    this.playStream = new kinesis.Stream(this, 'PlayStream', {
      streamName: 'courtvision-plays',
      shardCount: 1,
      retentionPeriod: cdk.Duration.hours(24), // Keep data for 24 hours
    });

    // Lambda function for data ingestion
    const ingestionLambda = new lambda.Function(this, 'IngestionFunction', {
      functionName: 'courtvision-ingest',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/ingestion/lambda-package.zip'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        DATA_SOURCE: 'live',
        DYNAMODB_TABLE: this.gamesTable.tableName,
        S3_BUCKET: this.recordingsBucket.bucketName,
        SCHEDULE_ENABLED: 'false',
        KINESIS_STREAM_NAME: this.playStream.streamName,
      },
    });

    // Grant Lambda permissions to DynamoDB table
    this.gamesTable.grantReadWriteData(ingestionLambda);
    
    // Grant Lambda permissions to S3 bucket
    this.recordingsBucket.grantReadWrite(ingestionLambda);

    // Grant Lambda permissions to write to Kinesis
    this.playStream.grantWrite(ingestionLambda);

    // EventBridge rule to trigger Lambda every minute
    // Only enabled when SCHEDULE_ENABLED is set to 'true'
    const ingestionSchedule = new events.Rule(this, 'IngestionSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
      description: 'Trigger ingestion Lambda every minute during games',
      enabled: false, // Start disabled - enable manually when testing
    });

    // Add Lambda as target
    ingestionSchedule.addTarget(new targets.LambdaFunction(ingestionLambda));

    // Outputs for the buckets
    new cdk.CfnOutput(this, 'RecordingsBucketName', {
      value: this.recordingsBucket.bucketName,
      description: 'S3 bucket for game recordings',
    });

    new cdk.CfnOutput(this, 'FrontendBucketName', {
      value: this.frontendBucket.bucketName,
      description: 'S3 bucket for frontend',
    });

    new cdk.CfnOutput(this, 'FrontendBucketWebsiteURL', {
      value: this.frontendBucket.bucketWebsiteUrl,
      description: 'Frontend website URL',
    });


    // Output the table name
    new cdk.CfnOutput(this, 'GamesTableName', {
      value: this.gamesTable.tableName,
      description: 'DynamoDB table for game data',
    });

    new cdk.CfnOutput(this, 'GamesTableArn', {
      value: this.gamesTable.tableArn,
      description: 'ARN of the games table',
    });

    new cdk.CfnOutput(this, 'PlayStreamName', {
      value: this.playStream.streamName,
      description: 'Kinesis stream for play-by-play events',
    });

    new cdk.CfnOutput(this, 'PlayStreamArn', {
      value: this.playStream.streamArn,
      description: 'ARN of the play stream',
    });
    
  }
}