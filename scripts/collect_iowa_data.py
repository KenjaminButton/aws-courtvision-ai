#!/usr/bin/env python3
"""
CourtVision AI - Complete Data Collection Pipeline
Fetches all Iowa Hawkeyes data for a season in one run.

Usage:
    python collect_iowa_data.py [--season YEAR]
    
Example:
    python collect_iowa_data.py --season 2025  # Collects all 2024-25 season data
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# Import our fetcher modules
from fetch_iowa_schedule import fetch_schedule, parse_schedule, save_schedule
from fetch_playbyplay import fetch_game_summary, parse_game_data


def main():
    parser = argparse.ArgumentParser(description='Collect all Iowa Hawkeyes game data')
    parser.add_argument('--season', type=int, default=2025,
                       help='Season ending year (e.g., 2025 for 2024-25 season)')
    parser.add_argument('--output-dir', type=str, default='./data',
                       help='Base output directory')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between API calls in seconds')
    parser.add_argument('--skip-pbp', action='store_true',
                       help='Skip play-by-play fetching (schedule only)')
    args = parser.parse_args()
    
    start_time = datetime.now()
    output_dir = Path(args.output_dir)
    games_dir = output_dir / 'games'
    
    print("=" * 70)
    print("COURTVISION AI - IOWA HAWKEYES DATA COLLECTION")
    print(f"Season: {args.season-1}-{str(args.season)[2:]}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # STEP 1: Fetch Schedule
    print("\n[STEP 1/2] Fetching season schedule...")
    raw_schedule = fetch_schedule(args.season)
    games = parse_schedule(raw_schedule)
    schedule_file = save_schedule(games, output_dir, args.season)
    
    completed_games = [g for g in games if g.get('status_completed')]
    print(f"  ✓ Found {len(games)} total games, {len(completed_games)} completed")
    
    if args.skip_pbp:
        print("\n[STEP 2/2] Skipping play-by-play (--skip-pbp flag set)")
    else:
        # STEP 2: Fetch Play-by-Play for all completed games
        print(f"\n[STEP 2/2] Fetching play-by-play for {len(completed_games)} games...")
        games_dir.mkdir(parents=True, exist_ok=True)
        
        successful = 0
        failed = []
        total_plays = 0
        
        for i, game in enumerate(completed_games, 1):
            game_id = game['game_id']
            game_file = games_dir / f"game_{game_id}.json"
            
            # Check cache
            if game_file.exists():
                with open(game_file) as f:
                    cached = json.load(f)
                    total_plays += cached.get('play_count', 0)
                    successful += 1
                    opp = game.get('opponent', {}).get('abbreviation', 'OPP')
                    print(f"  [{i}/{len(completed_games)}] vs {opp}: cached ({cached.get('play_count', 0)} plays)")
                continue
            
            try:
                raw_data = fetch_game_summary(game_id)
                parsed_data = parse_game_data(raw_data, game_id)
                
                with open(game_file, 'w') as f:
                    json.dump(parsed_data, f, indent=2)
                
                plays = parsed_data.get('play_count', 0)
                total_plays += plays
                successful += 1
                
                opp = game.get('opponent', {}).get('abbreviation', 'OPP')
                date = game.get('date', '')[:10]
                print(f"  [{i}/{len(completed_games)}] {date} vs {opp}: {plays} plays")
                
                if i < len(completed_games):
                    time.sleep(args.delay)
                    
            except Exception as e:
                failed.append({'game_id': game_id, 'error': str(e)})
                print(f"  [{i}/{len(completed_games)}] ERROR: {e}")
    
    # Summary
    elapsed = datetime.now() - start_time
    
    print("\n" + "=" * 70)
    print("DATA COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Season: {args.season-1}-{str(args.season)[2:]}")
    print(f"Total Games: {len(games)}")
    print(f"  - Regular Season: {len([g for g in games if g.get('season_type_id') == '2'])}")
    print(f"  - Postseason: {len([g for g in games if g.get('season_type_id') == '3'])}")
    
    if not args.skip_pbp:
        print(f"\nPlay-by-Play Data:")
        print(f"  - Games fetched: {successful}/{len(completed_games)}")
        print(f"  - Total plays: {total_plays:,}")
        if failed:
            print(f"  - Failed: {len(failed)}")
            for f in failed:
                print(f"      {f['game_id']}: {f['error']}")
    
    print(f"\nOutput Location:")
    print(f"  Schedule: {schedule_file}")
    if not args.skip_pbp:
        print(f"  Games: {games_dir}/")
    
    print(f"\nElapsed Time: {elapsed}")
    print("\n✓ Ready for DynamoDB upload!")


if __name__ == '__main__':
    main()