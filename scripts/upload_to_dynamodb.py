#!/usr/bin/env python3
"""
CourtVision AI - DynamoDB Upload Script
Uploads Iowa Hawkeyes game data to DynamoDB.

Table Design (Single-Table):
  - PK: game_id (String)
  - SK: record_type (String) - "METADATA" for game info, "PLAY#0001" for plays
  
This allows efficient queries:
  - Get game metadata: PK=game_id, SK="METADATA"
  - Get all plays: PK=game_id, SK begins_with "PLAY#"
  - Scan for all games: filter on SK="METADATA"

Usage:
    python upload_to_dynamodb.py --data-dir ./data
    python upload_to_dynamodb.py --create-table  # Create table only
    python upload_to_dynamodb.py --data-dir ./data --delete-existing  # Fresh start
"""

import argparse
import json
import time
from pathlib import Path
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError


TABLE_NAME = "courtvision-games"
REGION = "us-east-1"


def get_dynamodb_resource():
    """Get DynamoDB resource."""
    return boto3.resource('dynamodb', region_name=REGION)


def get_dynamodb_client():
    """Get DynamoDB client."""
    return boto3.client('dynamodb', region_name=REGION)


def table_exists(client) -> bool:
    """Check if table exists."""
    try:
        client.describe_table(TableName=TABLE_NAME)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise


def create_table(client):
    """Create the DynamoDB table with proper schema."""
    print(f"Creating table: {TABLE_NAME}")
    
    try:
        client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},   # Partition key
                {'AttributeName': 'sk', 'KeyType': 'RANGE'},  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand pricing (good for dev)
            Tags=[
                {'Key': 'Project', 'Value': 'CourtVision-AI'},
                {'Key': 'Team', 'Value': 'Iowa-Hawkeyes'},
            ]
        )
        
        # Wait for table to be active
        print("  Waiting for table to become active...")
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"  ✓ Table {TABLE_NAME} is ready!")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"  Table {TABLE_NAME} already exists")
        else:
            raise


