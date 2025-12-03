import json
import boto3
from datetime import datetime

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def load_game_data():
    """Load the live game data we fetched earlier"""
    with open('live-game-data.json', 'r') as f:
        return json.load(f)

def extract_scoring_plays(game_data):
    """Extract all scoring plays from the game"""
    plays = []
    for play in game_data.get('plays', []):
        if play.get('scoringPlay'):
            plays.append({
                'text': play.get('text', ''),
                'clock': play.get('clock', {}).get('displayValue', ''),
                'period': play.get('period', {}).get('number', 1),
                'type': play.get('type', {}).get('text', ''),
                'scoreValue': play.get('scoreValue', 0),
                'homeScore': play.get('homeScore', 0),
                'awayScore': play.get('awayScore', 0)
            })
    return plays

def build_prompt(play, home_team="USC Trojans", away_team="Saint Mary's Gaels"):
    """Build the commentary prompt for a play"""
    # Extract player name from text
    player_name = play['text'].split(' made ')[0] if ' made ' in play['text'] else "Unknown Player"
    
    prompt = f"""You are an enthusiastic women's college basketball commentator. Generate exciting play-by-play commentary for this event.

Play Details:
- Player: {player_name}
- Action: {play['type']}
- Description: {play['text']}
- Points (if scoring): {play['scoreValue']}
- Current Score: {home_team} {play['homeScore']} - {away_team} {play['awayScore']}

Game Context:
- Quarter: {play['period']}, Time: {play['clock']}
- Player's Game Stats: (stats not available in this test)
- Recent Context: (context not available in this test)

CRITICAL RULES:
1. MAXIMUM 2 sentences. No exceptions.
2. DO NOT invent player details (year, position, etc.) not provided above
3. DO NOT use clichés: "ice water in veins", "nothing but net", "on fire", "lights out"
4. Only mention facts explicitly provided in the data above
5. Match excitement to play significance (routine basket = 0.3-0.5, clutch shot = 0.7-0.9)

Generate natural, exciting commentary that sounds like a professional broadcaster.

Respond in JSON format:
{{
  "commentary": "<your commentary>",
  "excitement": <float 0-1>
}}"""
    
    return prompt

def call_bedrock(prompt):
    """Call Bedrock with the prompt"""
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 300,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Parse JSON from response
        return json.loads(content)
    except Exception as e:
        return {'error': str(e)}

def validate_response(response, play):
    """Validate the commentary response"""
    issues = []
    
    # Check JSON format
    if 'error' in response:
        issues.append(f"❌ API Error: {response['error']}")
        return issues
    
    if 'commentary' not in response or 'excitement' not in response:
        issues.append("❌ Missing required fields")
        return issues
    
    commentary = response['commentary']
    excitement = response['excitement']
    
    # Check sentence count
    sentence_count = commentary.count('.') + commentary.count('!') + commentary.count('?')
    if sentence_count > 2:
        issues.append(f"⚠️  Too many sentences: {sentence_count}")
    
    # Check for clichés
    cliches = ['ice water', 'nothing but net', 'on fire', 'lights out', 'from downtown']
    for cliche in cliches:
        if cliche.lower() in commentary.lower():
            issues.append(f"⚠️  Cliché detected: '{cliche}'")
    
    # Check excitement range
    if not (0 <= excitement <= 1):
        issues.append(f"❌ Excitement out of range: {excitement}")
    
    if not issues:
        issues.append("✅ All checks passed")
    
    return issues

def main():
    print("🏀 CourtVision AI - Commentary Testing\n")
    print("=" * 70)
    
    # Load game data
    game_data = load_game_data()
    plays = extract_scoring_plays(game_data)
    
    print(f"\n📊 Found {len(plays)} scoring plays to test\n")
    
    results = []
    
    for i, play in enumerate(plays, 1):  # Test ALL plays
    # for i, play in enumerate(plays[:10], 1):  # Test first 10 plays
        print(f"\n{'='*70}")
        print(f"Test {i}/10: {play['text'][:60]}...")
        print(f"Score: {play['homeScore']}-{play['awayScore']} | Q{play['period']} {play['clock']}")
        
        # Build and send prompt
        prompt = build_prompt(play)
        response = call_bedrock(prompt)
        
        # Validate
        issues = validate_response(response, play)
        
        # Display results
        if 'commentary' in response:
            print(f"\n💬 Commentary: {response['commentary']}")
            print(f"🎭 Excitement: {response['excitement']}")
        
        print(f"\n🔍 Validation:")
        for issue in issues:
            print(f"   {issue}")
        
        results.append({
            'play': play,
            'response': response,
            'issues': issues
        })
    
    # Summary
    print(f"\n\n{'='*70}")
    print("📈 SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for r in results if '✅' in '\n'.join(r['issues']))
    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"⚠️  Issues: {len(results) - passed}/{len(results)}")

if __name__ == '__main__':
    main()