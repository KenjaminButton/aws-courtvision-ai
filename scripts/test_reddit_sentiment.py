#!/usr/bin/env python3
"""
Test script for Reddit sentiment analysis with Haiku.
Run: python3 scripts/test_reddit_sentiment.py
"""

import json
from urllib import response
import boto3
import requests

# Reddit thread URL (without .json)
REDDIT_URL = "https://www.reddit.com/r/NCAAW/comments/1pltt4k/game_thread_lindenwood_at_9_iowa_300_pm_et_on_b1g/"

def fetch_reddit_comments(reddit_url: str, max_comments: int = 150) -> list[dict]:
    """Fetch comments from Reddit JSON endpoint."""
    json_url = reddit_url.rstrip('/') + '.json'
    
    headers = {
        'User-Agent': 'CourtVisionAI/1.0 (Iowa Hawkeyes Basketball Analytics)'
    }
    
    response = requests.get(json_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    comments = []
    
    # data[1] contains the comments (data[0] is the post itself)
    top_level_comments = data[1]['data']['children']
    
    for item in top_level_comments:
        if item['kind'] != 't1':  # t1 = comment
            continue
            
        comment_data = item['data']
        body = comment_data.get('body', '')
        score = comment_data.get('score', 0)
        author = comment_data.get('author', '[deleted]')
        
        # Skip deleted/removed comments
        if body in ['[deleted]', '[removed]', '']:
            continue
        
        comments.append({
            'body': body,
            'score': score,
            'author': author,
            'is_reply': False
        })
        
        # Get first-level replies if they exist
        replies = comment_data.get('replies')
        if isinstance(replies, dict) and 'data' in replies:
            for reply_item in replies['data']['children']:
                if reply_item['kind'] != 't1':
                    continue
                    
                reply_data = reply_item['data']
                reply_body = reply_data.get('body', '')
                
                if reply_body in ['[deleted]', '[removed]', '']:
                    continue
                
                comments.append({
                    'body': reply_body,
                    'score': reply_data.get('score', 0),
                    'author': reply_data.get('author', '[deleted]'),
                    'is_reply': True
                })
    
    # Sort by score (highest first) and limit
    comments.sort(key=lambda x: x['score'], reverse=True)
    return comments[:max_comments]


def analyze_sentiment(comments: list[dict]) -> dict:
    """Send comments to Haiku for sentiment analysis."""
    
    # Format comments for the prompt
    comments_text = "\n\n".join([
        f"[Score: {c['score']}] {c['body']}"
        for c in comments
    ])
    
    prompt = f"""You are analyzing fan reactions from a Reddit game thread for an Iowa Hawkeyes women's basketball game (2025-26 season).

CRITICAL CONTEXT - IOWA HAWKEYES ROSTER (2025-26):
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
- Only reference players from the roster above

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


    # Call Bedrock with Haiku
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    response_text = result['content'][0]['text']
    
    # Fix unescaped quotes in JSON strings (common Haiku issue)
    import re
    def fix_json_quotes(text):
        # This regex finds strings and escapes internal quotes
        # Simple approach: replace "Chit Chat" pattern specifically
        text = text.replace('Chazadi "Chit Chat" Wright', 'Chazadi \\"Chit Chat\\" Wright')
        text = text.replace('Chazadi "Chit-Chat" Wright', 'Chazadi \\"Chit-Chat\\" Wright')
        return text
    
    response_text = fix_json_quotes(response_text)

    # Debug: write raw response to file
    with open('haiku_response.txt', 'w') as f:
        f.write(response_text)
    print(f"\n🔍 Raw response saved to haiku_response.txt")
    
    # Try to parse JSON, with error handling
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parse error: {e}")
        print(f"Response preview: {response_text[:500]}")
        raise


def main():
    print("=" * 60)
    print("Reddit Sentiment Analysis Test")
    print("=" * 60)
    
    # Step 1: Fetch comments
    print(f"\n📥 Fetching comments from Reddit...")
    comments = fetch_reddit_comments(REDDIT_URL, max_comments=150)
    print(f"   Found {len(comments)} comments")
    
    # Show top 5 comments
    print(f"\n📊 Top 5 comments by score:")
    for i, c in enumerate(comments[:5], 1):
        preview = c['body'][:80] + "..." if len(c['body']) > 80 else c['body']
        print(f"   {i}. [Score: {c['score']}] {preview}")
    
    # Step 2: Analyze with Haiku
    print(f"\n🤖 Sending to Haiku for analysis...")
    sentiment = analyze_sentiment(comments)
    
    # Step 3: Display results
    print(f"\n" + "=" * 60)
    print("SENTIMENT ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n📈 Score: {sentiment['score']}/10")
    print(f"🏷️  Label: {sentiment['label']}")
    
    print(f"\n📝 Summary:")
    print(f"   {sentiment['summary']}")
    
    print(f"\n🎯 Key Themes:")
    for theme in sentiment['themes']:
        print(f"   • {theme}")
    
    print(f"\n💬 Notable Quotes:")
    for quote in sentiment['notable_quotes']:
        print(f"   \"{quote['text']}\"")
        print(f"   └─ {quote['context']}")
        print()
    
    # Also dump full JSON for inspection
    print(f"\n📋 Full JSON response:")
    print(json.dumps(sentiment, indent=2))


if __name__ == '__main__':
    main()