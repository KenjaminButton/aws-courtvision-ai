import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

def delete_all_items():
    """Delete all items from DynamoDB table"""
    
    print("🗑️  Starting deletion process...")
    
    total_deleted = 0
    
    # Scan and delete in batches
    while True:
        # Scan for items (max 25 at a time for batch delete)
        response = table.scan(Limit=25)
        items = response.get('Items', [])
        
        if not items:
            print("✅ Table is empty!")
            break
        
        # Batch delete
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'PK': item['PK'],
                        'SK': item['SK']
                    }
                )
                total_deleted += 1
        
        print(f"🗑️  Deleted {len(items)} items... (Total: {total_deleted})")
    
    print(f"\n✅ Deletion complete! Total deleted: {total_deleted}")

if __name__ == '__main__':
    confirm = input("⚠️  This will DELETE ALL ITEMS from courtvision-games. Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        delete_all_items()
    else:
        print("❌ Deletion cancelled")