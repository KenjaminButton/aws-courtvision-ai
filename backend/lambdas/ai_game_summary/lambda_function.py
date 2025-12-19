"""
CourtVision AI - Game Summary Generator
Uses Claude Sonnet to generate a sports journalism narrative from game data.
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# Clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'courtvision-games'))
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('REGION', 'us-east-1'))

# Using Sonnet for better accuracy (Haiku hallucinates too much)
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return super().default(obj)


def get_game_data(game_id: str) -> dict:
    """Fetch game metadata from DynamoDB."""
    response = table.get_item(
        Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
    )
    return response.get('Item')


def get_patterns(game_id: str) -> list:
    """Fetch patterns for the game."""
    response = table.query(
        KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#')
    )
    return response.get('Items', [])


def build_prompt(game: dict, patterns: list, game_context: str = None) -> str:
    """Build the prompt for Claude Sonnet."""
    iowa = game.get('iowa', {})
    opponent = game.get('opponent', {})
    
    iowa_score = iowa.get('score', '0')
    opp_score = opponent.get('score', '0')
    iowa_won = int(iowa_score) > int(opp_score)
    
    # Format patterns
    pattern_text = ""
    for p in patterns:
        team_label = p.get('team', 'Unknown')
        if p.get('pattern_type') == 'scoring_run':
            pattern_text += f"- ({team_label}) {p.get('points_for')}-{p.get('points_against')} scoring run in Q{p.get('period')}\n"
        elif p.get('pattern_type') == 'hot_streak':
            pattern_text += f"- ({team_label}) {p.get('player_name')} made {p.get('consecutive_makes')} consecutive field goals\n"
    
    # Get top performers from player_stats with FG stats
    top_performers = ""
    iowa_players = game.get('player_stats', {}).get('iowa', [])
    if iowa_players:
        sorted_players = sorted(iowa_players, key=lambda x: int(x.get('points', 0)), reverse=True)[:3]
        for p in sorted_players:
            fg = p.get('field_goals', '?-?')
            top_performers += f"- {p.get('player_name', 'Unknown')}: {p.get('points', 0)} pts ({fg} FG), {p.get('rebounds', 0)} reb, {p.get('assists', 0)} ast\n"
    
    # Use provided context or default
    if not game_context:
        game_context = "No additional context provided."
    
    prompt = f"""You are a sports journalist writing a game recap for Iowa Hawkeyes women's basketball.

IOWA HAWKEYES FACTS (2025-26 season):
- Head Coach: Jan Jensen (second year as head coach)
- Arena: Carver-Hawkeye Arena
- Conference: Big Ten
- Current schedule: Early season (December) - non-conference play

ROSTER:
- Hannah Stuelke: Senior, Forward
- Taylor McCabe: Senior, Guard
- Jada Gyamfi: Senior, Forward
- Kylie Feuerbach: Graduate Student, Guard
- Kennise Johnson: Junior, Guard
- Ava Heiden: Sophomore, Center
- Chazadi "Chit Chat" Wright: Sophomore, Guard
- Emely Rodriguez: Sophomore, Guard
- Teagan Mallegni: Sophomore, Guard
- Taylor Stremlow: Sophomore, Guard
- Callie Levin: Sophomore, Guard
- Layla Hays: Freshman, Center
- Addie Deal: Freshman, Guard
- Journey Houston: Freshman, Forward

IMPORTANT RULES:
- Use class years and positions from ROSTER above - never invent them
- ALWAYS use full team names: "UConn Huskies" not "Huskies", "Iowa Hawkeyes" not "Hawkeyes"
- Only the 5 players listed under "STARTERS THIS GAME:" are starters
- ANY player not listed under "STARTERS THIS GAME:" is a bench player
- NEVER refer to starters as bench players or say they got "extended minutes"
- ONLY use facts explicitly provided - do not add any details not given
- NEVER invent quotes from coaches, players, or staff - no quotes allowed
- Do NOT invent statistics not explicitly provided
- Do NOT reference team history, past seasons, or championships
- Focus ONLY on this specific game and the facts provided

GAME CONTEXT:
{game_context}

GAME RESULT:
Iowa {iowa_score} - {opponent.get('name', 'Opponent')} {opp_score}
Result: Iowa {'Won' if iowa_won else 'Lost'}
Location: {game.get('venue', {}).get('name', 'Unknown')}
Date: {game.get('date', '')[:10]}

TOP IOWA PERFORMERS:
{top_performers if top_performers else 'No stats available'}

KEY GAME PATTERNS:
{pattern_text if pattern_text else 'No notable patterns detected'}

Write a 400-500 word game recap. You MUST:
1. Incorporate the storylines from GAME CONTEXT
2. Mention top performers with their exact stats
3. Reference scoring runs and hot streaks
4. Use correct class years and positions from ROSTER"""

    return prompt


def generate_summary(game_id: str) -> dict:
    """Generate AI summary for a game."""
    # Check if summary already exists
    existing = table.get_item(
        Key={'pk': f'GAME#{game_id}', 'sk': 'AI_SUMMARY'}
    )
    if existing.get('Item'):
        return {
            'summary': existing['Item'].get('summary'),
            'generated_at': existing['Item'].get('generated_at'),
            'cached': True
        }
    
    # Fetch game data
    game = get_game_data(game_id)
    if not game:
        return {'error': 'Game not found'}
    
    # Get game context if stored
    game_context = game.get('game_context', None)
    
    patterns = get_patterns(game_id)
    
    # Build prompt and call Sonnet
    prompt = build_prompt(game, patterns, game_context)
    
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    summary_text = result['content'][0]['text']
    
    # Store in DynamoDB for caching
    from datetime import datetime
    generated_at = datetime.utcnow().isoformat() + 'Z'
    
    table.put_item(Item={
        'pk': f'GAME#{game_id}',
        'sk': 'AI_SUMMARY',
        'game_id': game_id,
        'summary': summary_text,
        'generated_at': generated_at,
        'model': MODEL_ID
    })
    
    return {
        'summary': summary_text,
        'generated_at': generated_at,
        'cached': False
    }


def handler(event, context):
    """Lambda handler."""
    try:
        game_id = event.get('pathParameters', {}).get('gameId')
        
        if not game_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Game ID required'})
            }
        
        result = generate_summary(game_id)
        
        if 'error' in result:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result)
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }