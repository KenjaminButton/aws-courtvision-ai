import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

print("📊 Re-populating player stats from existing plays...")

# Scan for all PLAY# records
response = table.scan(
    FilterExpression='begins_with(SK, :prefix)',
    ExpressionAttributeValues={':prefix': 'PLAY#'}
)

plays = response.get('Items', [])
print(f"Found {len(plays)} plays to process")

# Import the processing logic
import sys
sys.path.insert(0, 'lambda/processing')
from handler import update_player_stats

processed = 0
for play in plays:
    if play.get('playerId'):
        update_player_stats(play)
        processed += 1
        if processed % 50 == 0:
            print(f"   Processed {processed} plays...")

print(f"\n✅ Re-populated stats for {processed} plays")