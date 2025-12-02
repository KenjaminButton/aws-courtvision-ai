import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { WebSocketLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

interface WebSocketStackProps extends cdk.StackProps {
  gamesTable: dynamodb.Table;
}

export class WebSocketStack extends cdk.Stack {
  public readonly webSocketApi: apigatewayv2.WebSocketApi;
  public readonly webSocketStage: apigatewayv2.WebSocketStage;

  constructor(scope: Construct, id: string, props: WebSocketStackProps) {
    super(scope, id, props);

    // WebSocket Lambda
    const webSocketLambda = new lambda.Function(this, 'WebSocketHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/websocket'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
      },
    });

    // Grant Lambda permission to push messages to WebSocket connections
    webSocketLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['execute-api:ManageConnections'],
      resources: [
        `arn:aws:execute-api:${this.region}:${this.account}:*/*/@connections/*`,
      ],
    }));

    // Grant DynamoDB permissions
    props.gamesTable.grantReadWriteData(webSocketLambda);

    // WebSocket API
    this.webSocketApi = new apigatewayv2.WebSocketApi(this, 'GameWebSocket', {
      connectRouteOptions: {
        integration: new WebSocketLambdaIntegration('ConnectIntegration', webSocketLambda),
      },
      disconnectRouteOptions: {
        integration: new WebSocketLambdaIntegration('DisconnectIntegration', webSocketLambda),
      },
      defaultRouteOptions: {
        integration: new WebSocketLambdaIntegration('DefaultIntegration', webSocketLambda),
      },
    });

    // WebSocket Stage (production)
    this.webSocketStage = new apigatewayv2.WebSocketStage(this, 'ProductionStage', {
      webSocketApi: this.webSocketApi,
      stageName: 'prod',
      autoDeploy: true,
    });

    // Push Lambda - sends updates to connected clients
    const pushLambda = new lambda.Function(this, 'PushHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/push'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
        WEBSOCKET_ENDPOINT: `https://${this.webSocketApi.apiId}.execute-api.${this.region}.amazonaws.com/${this.webSocketStage.stageName}`,
      },
    });

    // Grant Push Lambda permission to read DynamoDB and push to WebSocket
    props.gamesTable.grantReadData(pushLambda);
    pushLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['execute-api:ManageConnections'],
      resources: [
        `arn:aws:execute-api:${this.region}:${this.account}:${this.webSocketApi.apiId}/${this.webSocketStage.stageName}/POST/@connections/*`,
      ],
    }));

    // Add DynamoDB Streams trigger
    pushLambda.addEventSource(new DynamoEventSource(props.gamesTable, {
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 10,
      bisectBatchOnError: true,
      retryAttempts: 3,
    }));

    // Output
    new cdk.CfnOutput(this, 'PushLambdaName', {
      value: pushLambda.functionName,
      description: 'Push Lambda function name',
    });

    // Outputs
    new cdk.CfnOutput(this, 'WebSocketURL', {
      value: this.webSocketStage.url,
      description: 'WebSocket API endpoint',
    });

    new cdk.CfnOutput(this, 'WebSocketApiId', {
      value: this.webSocketApi.apiId,
      description: 'WebSocket API ID',
    });
  }
}