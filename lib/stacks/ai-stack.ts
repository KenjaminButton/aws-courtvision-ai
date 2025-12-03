import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';

interface AiStackProps extends cdk.StackProps {
  gamesTable: dynamodb.Table;
}

export class AiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: AiStackProps) {
    super(scope, id, props);

    // AI Orchestrator Lambda
    const orchestratorLambda = new lambda.Function(this, 'OrchestratorFunction', {
      functionName: 'courtvision-ai-orchestrator',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/ai/orchestrator'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
      },
    });

    // Win Probability Lambda
    const winProbLambda = new lambda.Function(this, 'WinProbFunction', {
      functionName: 'courtvision-ai-winprob',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/ai/winprob'),
      timeout: cdk.Duration.seconds(120),
      memorySize: 1024,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
      },
    });

    // Commentary Lambda
    const commentaryLambda = new lambda.Function(this, 'CommentaryLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/ai/commentary'),
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
        WEBSOCKET_API_ENDPOINT: 'https://x54f0p0ve2.execute-api.us-east-1.amazonaws.com/prod',  // ADD THIS LINE
      },
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      description: 'Generate AI commentary for scoring plays',
    });

    // Grant DynamoDB permissions
    props.gamesTable.grantReadWriteData(commentaryLambda);

    // Grant Bedrock permissions
    commentaryLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'],
    }));

    // Grant WebSocket execute permissions
    commentaryLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['execute-api:ManageConnections', 'execute-api:Invoke'],
      resources: ['arn:aws:execute-api:us-east-1:*:x54f0p0ve2/*'],
    }));

    // Grant DynamoDB read permissions
    props.gamesTable.grantReadData(orchestratorLambda);
    // Grant DynamoDB read/write permissions
    props.gamesTable.grantReadWriteData(winProbLambda);

    // Grant permission to invoke other Lambda functions (for future AI workers)
    orchestratorLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['lambda:InvokeFunction'],
      resources: [
        `arn:aws:lambda:${this.region}:${this.account}:function:courtvision-ai-*`
      ],
    }));

    // Grant Bedrock access (wildcard for cross-region inference profiles)
    winProbLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream'
      ],
      resources: [
        'arn:aws:bedrock:*::foundation-model/*',
        `arn:aws:bedrock:*:${this.account}:inference-profile/*`,
      ],
    }));

    // Add DynamoDB Streams trigger
    orchestratorLambda.addEventSource(new DynamoEventSource(props.gamesTable, {
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 10,
      bisectBatchOnError: true,
      retryAttempts: 3,
    }));

    // Trigger Commentary Lambda from DynamoDB Stream
    commentaryLambda.addEventSource(new DynamoEventSource(props.gamesTable, {
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 10,
      retryAttempts: 2,
    }));

    // Output
    new cdk.CfnOutput(this, 'OrchestratorLambdaName', {
      value: orchestratorLambda.functionName,
      description: 'AI Orchestrator Lambda function name',
    });

    new cdk.CfnOutput(this, 'WinProbLambdaName', {
      value: winProbLambda.functionName,
      description: 'Win Probability Lambda function name',
    });

  }
}