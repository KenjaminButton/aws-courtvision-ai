import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

GAME_ID = 'GAME#2025-11-23#MIAMI-HURRICANES-IOWA-HAWKEYES'

def get_all_plays(game_id):
    """Get all plays for a game, sorted chronologically"""
    plays = []
    last_key = None
    
    while True:
        if last_key:
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :play)',
                ExpressionAttributeValues={':pk': game_id, ':play': 'PLAY#'},
                ExclusiveStartKey=last_key
            )
        else:
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :play)',
                ExpressionAttributeValues={':pk': game_id, ':play': 'PLAY#'}
            )
        
        plays.extend(response['Items'])
        
        if 'LastEvaluatedKey' not in response:
            break
        last_key = response['LastEvaluatedKey']
    
    # Sort by timestamp (SK contains timestamp)
    plays.sort(key=lambda p: p['SK'])
    return plays

def detect_run_in_window(window, home_team, away_team, window_size):
    """Check if a window contains a scoring run"""
    home_pts = 0
    away_pts = 0
    
    for play in window:
        if play.get('scoringPlay'):
            team = play.get('team')
            pts = play.get('pointsScored', 0)
            
            if team == home_team:
                home_pts += pts
            elif team == away_team:
                away_pts += pts
    
    # Custom thresholds per window size
    thresholds = {
        25: (8, 2),    # Short burst: 8-2
        50: (16, 4),   # Medium run: 16-4
        75: (20, 6),   # Long run: 20-6
        120: (20, 8)   # Quarter dominance: 20-8 (more lenient)
    }
    
    min_points, max_opponent = thresholds.get(window_size, (8, 2))
    
    if home_pts >= min_points and away_pts <= max_opponent:
        return {
            'team': home_team,
            'points_for': home_pts,
            'points_against': away_pts,
            'window_type': f'{window_size}-play'
        }
    elif away_pts >= min_points and home_pts <= max_opponent:
        return {
            'team': away_team,
            'points_for': away_pts,
            'points_against': home_pts,
            'window_type': f'{window_size}-play'
        }
    
    return None

def analyze_quarter_runs(quarter_plays, home_team, away_team, quarter_num):
    """Analyze runs within a single quarter"""
    if len(quarter_plays) < 25:
        return []
    
    # Find all runs in this quarter with different window sizes
    quarter_runs = []
    max_window = min(len(quarter_plays), 120)

    for window_size in [25, 50, 75, max_window]:
        if window_size > len(quarter_plays):
            continue
        
        for i in range(len(quarter_plays) - window_size + 1):
            window = quarter_plays[i:i+window_size]
            run = detect_run_in_window(window, home_team, away_team, window_size)
            
            if run:
                run['quarter'] = quarter_num
                run['start_play'] = i
                run['end_play'] = i + window_size
                run['window_start_sk'] = window[0]['SK']
                run['window_end_sk'] = window[-1]['SK']
                quarter_runs.append(run)
    
    return quarter_runs

def find_all_runs_by_quarter(plays, home_team, away_team):
    """Analyze each quarter separately"""
    # Group plays by quarter
    quarters = {}
    for play in plays:
        q = play.get('quarter', 0)
        if q not in quarters:
            quarters[q] = []
        quarters[q].append(play)
    
    # Analyze each quarter
    all_runs = []
    for quarter_num in sorted(quarters.keys()):
        print(f"   Analyzing Q{quarter_num}...")
        quarter_plays = quarters[quarter_num]
        quarter_runs = analyze_quarter_runs(quarter_plays, home_team, away_team, quarter_num)
        all_runs.extend(quarter_runs)
    
    return all_runs

def deduplicate_runs(runs):
    """Keep only the biggest run per team per quarter"""
    if not runs:
        return []
    
    # Group by quarter and team
    best_runs = {}
    
    for run in runs:
        quarter = run.get('quarter', 0)
        team = run['team']
        key = (quarter, team)
        
        # Keep the biggest run for this quarter/team combo
        if key not in best_runs or run['points_for'] > best_runs[key]['points_for']:
            best_runs[key] = run
    
    # Sort by quarter, then by points
    unique_runs = list(best_runs.values())
    unique_runs.sort(key=lambda r: (r.get('quarter', 0), -r['points_for']))
    
    return unique_runs

