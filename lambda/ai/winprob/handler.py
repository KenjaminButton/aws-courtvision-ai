import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Win Probability Prompt Template
WIN_PROB_PROMPT = """You are a sports analytics expert calculating win probability for a women's college basketball game.

Current Game State:
- Home Team: {home_team} (Score: {home_score})
- Away Team: {away_team} (Score: {away_score})
- Time Remaining: Quarter {quarter}, {time_remaining} remaining
- Recent Trend: {recent_trend}
- Home Team Shooting: {home_fg_pct}% FG, {home_3pt_pct}% 3PT
- Away Team Shooting: {away_fg_pct}% FG, {away_3pt_pct}% 3PT

Based on this game state, calculate the win probability for each team.

Respond in this exact JSON format:
{{
  "home_probability": <float between 0 and 1>,
  "away_probability": <float between 0 and 1>,
  "reasoning": "<2-3 sentence explanation of the key factors>"
}}

Consider: score differential, time remaining, momentum, shooting percentages, and historical comeback data. The probabilities must sum to 1.0.
"""


def get_game_context(game_id):
    """
    Fetch game state and calculate context for win probability
    
    Args:
        game_id: Game identifier (PK in DynamoDB)
    
    Returns:
        dict with game state information
    """
    try:
        # Fetch game metadata
        metadata_response = table.get_item(
            Key={'PK': game_id, 'SK': 'METADATA'}
        )
        metadata = metadata_response.get('Item', {})
        
        # Fetch current score
        score_response = table.get_item(
            Key={'PK': game_id, 'SK': 'SCORE#CURRENT'}
        )
        score = score_response.get('Item', {})
        
        # TODO: Fetch recent plays for trend analysis
        # For now, use a simple trend description
        recent_trend = "Teams trading baskets"
        
        # Build game context
        context = {
            'home_team': metadata.get('homeTeam', 'Home'),
            'away_team': metadata.get('awayTeam', 'Away'),
            'home_score': int(score.get('homeScore', 0)),
            'away_score': int(score.get('awayScore', 0)),
            'quarter': int(score.get('quarter', 1)),
            'time_remaining': score.get('gameClock', '10:00'),
            'recent_trend': recent_trend,
            'home_fg_pct': 45.0,  # TODO: Calculate from plays
            'home_3pt_pct': 35.0,  # TODO: Calculate from plays
            'away_fg_pct': 43.0,  # TODO: Calculate from plays
            'away_3pt_pct': 33.0,  # TODO: Calculate from plays
        }
        
        return context
        
    except Exception as e:
        print(f"❌ Error fetching game context: {str(e)}")
        return None


def calculate_win_probability(game_context):
    """
    Call Bedrock to calculate win probability
    
    Args:
        game_context: Dict with game state
    
    Returns:
        Dict with probabilities and reasoning
    """
    try:
        # Format prompt
        prompt = WIN_PROB_PROMPT.format(**game_context)
        
        # Bedrock request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        print("🔄 Calling Bedrock for win probability...")
        
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        assistant_message = response_body['content'][0]['text']
        
        # Parse JSON response
        result = json.loads(assistant_message)
        
        print(f"✅ Win Probability: {result['home_probability']:.1%} - {result['away_probability']:.1%}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error calculating win probability: {str(e)}")
        return None


def store_win_probability(game_id, probability_data, game_context):
    """
    Store win probability in DynamoDB
    
    Args:
        game_id: Game identifier
        probability_data: Dict with probabilities and reasoning
        game_context: Original game context
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Store as CURRENT (latest probability)
        table.put_item(Item={
            'PK': game_id,
            'SK': 'AI#WIN_PROB#CURRENT',
            'homeWinProbability': Decimal(str(probability_data['home_probability'])),
            'awayWinProbability': Decimal(str(probability_data['away_probability'])),
            'reasoning': probability_data['reasoning'],
            'homeScore': game_context['home_score'],
            'awayScore': game_context['away_score'],
            'quarter': game_context['quarter'],
            'calculatedAt': timestamp
        })
        
        # Also store historical record
        table.put_item(Item={
            'PK': game_id,
            'SK': f"AI#WIN_PROB#{timestamp}",
            'homeWinProbability': Decimal(str(probability_data['home_probability'])),
            'awayWinProbability': Decimal(str(probability_data['away_probability'])),
            'reasoning': probability_data['reasoning'],
            'homeScore': game_context['home_score'],
            'awayScore': game_context['away_score'],
            'quarter': game_context['quarter'],
            'calculatedAt': timestamp
        })
        
        print(f"✅ Stored win probability in DynamoDB")
        return True
        
    except Exception as e:
        print(f"❌ Error storing win probability: {str(e)}")
        return False


def handler(event, context):
    """
    Win Probability Lambda - calculates and stores win probability
    
    Invoked by AI Orchestrator when significant game events occur
    """
    try:
        print("📊 Win Probability Lambda started")
        
        # Extract game ID from event
        game_id = event.get('game_id')
        if not game_id:
            print("❌ No game_id in event")
            return {'statusCode': 400, 'body': 'Missing game_id'}
        
        print(f"Processing game: {game_id}")
        
        # Step 1: Gather game context
        game_context = get_game_context(game_id)
        if not game_context:
            return {'statusCode': 500, 'body': 'Failed to fetch game context'}
        
        print(f"Game: {game_context['home_team']} {game_context['home_score']} - {game_context['away_team']} {game_context['away_score']}")
        
        # Step 2: Calculate win probability
        probability_data = calculate_win_probability(game_context)
        if not probability_data:
            return {'statusCode': 500, 'body': 'Failed to calculate probability'}
        
        # Step 3: Store in DynamoDB
        store_win_probability(game_id, probability_data, game_context)
        
        # TODO Step 4: Push to WebSocket (Day 25)
        
        print("✅ Win probability calculation complete")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'home_probability': probability_data['home_probability'],
                'away_probability': probability_data['away_probability']
            })
        }
        
    except Exception as e:
        print(f"❌ Error in Win Probability Lambda: {str(e)}")
        raise