def delete_table(client):
    """Delete the DynamoDB table."""
    print(f"Deleting table: {TABLE_NAME}")
    
    try:
        client.delete_table(TableName=TABLE_NAME)
        
        # Wait for deletion
        print("  Waiting for table to be deleted...")
        waiter = client.get_waiter('table_not_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"  ✓ Table {TABLE_NAME} deleted")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"  Table {TABLE_NAME} doesn't exist")
        else:
            raise


def convert_floats(obj):
    """
    Recursively convert floats to Decimals for DynamoDB.
    Also handles None values and empty strings.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [convert_floats(i) for i in obj if i is not None]
    elif obj == "":
        return None  # DynamoDB doesn't like empty strings
    return obj


def upload_game(table, game_data: dict) -> tuple[int, int]:
    """
    Upload a single game to DynamoDB.
    
    Returns:
        Tuple of (metadata_items, play_items) uploaded
    """
    game_id = game_data['game_id']
    
    # Prepare game metadata (everything except plays)
    metadata = {k: v for k, v in game_data.items() if k != 'plays'}
    metadata = convert_floats(metadata)
    
    # Upload metadata item
    table.put_item(Item={
        'pk': f"GAME#{game_id}",
        'sk': 'METADATA',
        'entity_type': 'GAME',
        **metadata
    })
    
    # Upload plays in batches (DynamoDB batch_write limit is 25)
    plays = game_data.get('plays', [])
    play_count = 0
    
    with table.batch_writer() as batch:
        for i, play in enumerate(plays):
            play = convert_floats(play)
            sequence = str(i).zfill(4)  # "0000", "0001", etc.
            
            batch.put_item(Item={
                'pk': f"GAME#{game_id}",
                'sk': f"PLAY#{sequence}",
                'entity_type': 'PLAY',
                'game_id': game_id,
                **play
            })
            play_count += 1
    
    return (1, play_count)


def upload_schedule(table, schedule_data: dict):
    """Upload schedule metadata."""
    season_year = schedule_data.get('season_year', 2025)
    
    # Create schedule summary item
    schedule_item = {
        'pk': f"SCHEDULE#{season_year}",
        'sk': 'METADATA',
        'entity_type': 'SCHEDULE',
        'team_id': schedule_data.get('team_id'),
        'season_year': season_year,
        'total_games': schedule_data.get('total_games'),
        'fetched_at': schedule_data.get('fetched_at'),
    }
    
    table.put_item(Item=convert_floats(schedule_item))
    
    # Create individual game schedule entries for quick listing
    with table.batch_writer() as batch:
        for game in schedule_data.get('games', []):
            game = convert_floats(game)
            game_id = game.get('game_id')
            
            batch.put_item(Item={
                'pk': f"SCHEDULE#{season_year}",
                'sk': f"GAME#{game_id}",
                'entity_type': 'SCHEDULE_GAME',
                'game_id': game_id,
                'date': game.get('date'),
                'short_name': game.get('short_name'),
                'season_type': game.get('season_type'),
                'season_type_id': game.get('season_type_id'),
                'status_completed': game.get('status_completed'),
                'iowa_score': game.get('iowa', {}).get('score'),
                'iowa_won': game.get('iowa', {}).get('winner'),
                'opponent_abbrev': game.get('opponent', {}).get('abbreviation'),
                'opponent_score': game.get('opponent', {}).get('score'),
                'tournament_round': game.get('tournament_round'),
            })
    
    print(f"  ✓ Schedule uploaded: {len(schedule_data.get('games', []))} games")


def main():
    parser = argparse.ArgumentParser(description='Upload Iowa game data to DynamoDB')
    parser.add_argument('--data-dir', type=str, default='./data',
                       help='Directory containing game data')
    parser.add_argument('--create-table', action='store_true',
                       help='Create table only (no data upload)')
    parser.add_argument('--delete-existing', action='store_true',
                       help='Delete existing table before creating new one')
    parser.add_argument('--skip-plays', action='store_true',
                       help='Upload game metadata only, skip play-by-play')
    args = parser.parse_args()
    
    print("=" * 70)
    print("COURTVISION AI - DYNAMODB UPLOAD")
    print("=" * 70)
    
    client = get_dynamodb_client()
    dynamodb = get_dynamodb_resource()
    
    # Handle table creation/deletion
    if args.delete_existing:
        if table_exists(client):
            delete_table(client)
            time.sleep(2)  # Brief pause after deletion
    
    if not table_exists(client):
        create_table(client)
    else:
        print(f"Table {TABLE_NAME} already exists")
    
    if args.create_table:
        print("\n✓ Table ready (--create-table flag, skipping data upload)")
        return
    
    # Get table reference
    table = dynamodb.Table(TABLE_NAME)
    
    # Find data files
    data_dir = Path(args.data_dir)
    schedule_file = data_dir / 'iowa_schedule_2025.json'
    games_dir = data_dir / 'games'
    
    if not schedule_file.exists():
        print(f"\nERROR: Schedule file not found: {schedule_file}")
        print("Run collect_iowa_data.py first!")
        return
    
    # Upload schedule
    print(f"\n[1/2] Uploading schedule...")
    with open(schedule_file) as f:
        schedule_data = json.load(f)
    upload_schedule(table, schedule_data)
    
    # Upload games
    print(f"\n[2/2] Uploading game data...")
    game_files = sorted(games_dir.glob('game_*.json'))
    
    if not game_files:
        print(f"  No game files found in {games_dir}")
        return
    
    total_games = 0
    total_plays = 0
    
    for i, game_file in enumerate(game_files, 1):
        with open(game_file) as f:
            game_data = json.load(f)
        
        if args.skip_plays:
            game_data['plays'] = []  # Clear plays
        
        games, plays = upload_game(table, game_data)
        total_games += games
        total_plays += plays
        
        opponent = game_data.get('opponent', {}).get('abbreviation', 'OPP')
        print(f"  [{i}/{len(game_files)}] Game {game_data['game_id']} vs {opponent}: {plays} plays")
    
    # Summary
    print("\n" + "=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)
    print(f"Table: {TABLE_NAME}")
    print(f"Region: {REGION}")
    print(f"Games uploaded: {total_games}")
    print(f"Plays uploaded: {total_plays:,}")
    
    # Show how to query
    print("\n" + "-" * 70)
    print("QUERY EXAMPLES (AWS CLI)")
    print("-" * 70)
    print(f"""
# Get schedule
aws dynamodb query \\
  --table-name {TABLE_NAME} \\
  --key-condition-expression "pk = :pk" \\
  --expression-attribute-values '{{":pk":{{"S":"SCHEDULE#2025"}}}}' \\
  --region {REGION}

# Get game metadata
aws dynamodb get-item \\
  --table-name {TABLE_NAME} \\
  --key '{{"pk":{{"S":"GAME#401713556"}},"sk":{{"S":"METADATA"}}}}' \\
  --region {REGION}

# Get all plays for a game
aws dynamodb query \\
  --table-name {TABLE_NAME} \\
  --key-condition-expression "pk = :pk AND begins_with(sk, :sk)" \\
  --expression-attribute-values '{{":pk":{{"S":"GAME#401713556"}},":sk":{{"S":"PLAY#"}}}}' \\
  --region {REGION}
""")


if __name__ == '__main__':
    main()