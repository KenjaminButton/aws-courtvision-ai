#!/usr/bin/env python3
"""
Test script to verify Reddit comment storage and retrieval flow.
Run: python3 scripts/test_reddit_storage.py
"""

import json
import boto3
import requests
from datetime import datetime

# Config
REDDIT_URL = "https://www.reddit.com/r/NCAAW/comments/1pltt4k/game_thread_lindenwood_at_9_iowa_300_pm_et_on_b1g/"
GAME_ID = "401818635"
TABLE_NAME = "courtvision-games"

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(TABLE_NAME)


def fetch_reddit_comments(reddit_url: str, max_comments: int = 150) -> list[dict]:
    """Fetch comments from Reddit (runs locally, not in Lambda)."""
    json_url = reddit_url.rstrip('/') + '.json'
    
    headers = {
        'User-Agent': 'CourtVisionAI/1.0 (Iowa Hawkeyes Basketball Analytics)'
    }
    
    response = requests.get(json_url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    comments = []
    top_level_comments = data[1]['data']['children']
    
    for item in top_level_comments:
        if item['kind'] != 't1':
            continue
            
        comment_data = item['data']
        body = comment_data.get('body', '')
        score = comment_data.get('score', 0)
        
        if body in ['[deleted]', '[removed]', '']:
            continue
        
        comments.append({'body': body, 'score': score})
        
        # Get first-level replies
        replies = comment_data.get('replies')
        if isinstance(replies, dict) and 'data' in replies:
            for reply_item in replies['data']['children']:
                if reply_item['kind'] != 't1':
                    continue
                reply_data = reply_item['data']
                reply_body = reply_data.get('body', '')
                if reply_body not in ['[deleted]', '[removed]', '']:
                    comments.append({
                        'body': reply_body,
                        'score': reply_data.get('score', 0)
                    })
    
    comments.sort(key=lambda x: x['score'], reverse=True)
    return comments[:max_comments]


def store_comments(game_id: str, reddit_url: str, comments: list[dict]):
    """Store comments in DynamoDB."""
    item = {
        'pk': f'GAME#{game_id}',
        'sk': 'REDDIT_COMMENTS',
        'game_id': game_id,
        'reddit_url': reddit_url,
        'comments': comments,
        'comment_count': len(comments),
        'fetched_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    table.put_item(Item=item)
    return item


def get_stored_comments(game_id: str) -> dict | None:
    """Retrieve stored comments from DynamoDB."""
    try:
        response = table.get_item(
            Key={'pk': f'GAME#{game_id}', 'sk': 'REDDIT_COMMENTS'}
        )
        return response.get('Item')
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    print("=" * 60)
    print("Reddit Comment Storage Test")
    print("=" * 60)
    
    # Step 1: Fetch from Reddit (locally)
    print(f"\n📥 Fetching comments from Reddit...")
    comments = fetch_reddit_comments(REDDIT_URL, max_comments=150)
    print(f"   Found {len(comments)} comments")
    
    # Step 2: Show what we'll store
    print(f"\n📦 Data to store in DynamoDB:")
    print(f"   pk: GAME#{GAME_ID}")
    print(f"   sk: REDDIT_COMMENTS")
    print(f"   comment_count: {len(comments)}")
    print(f"   Sample comment: {comments[0]['body'][:60]}...")
    
    # Step 3: Store in DynamoDB
    print(f"\n💾 Storing in DynamoDB...")
    stored = store_comments(GAME_ID, REDDIT_URL, comments)
    print(f"   ✅ Stored successfully!")
    
    # Step 4: Retrieve and verify
    print(f"\n🔍 Retrieving from DynamoDB...")
    retrieved = get_stored_comments(GAME_ID)
    
    if retrieved:
        print(f"   ✅ Retrieved successfully!")
        print(f"   comment_count: {retrieved['comment_count']}")
        print(f"   fetched_at: {retrieved['fetched_at']}")
        print(f"   First comment score: {retrieved['comments'][0]['score']}")
    else:
        print(f"   ❌ Failed to retrieve!")
        return
    
    # Step 5: Confirm Lambda can use this
    print(f"\n✅ SUCCESS! Lambda can now read comments from DynamoDB")
    print(f"   instead of fetching from Reddit directly.")


if __name__ == '__main__':
    main()