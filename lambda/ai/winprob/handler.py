import json
import os
import boto3
import time
from datetime import datetime
from decimal import Decimal

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Win Probability Prompt Template
WIN_PROB_PROMPT = """Calculate win probability for women's college basketball:

Home: {home_team} ({home_score} pts, {home_fg_pct}% FG, {home_3pt_pct}% 3PT)
Away: {away_team} ({away_score} pts, {away_fg_pct}% FG, {away_3pt_pct}% 3PT)
Time: Q{quarter}, {time_remaining} ({game_minute:.0f} min elapsed)

Respond JSON only:
{{
  "home_probability": 0.XX,
  "away_probability": 0.XX,
  "reasoning": "<1-2 sentences>"
}}"""

# Global variable to track last calculation time per game
last_calculation_times = {}

def should_calculate_win_prob(game_id):
    """
    Throttle Win Probability calculations to max 1 per 2 minutes
    
    Returns:
        bool: True if enough time has passed since last calculation
    """
    current_time = time.time()
    last_calc = last_calculation_times.get(game_id, 0)
    
    # Allow calculation if 120 seconds (2 minutes) have passed
    if current_time - last_calc >= 120:
        last_calculation_times[game_id] = current_time
        return True
    
    print(f"⏱️  Throttled Win Prob for {game_id} (last calc {int(current_time - last_calc)}s ago)")
    return False

def calculate_game_minute(quarter, game_clock):
    """
    Calculate elapsed game minutes from quarter and game clock
    
    Args:
        quarter: Current quarter (1-4 for regulation, 5+ for OT)
        game_clock: Game clock string (e.g., "7:23" or "3:45")
    
    Returns:
        float: Game minutes elapsed
    
    Examples:
        Q1 at 7:00 → 3.0 minutes
        Q3 at 5:30 → 24.5 minutes
        OT1 at 3:00 → 42.0 minutes
    """
    try:
        # Parse clock (format: "MM:SS" or "M:SS")
        if ':' in game_clock:
            parts = game_clock.split(':')
            clock_minutes = int(parts[0])
            clock_seconds = int(parts[1])
            clock_total = clock_minutes + (clock_seconds / 60.0)
        else:
            clock_total = 0.0
        
        # Regulation (Quarters 1-4)
        if quarter <= 4:
            return (quarter - 1) * 10 + (10 - clock_total)
        
        # Overtime (Quarters 5+)
        else:
            ot_period = quarter - 5  # 0 for OT1, 1 for OT2, etc.
            return 40 + (ot_period * 5) + (5 - clock_total)
    
    except Exception as e:
        print(f"⚠️ Error calculating game minute: {str(e)}")
        return 0.0


def get_team_player_stats(game_id, team_name):
    """
    Query all player stats for a specific team in a game
    
    Args:
        game_id: Game identifier (PK)
        team_name: Team name to filter by (e.g., "Stanford")
    
    Returns:
        dict: Aggregated team stats or None if no stats found
    """
    try:
        # Scan for all player stats in this game
        response = table.scan(
            FilterExpression='begins_with(PK, :player_prefix) AND gameId = :gid',
            ExpressionAttributeValues={
                ':player_prefix': 'PLAYER#',
                ':gid': game_id
            }
        )
        
        players = response.get('Items', [])
        
        # Filter by team and aggregate
        team_stats = {
            'fgMade': 0,
            'fgAttempted': 0,
            'threeMade': 0,
            'threeAttempted': 0
        }
        
        for player in players:
            if player.get('team') == team_name:
                team_stats['fgMade'] += int(player.get('fgMade', 0))
                team_stats['fgAttempted'] += int(player.get('fgAttempted', 0))
                team_stats['threeMade'] += int(player.get('threeMade', 0))
                team_stats['threeAttempted'] += int(player.get('threeAttempted', 0))
        
        return team_stats if team_stats['fgAttempted'] > 0 else None
        
    except Exception as e:
        print(f"⚠️ Error querying team stats for {team_name}: {str(e)}")
        return None


