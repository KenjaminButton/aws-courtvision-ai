import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

print("🗑️  Deleting all player stats...")

response = table.scan(
    FilterExpression='begins_with(PK, :prefix)',
    ExpressionAttributeValues={':prefix': 'PLAYER#'}
)

items = response.get('Items', [])
total_deleted = 0

with table.batch_writer() as batch:
    for item in items:
        batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
        total_deleted += 1
        print(f"   Deleted {item['PK']}")

print(f"\n✅ Deleted {total_deleted} player stat records")