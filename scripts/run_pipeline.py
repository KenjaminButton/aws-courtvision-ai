#!/usr/bin/env python3
"""
run_pipeline.py - Main data pipeline for CourtVision AI

This script runs the complete data pipeline:
1. Fetch/sync game schedule from ESPN
2. Fetch detailed data for newly completed games
3. Run pattern detection on games with new data

Usage:
    python3 run_pipeline.py                    # Run for current season
    python3 run_pipeline.py --season 2025     # Run for specific season
    python3 run_pipeline.py --skip-details    # Only sync schedule
    python3 run_pipeline.py --skip-patterns   # Skip pattern detection

Recommended: Run this daily or before each game day via cron/Lambda.
"""

import subprocess
import sys
import argparse
from datetime import datetime


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"   Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {cmd[0]}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run CourtVision AI data pipeline'
    )
    
    parser.add_argument(
        '--season',
        type=int,
        default=2026,
        help='Season ending year (default: 2026 for 2025-26)'
    )
    
    parser.add_argument(
        '--skip-details',
        action='store_true',
        help='Skip fetching game details'
    )
    
    parser.add_argument(
        '--skip-patterns',
        action='store_true',
        help='Skip pattern detection'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-fetch all data'
    )
    
    args = parser.parse_args()
    
    season_label = f"{args.season - 1}-{str(args.season)[2:]}"
    
    print("\n" + "=" * 60)
    print(f"🏀 COURTVISION AI - DATA PIPELINE")
    print(f"📅 Season: {season_label}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        'schedule': False,
        'details': False,
        'patterns': False,
    }
    
    # Step 1: Fetch/sync schedule
    cmd = ['python3', 'fetch_season_games.py', '--season', str(args.season)]
    if args.force:
        cmd.append('--force')
    
    results['schedule'] = run_command(cmd, "Step 1: Syncing Game Schedule")
    
    if not results['schedule']:
        print("\n❌ Schedule sync failed. Stopping pipeline.")
        return 1
    
    # Step 2: Fetch game details
    if not args.skip_details:
        cmd = ['python3', 'fetch_game_details.py', '--season', str(args.season)]
        if args.force:
            cmd.append('--force')
        
        results['details'] = run_command(cmd, "Step 2: Fetching Game Details")
    else:
        print("\n⏭️  Skipping Step 2: Game Details (--skip-details)")
        results['details'] = True
    
    # Step 3: Pattern detection
    if not args.skip_patterns:
        # Only run if we have the pattern detection script
        try:
            cmd = ['python3', 'analyze_patterns.py', '--season', str(args.season)]
            results['patterns'] = run_command(cmd, "Step 3: Pattern Detection")
        except Exception:
            print("\n⚠️  Pattern detection script not found, skipping...")
            results['patterns'] = True
    else:
        print("\n⏭️  Skipping Step 3: Pattern Detection (--skip-patterns)")
        results['patterns'] = True
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PIPELINE SUMMARY")
    print("=" * 60)
    
    status = {True: "✅ Success", False: "❌ Failed"}
    
    print(f"   Schedule Sync:     {status[results['schedule']]}")
    print(f"   Game Details:      {status[results['details']]}")
    print(f"   Pattern Detection: {status[results['patterns']]}")
    
    print(f"\n🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Return success if all steps passed
    if all(results.values()):
        print("\n✅ Pipeline completed successfully!")
        return 0
    else:
        print("\n⚠️  Pipeline completed with errors")
        return 1


if __name__ == '__main__':
    sys.exit(main())