def calculate_team_shooting(game_id, team_name):
    """
    Calculate shooting percentages for a team
    
    Args:
        game_id: Game identifier
        team_name: Team name (e.g., "Stanford")
    
    Returns:
        dict: Shooting percentages or "Not yet available"
    """
    stats = get_team_player_stats(game_id, team_name)
    
    if stats and stats['fgAttempted'] > 0:
        fg_pct = (stats['fgMade'] / stats['fgAttempted']) * 100
        three_pct = (stats['threeMade'] / stats['threeAttempted']) * 100 if stats['threeAttempted'] > 0 else 0
        
        print(f"📊 {team_name} shooting: {fg_pct:.1f}% FG ({stats['fgMade']}/{stats['fgAttempted']}), {three_pct:.1f}% 3PT ({stats['threeMade']}/{stats['threeAttempted']})")
        
        return {
            'fg_pct': round(fg_pct, 1),
            '3pt_pct': round(three_pct, 1)
        }
    else:
        print(f"⚠️ No shooting stats available yet for {team_name}")
        return {
            'fg_pct': 'Not yet available',
            '3pt_pct': 'Not yet available'
        }


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
        quarter = int(score.get('quarter', 1))
        game_clock = score.get('gameClock', '10:00')
        game_minute = calculate_game_minute(quarter, game_clock)
        # Calculate real shooting percentages
        home_shooting = calculate_team_shooting(game_id, metadata.get('homeTeam', 'Home'))
        away_shooting = calculate_team_shooting(game_id, metadata.get('awayTeam', 'Away'))


        context = {
            'home_team': metadata.get('homeTeam', 'Home'),
            'away_team': metadata.get('awayTeam', 'Away'),
            'home_score': int(score.get('homeScore', 0)),
            'away_score': int(score.get('awayScore', 0)),
            'quarter': quarter,
            'time_remaining': game_clock,
            'game_minute': game_minute,
            'recent_trend': recent_trend,
            'home_fg_pct': home_shooting['fg_pct'],
            'home_3pt_pct': home_shooting['3pt_pct'],
            'away_fg_pct': away_shooting['fg_pct'],
            'away_3pt_pct': away_shooting['3pt_pct'],
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
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        print("🔄 Calling Bedrock for win probability...")
        
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-haiku-20241022-v1:0',
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
            'gameMinute': Decimal(str(game_context['game_minute'])),
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
            'gameMinute': Decimal(str(game_context['game_minute'])),
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
        
        # Throttle to prevent excessive calculations
        if not should_calculate_win_prob(game_id):
            return {
                'statusCode': 200,
                'body': json.dumps('Throttled - too soon since last calculation')
            }
        
        # Step 1: Gather game context
        game_context = get_game_context(game_id)
        if not game_context:
            return {'statusCode': 500, 'body': 'Failed to fetch game context'}
        
        print(f"Game: {game_context['home_team']} {game_context['home_score']} - {game_context['away_team']} {game_context['away_score']}")
        
        # ADD THIS CHECK - If game is over, don't call Bedrock
        if game_context['time_remaining'] == '0:00' or game_context['game_minute'] >= 40:
            home_score = game_context['home_score']
            away_score = game_context['away_score']
            
            if home_score > away_score:
                winner = game_context['home_team']
                probability_data = {
                    'home_probability': 1.0,
                    'away_probability': 0.0,
                    'reasoning': f"Game is over. {winner} won {home_score}-{away_score}."
                }
            else:
                winner = game_context['away_team']
                probability_data = {
                    'home_probability': 0.0,
                    'away_probability': 1.0,
                    'reasoning': f"Game is over. {winner} won {away_score}-{home_score}."
                }
            
            print(f"🏁 Game over - deterministic result (no Bedrock call needed)")
        else:
            # Step 2: Calculate win probability (only if game is still in progress)
            probability_data = calculate_win_probability(game_context)
        
        # Check if probability_data was set (either deterministic or from Bedrock)
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