#!/usr/bin/env python3
"""
Test AI Game Summary prompt locally before deploying Lambda.
"""

import boto3
import json
from decimal import Decimal

# Setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
GAME_ID = "401818635"  # Lindenwood game


def get_game_data(game_id: str) -> dict:
    response = table.get_item(
        Key={'pk': f'GAME#{game_id}', 'sk': 'METADATA'}
    )
    return response.get('Item')


def get_patterns(game_id: str) -> list:
    from boto3.dynamodb.conditions import Key
    response = table.query(
        KeyConditionExpression=Key('pk').eq(f'GAME#{game_id}') & Key('sk').begins_with('PATTERN#')
    )
    return response.get('Items', [])


def build_prompt(game: dict, patterns: list) -> str:
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
            pattern_text += f"- ({team_label}) {p.get('points_for')}-{p.get('points_against')} scoring run in period {p.get('period')}\n"
        elif p.get('pattern_type') == 'hot_streak':
            pattern_text += f"- ({team_label}) {p.get('player_name')} made {p.get('consecutive_makes')} consecutive field goals\n"
    
    # Get top performers from player_stats
    top_performers = ""
    iowa_players = game.get('player_stats', {}).get('iowa', [])
    if iowa_players:
        sorted_players = sorted(iowa_players, key=lambda x: int(x.get('points', 0)), reverse=True)[:3]
        for p in sorted_players:
            fg = p.get('field_goals', '?-?')
            top_performers += f"- {p.get('player_name', 'Unknown')}: {p.get('points', 0)} pts ({fg} FG), {p.get('rebounds', 0)} reb, {p.get('assists', 0)} ast\n"
    
    # MANUAL GAME CONTEXT - edit this for each game!
    game_context = """Iowa (#11) hosts unranked Lindenwood in a non-conference tune-up game.

    STARTERS THIS GAME:
    - Hannah Stuelke (Senior, Forward)
    - Ava Heiden (Sophomore, Center)
    - Taylor McCabe (Senior, Guard)
    - Kylie Feuerbach (Graduate Student, Guard)
    - Chazadi "Chit Chat" Wright (Sophomore, Guard)

    GAME NOTES:
    This is Iowa's final home game before the holiday break, before traveling to Brooklyn to face #1 ranked UConn Huskies next Saturday in a highly anticipated top-15 matchup. The Hawkeyes used this game to get bench players extended minutes. Point guard Chazadi "Chit Chat" Wright left the game early and did not return - perhaps we are saving her for the UConn game next weekend in Brooklyn, New York. This was a breakout game for Hannah Stuelke and we hope her confidence can carry into the rest of the season. Ava Heiden and Layla Hays played very well."""

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


def main():
    print(f"🏀 Testing AI Summary for game {GAME_ID}\n")
    print("=" * 60)
    
    # Fetch data
    print("\n📊 Fetching game data...")
    game = get_game_data(GAME_ID)
    if not game:
        print("❌ Game not found!")
        return
    
    print(f"   Iowa: {game.get('iowa', {}).get('score')} vs {game.get('opponent', {}).get('name')}: {game.get('opponent', {}).get('score')}")
    
    patterns = get_patterns(GAME_ID)
    print(f"   Patterns found: {len(patterns)}")
    
    # Build and show prompt
    prompt = build_prompt(game, patterns)
    print("\n📝 PROMPT BEING SENT TO Sonnet v1.0:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    
    # Ask for confirmation before calling Bedrock (costs money!)
    confirm = input("\n⚠️  Send to Bedrock Sonnet v1.0? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    # Call Bedrock
    print("\n🤖 Calling Claude Sonnet v1.0...")
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
    summary = result['content'][0]['text']
    
    print("\n✅ AI GENERATED SUMMARY:")
    print("=" * 60)
    print(summary)
    print("=" * 60)
    print(f"\nWord count: {len(summary.split())}")


if __name__ == '__main__':
    main()