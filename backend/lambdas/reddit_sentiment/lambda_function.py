import json
import boto3
import os
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
from decimal import Decimal

def convert_decimals(obj):
    """Convert DynamoDB Decimals to Python int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    return obj


TABLE_NAME = os.environ.get('TABLE_NAME', 'courtvision-games')
REGION = os.environ.get('REGION', 'us-east-1')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
bedrock = boto3.client('bedrock-runtime', region_name=REGION)

# Iowa Hawkeyes Roster 2025-26
ROSTER_CONTEXT = """IOWA HAWKEYES ROSTER (2025-26):
- Head Coach: Jan Jensen
- Hannah Stuelke: Senior, Forward
- Taylor McCabe: Senior, Guard  
- Jada Gyamfi: Senior, Forward
- Kylie Feuerbach: Graduate Student, Guard
- Kennise Johnson: Junior, Guard
- Ava Heiden: Sophomore, Center
- Chazadi "Chit Chat" Wright: Sophomore, Guard (NICKNAME: "Chit Chat" or "Chit-Chat")
- Emely Rodriguez: Sophomore, Guard
- Teagan Mallegni: Sophomore, Guard
- Taylor Stremlow: Sophomore, Guard
- Callie Levin: Sophomore, Guard
- Layla Hays: Freshman, Center
- Addie Deal: Freshman, Guard
- Journey Houston: Freshman, Forward

IMPORTANT: 
- "Chit Chat" or "Chit-Chat" refers to Chazadi Wright, NOT Caitlin Clark
- Caitlin Clark graduated in 2024 and is NOT on this team
- Only reference players from the roster above"""


def get_cached_sentiment(game_id: str) -> dict | None:
    """Check if we have cached sentiment for this game."""
    try:
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'REDDIT_SENTIMENT'}
        )
        if 'Item' in response:
            return response['Item']
    except Exception as e:
        print(f"Error checking cache: {e}")
    return None


def get_reddit_url(game_id: str) -> str | None:
    """Get Reddit thread URL from game metadata."""
    try:
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
        )
        if 'Item' in response:
            return response['Item'].get('reddit_thread_url')
    except Exception as e:
        print(f"Error getting reddit URL: {e}")
    return None


def get_stored_comments(game_id: str) -> list[dict] | None:
    """Get pre-stored Reddit comments from DynamoDB."""
    try:
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'REDDIT_COMMENTS'}
        )
        if 'Item' in response:
            return response['Item'].get('comments', [])
    except Exception as e:
        print(f"Error getting stored comments: {e}")
    return None


def analyze_sentiment(comments: list[dict]) -> dict:
    """Send comments to Haiku for sentiment analysis."""
    
    comments_text = "\n\n".join([
        f"[Score: {c['score']}] {c['body']}"
        for c in comments
    ])
    
    prompt = f"""You are analyzing fan reactions from a Reddit game thread for an Iowa Hawkeyes women's basketball game (2025-26 season).

CRITICAL CONTEXT - {ROSTER_CONTEXT}

---

Here are the top comments from the game thread (sorted by upvotes):

{comments_text}

---

Analyze the overall fan sentiment and provide your analysis in this exact JSON format:

{{
  "score": <number 1-10, where 1=furious, 5=mixed, 10=ecstatic>,
  "label": "<one of: Ecstatic, Happy, Satisfied, Mixed, Disappointed, Frustrated, Upset>",
  "summary": "<3-5 sentence summary of the overall fan mood and reaction to the game>",
  "themes": [
    "<key theme 1>",
    "<key theme 2>",
    "<key theme 3>"
  ],
  "notable_quotes": [
    {{"text": "<actual quote from comments>", "context": "<brief context>"}},
    {{"text": "<actual quote from comments>", "context": "<brief context>"}}
  ]
}}

RULES:
1. The "notable_quotes" must be REAL quotes from the comments - do not invent them
2. Only reference players from the ROSTER above
3. "Chit Chat" = Chazadi Wright (sophomore guard), never Caitlin Clark
4. Keep summary focused on Iowa fan perspective
5. Identify 3-5 main themes being discussed
6. IMPORTANT: In your JSON response, escape any double quotes inside strings with backslash (\\")

Respond with ONLY the JSON, no other text."""

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    result = json.loads(response['body'].read())
    response_text = result['content'][0]['text']
    
    # Fix common unescaped quote issues
    response_text = response_text.replace('Chazadi "Chit Chat" Wright', 'Chazadi \\"Chit Chat\\" Wright')
    response_text = response_text.replace('Chazadi "Chit-Chat" Wright', 'Chazadi \\"Chit-Chat\\" Wright')
    
    return json.loads(response_text)


def save_sentiment(game_id: str, sentiment: dict, comment_count: int):
    """Cache the sentiment analysis in DynamoDB."""
    table.put_item(Item={
        'pk': f'GAME#{game_id}',
        'sk': 'REDDIT_SENTIMENT',
        'game_id': game_id,
        'score': sentiment['score'],
        'label': sentiment['label'],
        'summary': sentiment['summary'],
        'themes': sentiment['themes'],
        'notable_quotes': sentiment['notable_quotes'],
        'comment_count': comment_count,
        'analyzed_at': datetime.utcnow().isoformat() + 'Z',
        'model': 'claude-3-haiku'
    })


def handler(event, context):
    """Lambda handler for GET /games/{gameId}/sentiment"""
    
    # Get game ID from path
    game_id = event.get('pathParameters', {}).get('gameId')
    if not game_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing gameId'})
        }
    
    # Check cache first
    cached = get_cached_sentiment(game_id)
    if cached:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(convert_decimals({
                'score': cached['score'],
                'label': cached['label'],
                'summary': cached['summary'],
                'themes': cached['themes'],
                'notable_quotes': cached['notable_quotes'],
                'comment_count': cached.get('comment_count', 0),
                'analyzed_at': cached['analyzed_at'],
                'cached': True
            }))
        }
    
    # Get stored comments from DynamoDB
    comments = get_stored_comments(game_id)
    
    if not comments:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'No Reddit comments stored for this game. Run add_game_media.py --reddit first.'})
        }
    
    # Analyze sentiment
    try:
        sentiment = analyze_sentiment(comments)
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Failed to analyze sentiment'})
        }
    
    # Cache the result
    save_sentiment(game_id, sentiment, len(comments))
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'score': sentiment['score'],
            'label': sentiment['label'],
            'summary': sentiment['summary'],
            'themes': sentiment['themes'],
            'notable_quotes': sentiment['notable_quotes'],
            'comment_count': len(comments),
            'analyzed_at': datetime.utcnow().isoformat() + 'Z',
            'cached': False
        })
    }