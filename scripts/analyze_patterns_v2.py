#!/usr/bin/env python3
"""
analyze_patterns_v2.py - Detect scoring patterns in Iowa Hawkeyes games

This script analyzes play-by-play data to detect:
1. Scoring Runs - One team dominates scoring over a window of plays
2. Hot Streaks - Player makes 3+ consecutive field goals

SCHEMA (matches fetch_game_details.py):
- pk: GAME#{game_id}  (lowercase, e.g., GAME#401713556)
- sk: PLAY#0001      (zero-padded sequence)
- Pattern sk: PATTERN#scoring_run#001 or PATTERN#hot_streak#001

Usage:
    python3 analyze_patterns_v2.py                     # Analyze all games
    python3 analyze_patterns_v2.py --game 401713556   # Specific game
    python3 analyze_patterns_v2.py --season 2026      # Specific season
    python3 analyze_patterns_v2.py --clear            # Clear existing patterns first
"""

import boto3
import argparse
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

# Configuration
DYNAMODB_TABLE = "courtvision-games"
IOWA_TEAM_ID = "2294"

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(DYNAMODB_TABLE)


def get_all_games(season: int) -> list:
    """Get all completed games for a season"""
    games = []
    
    response = table.query(
        KeyConditionExpression='pk = :pk',
        ExpressionAttributeValues={':pk': f"SEASON#{season}"}
    )
    
    for item in response.get('Items', []):
        if item.get('status_completed') and item.get('details_fetched'):
            games.append({
                'game_id': item['game_id'],
                'date': item.get('date', ''),
                'opponent': item.get('opponent_abbrev', 'OPP'),
            })
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': f"SEASON#{season}"},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for item in response.get('Items', []):
            if item.get('status_completed') and item.get('details_fetched'):
                games.append({
                    'game_id': item['game_id'],
                    'date': item.get('date', ''),
                    'opponent': item.get('opponent_abbrev', 'OPP'),
                })
    
    return sorted(games, key=lambda x: x['date'])


def get_game_metadata(game_id: str) -> dict:
    """Get game metadata including team names"""
    response = table.get_item(
        Key={'pk': f"GAME#{game_id}", 'sk': 'METADATA'}
    )
    return response.get('Item', {})


def get_all_plays(game_id: str) -> list:
    """Get all plays for a game, sorted by sequence"""
    plays = []
    
    response = table.query(
        KeyConditionExpression='pk = :pk AND begins_with(sk, :play)',
        ExpressionAttributeValues={
            ':pk': f"GAME#{game_id}",
            ':play': 'PLAY#'
        }
    )
    
    plays.extend(response.get('Items', []))
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression='pk = :pk AND begins_with(sk, :play)',
            ExpressionAttributeValues={
                ':pk': f"GAME#{game_id}",
                ':play': 'PLAY#'
            },
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        plays.extend(response.get('Items', []))
    
    # Sort by sequence number
    plays.sort(key=lambda p: int(p.get('sequence', 0)))
    return plays


def clear_existing_patterns(game_id: str) -> int:
    """Delete existing patterns for a game"""
    count = 0
    
    response = table.query(
        KeyConditionExpression='pk = :pk AND begins_with(sk, :pattern)',
        ExpressionAttributeValues={
            ':pk': f"GAME#{game_id}",
            ':pattern': 'PATTERN#'
        }
    )
    
    for item in response.get('Items', []):
        table.delete_item(Key={'pk': item['pk'], 'sk': item['sk']})
        count += 1
    
    return count


def detect_scoring_run(window: list, iowa_team_id: str, opponent_team_id: str, window_size: int) -> dict:
    """Check if a window of plays contains a scoring run"""
    iowa_pts = 0
    opponent_pts = 0
    
    for play in window:
        if play.get('scoring_play'):
            team_id = str(play.get('team_id', ''))
            pts = int(play.get('score_value', 0))
            
            if team_id == iowa_team_id:
                iowa_pts += pts
            elif team_id == opponent_team_id:
                opponent_pts += pts
    
    # Thresholds based on window size
    thresholds = {
        25: (8, 2),    # 8-2 run or better in 25 plays
        50: (14, 4),   # 14-4 run or better in 50 plays
        75: (18, 6),   # 18-6 run or better in 75 plays
        100: (22, 8),  # 22-8 run or better in 100 plays
    }
    
    min_points, max_opponent = thresholds.get(window_size, (8, 2))
    
    # Check if Iowa is on a run
    if iowa_pts >= min_points and opponent_pts <= max_opponent:
        return {
            'is_iowa': True,
            'points_for': iowa_pts,
            'points_against': opponent_pts,
        }
    # Check if opponent is on a run
    elif opponent_pts >= min_points and iowa_pts <= max_opponent:
        return {
            'is_iowa': False,
            'points_for': opponent_pts,
            'points_against': iowa_pts,
        }
    
    return None


