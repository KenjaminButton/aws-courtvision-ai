#!/usr/bin/env python3
"""
Test script for Win Probability prompt engineering
Tests various game scenarios before building the Lambda
"""

import json
import boto3
from datetime import datetime

# Initialize Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

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


def call_bedrock_win_prob(game_state):
    """
    Call Bedrock with win probability prompt
    
    Args:
        game_state: Dict with game state information
    
    Returns:
        Dict with home_probability, away_probability, reasoning
    """
    # Format the prompt with game state
    prompt = WIN_PROB_PROMPT.format(**game_state)
    
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
    
    try:
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        assistant_message = response_body['content'][0]['text']
        
        # Parse JSON from response
        result = json.loads(assistant_message)
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"Raw response: {assistant_message}")
        return None
    except Exception as e:
        print(f"❌ Error calling Bedrock: {str(e)}")
        return None


def test_scenario(name, game_state):
    """Test a specific game scenario"""
    print(f"\n{'='*60}")
    print(f"📊 Testing: {name}")
    print(f"{'='*60}")
    print(f"Game State: {game_state['home_team']} {game_state['home_score']} - {game_state['away_team']} {game_state['away_score']}")
    print(f"Quarter {game_state['quarter']}, {game_state['time_remaining']}")
    print()
    
    result = call_bedrock_win_prob(game_state)
    
    if result:
        print(f"✅ Home Win Probability: {result['home_probability']:.1%}")
        print(f"✅ Away Win Probability: {result['away_probability']:.1%}")
        print(f"✅ Reasoning: {result['reasoning']}")
        
        # Validate
        prob_sum = result['home_probability'] + result['away_probability']
        if abs(prob_sum - 1.0) > 0.01:
            print(f"⚠️  Warning: Probabilities sum to {prob_sum}, not 1.0")
    else:
        print("❌ Test failed")


if __name__ == "__main__":
    print("🏀 Win Probability Prompt Testing")
    
    # Test Case 1: Close game, 3rd quarter
    test_scenario("Close Game - Mid 3rd Quarter", {
        'home_team': 'UConn',
        'away_team': 'Stanford',
        'home_score': 58,
        'away_score': 52,
        'quarter': 3,
        'time_remaining': '7:03',
        'recent_trend': 'UConn on a 9-2 run over last 3 minutes',
        'home_fg_pct': 45.2,
        'home_3pt_pct': 41.7,
        'away_fg_pct': 42.1,
        'away_3pt_pct': 28.6
    })
    
    # Test Case 2: Tied game, start of 4th quarter
    test_scenario("Tied Game - Start of 4th Quarter", {
        'home_team': 'South Carolina',
        'away_team': 'LSU',
        'home_score': 62,
        'away_score': 62,
        'quarter': 4,
        'time_remaining': '10:00',
        'recent_trend': 'Teams trading baskets, no clear momentum',
        'home_fg_pct': 48.3,
        'home_3pt_pct': 35.0,
        'away_fg_pct': 46.7,
        'away_3pt_pct': 38.5
    })
    
    # Test Case 3: Blowout - 4th quarter
    test_scenario("Blowout - Late 4th Quarter", {
        'home_team': 'Iowa',
        'away_team': 'Nebraska',
        'home_score': 88,
        'away_score': 65,
        'quarter': 4,
        'time_remaining': '3:24',
        'recent_trend': 'Iowa has controlled the entire second half',
        'home_fg_pct': 52.1,
        'home_3pt_pct': 44.4,
        'away_fg_pct': 38.9,
        'away_3pt_pct': 25.0
    })
    
    # Test Case 4: Close finish - under 1 minute
    test_scenario("Nail-biter - Final Minute", {
        'home_team': 'Notre Dame',
        'away_team': 'Louisville',
        'home_score': 71,
        'away_score': 69,
        'quarter': 4,
        'time_remaining': '0:47',
        'recent_trend': 'Louisville hit a three to cut lead to 2',
        'home_fg_pct': 44.0,
        'home_3pt_pct': 33.3,
        'away_fg_pct': 43.2,
        'away_3pt_pct': 36.4
    })
    
    print(f"\n{'='*60}")
    print("✅ All test scenarios complete")
    print(f"{'='*60}")