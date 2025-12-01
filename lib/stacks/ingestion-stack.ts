import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class IngestionStack extends cdk.Stack {
  public readonly gamesTable: dynamodb.Table;
    public readonly recordingsBucket: s3.Bucket;
    public readonly frontendBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Main DynamoDB table for all game data
    this.gamesTable = new dynamodb.Table(this, 'GamesTable', {
      tableName: 'courtvision-games',
      partitionKey: {
        name: 'PK',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'SK',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // On-demand pricing
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES, // Enable streams for AI triggers
      removalPolicy: cdk.RemovalPolicy.RETAIN, // Don't delete table if stack is deleted
    });

    // Add Global Secondary Index for date-based queries
    this.gamesTable.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: {
        name: 'GSI1PK',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'GSI1SK',
        type: dynamodb.AttributeType.STRING,
      },
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
      },
    });

    // Grant Lambda permissions to DynamoDB table
    this.gamesTable.grantReadWriteData(ingestionLambda);
    
    // Grant Lambda permissions to S3 bucket
    this.recordingsBucket.grantReadWrite(ingestionLambda);

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
  }
}