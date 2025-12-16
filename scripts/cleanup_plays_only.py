import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('courtvision-games')

def delete_all_plays():
    """Delete ONLY sk=PLAY# records, nothing else"""
    print("Scanning for PLAY# records...")
    
    deleted = 0
    scan_kwargs = {
        'FilterExpression': 'begins_with(sk, :play)',
        'ExpressionAttributeValues': {':play': 'PLAY#'},
        'ProjectionExpression': 'pk, sk'
    }
    
    while True:
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        if not items:
            break
        
        print(f"  Deleting batch of {len(items)}...")
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'pk': item['pk'], 'sk': item['sk']})
                deleted += 1
        
        if 'LastEvaluatedKey' not in response:
            break
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    print(f"\n✅ Deleted {deleted} PLAY# records")

if __name__ == '__main__':
    confirm = input("Delete ALL PLAY# records? (yes/no): ")
    if confirm.lower() == 'yes':
        delete_all_plays()
    else:
        print("Aborted")