def find_scoring_runs(plays: list, iowa_team_id: str, opponent_team_id: str, 
                       iowa_name: str, opponent_name: str) -> list:
    """Find all scoring runs in the game"""
    runs = []
    
    # Group plays by period
    periods = defaultdict(list)
    for play in plays:
        period = play.get('period', 1)
        periods[period].append(play)
    
    # Analyze each period
    for period, period_plays in sorted(periods.items()):
        if len(period_plays) < 25:
            continue
        
        period_runs = []
        
        # Try different window sizes
        for window_size in [25, 50, 75]:
            if window_size > len(period_plays):
                continue
            
            for i in range(len(period_plays) - window_size + 1):
                window = period_plays[i:i + window_size]
                run = detect_scoring_run(window, iowa_team_id, opponent_team_id, window_size)
                
                if run:
                    # Get start/end sequence numbers
                    start_seq = int(window[0].get('sequence', 0))
                    end_seq = int(window[-1].get('sequence', 0))
                    
                    period_runs.append({
                        'team': iowa_name if run['is_iowa'] else opponent_name,
                        'team_id': iowa_team_id if run['is_iowa'] else opponent_team_id,
                        'is_iowa': run['is_iowa'],
                        'points_for': run['points_for'],
                        'points_against': run['points_against'],
                        'period': period,
                        'window_size': window_size,
                        'start_sequence': start_seq,
                        'end_sequence': end_seq,
                    })
        
        # Deduplicate: keep the best run per team per period
        best_runs = {}
        for run in period_runs:
            key = (run['period'], run['team'])
            if key not in best_runs or run['points_for'] > best_runs[key]['points_for']:
                best_runs[key] = run
        
        runs.extend(best_runs.values())
    
    return runs


def extract_player_name_from_text(text: str) -> str:
    """
    Extract player name from play text as fallback.
    Examples:
        'Hannah Stuelke made Layup.' -> 'Hannah Stuelke'
        'Lucy Olsen missed Three Point Jumper.' -> 'Lucy Olsen'
    """
    if not text:
        return ''
    
    action_words = [
        ' made ', ' missed ', ' Made ', ' Missed ',
        ' Offensive Rebound', ' Defensive Rebound',
        ' Turnover', ' Steal', ' Block', ' Foul',
    ]
    
    for action in action_words:
        if action in text:
            name = text.split(action)[0].strip()
            if len(name) >= 2 and not name.startswith('Team'):
                return name
    
    return ''


def detect_hot_streaks(plays: list, iowa_team_id: str, iowa_name: str, opponent_name: str) -> list:
    """Detect players with 3+ consecutive made field goals"""
    hot_streaks = []
    player_streaks = {}  # player_id -> streak info
    
    for play in plays:
        player_id = play.get('player_id')
        if not player_id:
            continue
        
        play_type = (play.get('type', '') or '').lower()
        text = play.get('text', '') or ''
        text_lower = text.lower()
        scoring_play = play.get('scoring_play', False)
        
        # Skip free throws
        if 'free throw' in play_type or 'free throw' in text_lower:
            continue
        
        # Check for made shot (field goal)
        is_made_shot = scoring_play and ('made' in text_lower or 'shot' in play_type or 'layup' in play_type or 'dunk' in play_type or 'jumper' in play_type)
        is_missed_shot = 'missed' in text_lower or 'miss' in play_type
        
        if is_made_shot:
            # Get player name - try field first, then extract from text
            player_name = play.get('player_name', '') or extract_player_name_from_text(text)
            
            if player_id not in player_streaks:
                player_streaks[player_id] = {
                    'count': 0,
                    'player_name': player_name or 'Unknown',
                    'team_id': play.get('team_id', ''),
                    'period': play.get('period', 1),
                }
            
            # Update name if we get a better one
            if player_name and player_streaks[player_id]['player_name'] in ['Unknown', '']:
                player_streaks[player_id]['player_name'] = player_name
            
            player_streaks[player_id]['count'] += 1
            player_streaks[player_id]['last_period'] = play.get('period', 1)
            
            # Record streak if it qualifies (3+)
            if player_streaks[player_id]['count'] >= 3:
                streak = player_streaks[player_id]
                team_id = str(streak['team_id'])
                
                hot_streaks.append({
                    'player_id': player_id,
                    'player_name': streak['player_name'],
                    'team': iowa_name if team_id == iowa_team_id else opponent_name,
                    'team_id': team_id,
                    'is_iowa': team_id == iowa_team_id,
                    'consecutive_makes': streak['count'],
                    'period': streak['last_period'],
                })
        
        elif is_missed_shot:
            # Reset streak on miss
            if player_id in player_streaks:
                del player_streaks[player_id]
    
    # Deduplicate - keep longest streak per player
    best_streaks = {}
    for streak in hot_streaks:
        player_id = streak['player_id']
        if player_id not in best_streaks or streak['consecutive_makes'] > best_streaks[player_id]['consecutive_makes']:
            best_streaks[player_id] = streak
    
    return list(best_streaks.values())