def store_pattern(game_id, pattern):
    """Store pattern in DynamoDB"""
    timestamp = datetime.now().isoformat()
    
    table.put_item(Item={
        'PK': game_id,
        'SK': f"AI#PATTERN#{timestamp}",
        'patternType': 'scoring_run',
        'team': pattern['team'],
        'pointsFor': pattern['points_for'],
        'pointsAgainst': pattern['points_against'],
        'description': f"{pattern['team']} on a {pattern['points_for']}-{pattern['points_against']} run",
        'detectedAt': timestamp,
        'windowStart': pattern.get('window_start_sk', ''),
        'windowEnd': pattern.get('window_end_sk', '')
    })

def detect_hot_streaks(plays):
    """Detect players with 3+ consecutive made shots"""
    hot_streaks = []
    player_streaks = {}  # player_id -> consecutive makes
    
    for play in plays:
        player_id = play.get('playerId')
        if not player_id:
            continue
        
        # Check if this is a made shot (not free throw)
# Check if this is a made shot (not free throw)
        action = play.get('action', '').lower()
        is_free_throw = 'free' in action
        is_made_shot = ('made' in action and not is_free_throw)
        is_missed_shot = ('missed' in action and not is_free_throw)
        
        if is_made_shot:
            # Increment streak
            if player_id not in player_streaks:
                player_streaks[player_id] = {
                    'count': 0,
                    'player_name': play.get('playerName', 'Unknown'),
                    'team': play.get('team', 'Unknown'),
                    'plays': []
                }
            
            player_streaks[player_id]['count'] += 1
            player_streaks[player_id]['plays'].append(play)
            
            # Check if streak qualifies (3+)
            if player_streaks[player_id]['count'] >= 3:
                # Record the streak at this point
                streak = player_streaks[player_id]
                hot_streaks.append({
                    'type': 'hot_streak',
                    'player_id': player_id,
                    'player_name': streak['player_name'],
                    'team': streak['team'],
                    'consecutive_makes': streak['count'],
                    'quarter': play.get('quarter', 0),
                    'timestamp': play.get('timestamp', '')
                })
        
        elif is_missed_shot:
            # Reset streak on miss
            if player_id in player_streaks:
                del player_streaks[player_id]
    
    # Deduplicate - keep only the longest streak per player
    best_streaks = {}
    for streak in hot_streaks:
        player_id = streak['player_id']
        if player_id not in best_streaks or streak['consecutive_makes'] > best_streaks[player_id]['consecutive_makes']:
            best_streaks[player_id] = streak
    
    return list(best_streaks.values())

def detect_momentum_shifts(plays, home_team, away_team):
    """Detect lead changes after trailing by 3+ points"""
    momentum_shifts = []
    
    previous_leader = None
    max_deficit = 0  # Track maximum deficit since last lead change
    
    for play in plays:
        home_score = play.get('homeScore', 0)
        away_score = play.get('awayScore', 0)
        margin = home_score - away_score
        
        current_leader = 'home' if margin > 0 else 'away' if margin < 0 else 'tied'
        
        # Track maximum deficit for current trailing team
        if current_leader == 'home':
            max_deficit = max(max_deficit, abs(margin))
        elif current_leader == 'away':
            max_deficit = max(max_deficit, abs(margin))
        
        # Check for lead change
        if previous_leader and current_leader != 'tied' and current_leader != previous_leader:
            # They took the lead - check the maximum deficit they overcame
            if max_deficit >= 1:
                team_name = home_team if current_leader == 'home' else away_team
                momentum_shifts.append({
                    'type': 'momentum_shift',
                    'team': team_name,
                    'previous_deficit': max_deficit,
                    'new_score': f"{home_score}-{away_score}",
                    'quarter': play.get('quarter', 0),
                    'timestamp': play.get('timestamp', ''),
                    'description': f"{team_name} storms back from {max_deficit} down to take the lead"
                })
            
            # Reset max deficit after lead change
            max_deficit = 0
        
        previous_leader = current_leader
    
    return momentum_shifts

