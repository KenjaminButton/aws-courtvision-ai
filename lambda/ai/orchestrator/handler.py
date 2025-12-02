import json
import os
import boto3
from datetime import datetime

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)
lambda_client = boto3.client('lambda')

def invoke_win_prob_lambda(game_id):
    """
    Invoke Win Probability Lambda for a game
    
    Args:
        game_id: Game identifier (PK)
    """
    try:
        payload = {
            'game_id': game_id
        }
        
        response = lambda_client.invoke(
            FunctionName='courtvision-ai-winprob',
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        print(f"✅ Invoked Win Probability Lambda for {game_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error invoking Win Prob Lambda: {str(e)}")
        return False


def should_trigger_ai(record):
    """
    Determine if a DynamoDB change warrants AI analysis
    
    Args:
        record: DynamoDB Stream record (NewImage format)
    
    Returns:
        dict with 'should_analyze' (bool) and 'trigger_types' (list)
    """
    try:
        # Extract SK (Sort Key) from the record
        sk = record.get('SK', {}).get('S', '')
        
        trigger_types = []
        
        # Trigger on scoring plays
        if sk.startswith('PLAY#'):
            scoring_play = record.get('scoringPlay', {}).get('BOOL', False)
            if scoring_play:
                trigger_types.append('scoring_play')
                print(f"✅ Scoring play detected: {sk}")
        
        # Trigger on score updates (potential for win probability)
        if sk == 'SCORE#CURRENT':
            trigger_types.append('score_update')
            print(f"✅ Score update detected")
        
        # Trigger on game completion (for post-game summary)
        if sk == 'METADATA':
            status = record.get('status', {}).get('S', '')
            if status == 'final':
                trigger_types.append('game_final')
                print(f"✅ Game completed detected")
        
        return {
            'should_analyze': len(trigger_types) > 0,
            'trigger_types': trigger_types
        }
        
    except Exception as e:
        print(f"❌ Error in should_trigger_ai: {str(e)}")
        return {
            'should_analyze': False,
            'trigger_types': []
        }


def handler(event, context):
    """
    AI Orchestrator Lambda - triggered by DynamoDB Streams
    
    Analyzes changes to determine if AI processing is needed,
    then routes to appropriate AI Lambda functions.
    """
    try:
        print("🤖 AI Orchestrator Lambda started")
        print(f"Received {len(event['Records'])} DynamoDB Stream records")
        
        analyzed_count = 0
        
        for record in event['Records']:
            # Only process INSERT and MODIFY events
            if record['eventName'] not in ['INSERT', 'MODIFY']:
                continue
            
            # Get the new item data
            new_image = record['dynamodb'].get('NewImage', {})
            
            # Check if this change needs AI analysis
            analysis = should_trigger_ai(new_image)
            
            if analysis['should_analyze']:
                print(f"📊 Trigger types: {analysis['trigger_types']}")
                
                # Route to appropriate AI Lambda functions
                for trigger_type in analysis['trigger_types']:
                    if trigger_type == 'scoring_play':
                        print("  → Invoking: AI Commentary Lambda (TODO)")
                        # Invoke Win Probability on scoring plays
                        invoke_win_prob_lambda(new_image.get('PK', {}).get('S', ''))
                    elif trigger_type == 'score_update':
                        print("  → Invoking: Win Probability Lambda")
                        invoke_win_prob_lambda(new_image.get('PK', {}).get('S', ''))
                    elif trigger_type == 'game_final':
                        print("  → Invoking: Post-Game Summary Lambda (TODO)")
                
                analyzed_count += 1
        
        print(f"✅ Orchestrator processed {analyzed_count} AI-worthy events")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {analyzed_count} events for AI analysis')
        }
        
    except Exception as e:
        print(f"❌ Error in AI Orchestrator: {str(e)}")
        raise