import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
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

    // REST API Lambda - for game lookups by ESPN ID
    const apiLambda = new lambda.Function(this, 'ApiHandler', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('lambda/api'),
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
      environment: {
        DYNAMODB_TABLE: props.gamesTable.tableName,
      },
    });

    // Grant API Lambda read access to DynamoDB (for GSI2 queries)
    props.gamesTable.grantReadData(apiLambda);

    // REST API Gateway
    const restApi = new apigateway.RestApi(this, 'GameApi', {
      restApiName: 'CourtVision Game API',
      description: 'REST API for game data lookups',
      deploy: true,  
      deployOptions: {
        stageName: 'prod',
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // Add /game resource
    const gameResource = restApi.root.addResource('game');
    
    // Add /game/{espnGameId} resource
    const gameIdResource = gameResource.addResource('{espnGameId}');
    gameIdResource.addMethod('GET', new apigateway.LambdaIntegration(apiLambda));

    // Add /game/{espnGameId}/win-probability resource
    const winProbResource = gameIdResource.addResource('win-probability');
    winProbResource.addMethod('GET', new apigateway.LambdaIntegration(apiLambda));

    // Add /games resource (for today's games list)
    const gamesResource = restApi.root.addResource('games');
    gamesResource.addMethod('GET', new apigateway.LambdaIntegration(apiLambda));

    // Outputs
    new cdk.CfnOutput(this, 'PushLambdaName', {
      value: pushLambda.functionName,
      description: 'Push Lambda function name',
    });

    new cdk.CfnOutput(this, 'WebSocketURL', {
      value: this.webSocketStage.url,
      description: 'WebSocket API endpoint',
    });

    new cdk.CfnOutput(this, 'WebSocketApiId', {
      value: this.webSocketApi.apiId,
      description: 'WebSocket API ID',
    });

    new cdk.CfnOutput(this, 'RestApiUrl', {
      value: restApi.url,
      description: 'REST API endpoint',
    });
  }
}

