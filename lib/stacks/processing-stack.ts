import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as kinesis from 'aws-cdk-lib/aws-kinesis';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { KinesisEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { StartingPosition } from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

interface ProcessingStackProps extends cdk.StackProps {
  playStream: kinesis.IStream;
  gamesTable: dynamodb.ITable;
}

export class ProcessingStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ProcessingStackProps) {
    super(scope, id, props);

    // Processing Lambda function
    const processingLambda = new lambda.Function(this, 'ProcessingFunction', {
      functionName: 'courtvision-process',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/processing'),
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
      },
    });

    // Grant Lambda permissions to DynamoDB table
    props.gamesTable.grantReadWriteData(processingLambda);

    // Add Kinesis as event source
    processingLambda.addEventSource(
      new KinesisEventSource(props.playStream, {
        startingPosition: StartingPosition.LATEST,
        batchSize: 10,
        bisectBatchOnError: true, // Retry individual records on failure
        retryAttempts: 3,
      })
    );

    // Output
    new cdk.CfnOutput(this, 'ProcessingLambdaName', {
      value: processingLambda.functionName,
      description: 'Processing Lambda function name',
    });
  }
}