def store_hot_streak(game_id, streak):
    """Store hot streak pattern in DynamoDB"""
    timestamp = datetime.now().isoformat()
    
    table.put_item(Item={
        'PK': game_id,
        'SK': f"AI#PATTERN#{timestamp}#HOTSTREAK",
        'patternType': 'hot_streak',
        'playerId': streak['player_id'],
        'playerName': streak['player_name'],
        'team': streak['team'],
        'consecutiveMakes': streak['consecutive_makes'],
        'quarter': streak['quarter'],
        'description': f"{streak['player_name']} on fire - {streak['consecutive_makes']} straight made shots!",
        'detectedAt': timestamp
    })

def store_momentum_shift(game_id, shift):
    """Store momentum shift pattern in DynamoDB"""
    timestamp = datetime.now().isoformat()
    
    table.put_item(Item={
        'PK': game_id,
        'SK': f"AI#PATTERN#{timestamp}#MOMENTUM",
        'patternType': 'momentum_shift',
        'team': shift['team'],
        'previousDeficit': shift['previous_deficit'],
        'newScore': shift['new_score'],
        'quarter': shift['quarter'],
        'description': shift['description'],
        'detectedAt': timestamp
    })


def analyze_game(game_id):
    """Main analysis function"""
    print(f"🔍 Analyzing patterns for {game_id}...\n")
    
    # Get metadata for team names
    metadata_response = table.get_item(
        Key={'PK': game_id, 'SK': 'METADATA'}
    )
    metadata = metadata_response.get('Item', {})
    home_team = metadata.get('homeTeam', 'Home')
    away_team = metadata.get('awayTeam', 'Away')
    
    print(f"📋 Teams: {home_team} vs {away_team}")
    
    # Get all plays
    print("📥 Loading all plays...")
    plays = get_all_plays(game_id)
    print(f"   Loaded {len(plays)} plays")
    
    # *** ADD THIS DEBUG ***
    print("\n📊 Analyzing quarter breakdown...")
    for quarter in [1, 2, 3, 4]:
        quarter_plays = [p for p in plays if p.get('quarter') == quarter]
        quarter_scoring = [p for p in quarter_plays if p.get('scoringPlay')]
        
        home_pts = sum(p.get('pointsScored', 0) for p in quarter_scoring if p.get('team') == home_team)
        away_pts = sum(p.get('pointsScored', 0) for p in quarter_scoring if p.get('team') == away_team)
        
        print(f"   Q{quarter}: {len(quarter_plays)} total plays, {len(quarter_scoring)} scoring")
        print(f"          {home_team}: {home_pts} pts, {away_team}: {away_pts} pts")
    # *** END DEBUG ***
    
    # Find all runs by quarter
    print("\n🔍 Scanning for scoring runs by quarter...")
    all_runs = find_all_runs_by_quarter(plays, home_team, away_team)
    print(f"   Found {len(all_runs)} potential runs")
    
    # Deduplicate
    print("\n🧹 Deduplicating overlapping runs...")
    unique_runs = deduplicate_runs(all_runs)
    print(f"   {len(unique_runs)} unique runs")
    
    # Display and store
    print("\n🔥 DETECTED PATTERNS:\n")
    for i, run in enumerate(unique_runs, 1):
        desc = f"{run['team']} on a {run['points_for']}-{run['points_against']} run"
        print(f"   {i}. {desc}")
        store_pattern(game_id, run)
    
    print(f"\n✅ Analysis complete! Stored {len(unique_runs)} patterns in DynamoDB")
    
    # *** ADD THIS ***
    # Detect hot streaks
    print("\n🔥 Detecting hot streaks...")
    hot_streaks = detect_hot_streaks(plays)
    print(f"   Found {len(hot_streaks)} hot streaks")
    
    for streak in hot_streaks:
        desc = f"{streak['player_name']} ({streak['team']}): {streak['consecutive_makes']} straight makes"
        print(f"   🔥 {desc}")
        store_hot_streak(game_id, streak)
    
    # Detect momentum shifts
    print("\n⚡ Detecting momentum shifts...")
    momentum_shifts = detect_momentum_shifts(plays, home_team, away_team)
    print(f"   Found {len(momentum_shifts)} momentum shifts")
    
    for shift in momentum_shifts:
        print(f"   ⚡ {shift['description']}")
        store_momentum_shift(game_id, shift)
    
    print(f"\n✅ Complete! Stored {len(unique_runs)} runs, {len(hot_streaks)} hot streaks, {len(momentum_shifts)} momentum shifts")

if __name__ == '__main__':
    analyze_game(GAME_ID)
