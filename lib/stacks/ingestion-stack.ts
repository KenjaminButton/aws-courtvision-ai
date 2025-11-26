import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class IngestionStack extends cdk.Stack {
  public readonly gamesTable: dynamodb.Table;

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