def store_pattern(game_id: str, pattern_type: str, pattern: dict, index: int):
    """Store a pattern in DynamoDB"""
    timestamp = datetime.now().isoformat()
    
    # Build description
    if pattern_type == 'scoring_run':
        description = f"{pattern['team']} {pattern['points_for']}-{pattern['points_against']} run in Q{pattern['period']}"
    else:  # hot_streak
        description = f"{pattern['player_name']}: {pattern['consecutive_makes']} consecutive makes"
    
    item = {
        'pk': f"GAME#{game_id}",
        'sk': f"PATTERN#{pattern_type}#{index:03d}",
        'entity_type': 'PATTERN',
        'pattern_type': pattern_type,
        'team': pattern['team'],
        'team_id': pattern.get('team_id', ''),
        'is_iowa': pattern.get('is_iowa', False),
        'description': description,
        'period': pattern.get('period', 1),
        'detected_at': timestamp,
    }
    
    # Add type-specific fields
    if pattern_type == 'scoring_run':
        item['points_for'] = pattern['points_for']
        item['points_against'] = pattern['points_against']
        item['start_sequence'] = pattern.get('start_sequence', 0)
        item['end_sequence'] = pattern.get('end_sequence', 0)
    else:  # hot_streak
        item['player_id'] = pattern['player_id']
        item['player_name'] = pattern['player_name']
        item['consecutive_makes'] = pattern['consecutive_makes']
    
    table.put_item(Item=item)


def analyze_game(game_id: str, clear_existing: bool = True) -> dict:
    """Analyze a single game for patterns"""
    result = {
        'game_id': game_id,
        'scoring_runs': 0,
        'hot_streaks': 0,
        'success': False,
        'error': None,
    }
    
    try:
        # Get game metadata
        metadata = get_game_metadata(game_id)
        if not metadata:
            result['error'] = "Game metadata not found"
            return result
        
        iowa_data = metadata.get('iowa', {})
        opponent_data = metadata.get('opponent', {})
        
        iowa_team_id = iowa_data.get('team_id', IOWA_TEAM_ID)
        opponent_team_id = opponent_data.get('team_id', '')
        iowa_name = iowa_data.get('name', 'Iowa Hawkeyes')
        opponent_name = opponent_data.get('name', 'Opponent')
        
        # Get all plays
        plays = get_all_plays(game_id)
        if not plays:
            result['error'] = "No plays found"
            return result
        
        # Clear existing patterns if requested
        if clear_existing:
            cleared = clear_existing_patterns(game_id)
            if cleared > 0:
                print(f"   Cleared {cleared} existing patterns")
        
        # Detect scoring runs
        scoring_runs = find_scoring_runs(
            plays, iowa_team_id, opponent_team_id, iowa_name, opponent_name
        )
        
        # Detect hot streaks
        hot_streaks = detect_hot_streaks(plays, iowa_team_id, iowa_name, opponent_name)
        
        # Store patterns
        pattern_index = 1
        
        for run in scoring_runs:
            store_pattern(game_id, 'scoring_run', run, pattern_index)
            pattern_index += 1
        
        for streak in hot_streaks:
            store_pattern(game_id, 'hot_streak', streak, pattern_index)
            pattern_index += 1
        
        result['scoring_runs'] = len(scoring_runs)
        result['hot_streaks'] = len(hot_streaks)
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Analyze games for patterns')
    parser.add_argument('--game', type=str, help='Specific game ID to analyze')
    parser.add_argument('--season', type=int, default=2026, help='Season to analyze (default: 2026)')
    parser.add_argument('--clear', action='store_true', help='Clear existing patterns before analyzing')
    
    args = parser.parse_args()
    
    print(f"\n🔍 Pattern Detection - CourtVision AI")
    print("=" * 60)
    
    if args.game:
        # Analyze single game
        print(f"📊 Analyzing game {args.game}...")
        result = analyze_game(args.game, clear_existing=args.clear)
        
        if result['success']:
            print(f"✅ Found {result['scoring_runs']} scoring runs, {result['hot_streaks']} hot streaks")
        else:
            print(f"❌ Error: {result['error']}")
        return
    
    # Analyze all games for season
    print(f"📅 Loading games for {args.season - 1}-{str(args.season)[2:]} season...")
    games = get_all_games(args.season)
    print(f"📋 Found {len(games)} completed games with details\n")
    
    if not games:
        print("⚠️  No games found to analyze")
        return
    
    total_runs = 0
    total_streaks = 0
    success_count = 0
    
    for i, game in enumerate(games, 1):
        game_id = game['game_id']
        opponent = game['opponent']
        date = game['date'].split('T')[0] if game['date'] else ''
        
        print(f"[{i}/{len(games)}] {date} vs {opponent}")
        
        result = analyze_game(game_id, clear_existing=args.clear)
        
        if result['success']:
            print(f"   ✅ {result['scoring_runs']} runs, {result['hot_streaks']} streaks")
            total_runs += result['scoring_runs']
            total_streaks += result['hot_streaks']
            success_count += 1
        else:
            print(f"   ❌ {result['error']}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY")
    print(f"   Games analyzed: {success_count}/{len(games)}")
    print(f"   Total scoring runs: {total_runs}")
    print(f"   Total hot streaks: {total_streaks}")
    print("=" * 60)


if __name__ == '__main__':
    main()