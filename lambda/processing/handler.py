import json
import base64
import os
from datetime import datetime

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

def handler(event, context):
    """
    Processing Lambda - triggered by Kinesis stream
    
    Receives play-by-play data from Kinesis, processes it,
    and will eventually write to DynamoDB.
    """
    try:
        print("🏀 CourtVision Processing Lambda started")
        print(f"Received {len(event['Records'])} records from Kinesis")
        
        processed_count = 0
        
        for record in event['Records']:
            # Kinesis data is base64 encoded
            payload = base64.b64decode(record['kinesis']['data'])
            play_data = json.loads(payload)
            
            # For now, just log the play
            print(f"📝 Processing play: {play_data.get('playId', 'unknown')}")
            print(f"   Game: {play_data.get('PK', 'unknown')}")
            print(f"   Quarter: {play_data.get('quarter', 'unknown')}")
            print(f"   Text: {play_data.get('text', 'N/A')}")
            
            processed_count += 1
        
        print(f"✅ Successfully processed {processed_count} plays")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {processed_count} plays')
        }
        
    except Exception as e:
        print(f"❌ Error processing Kinesis records: {str(e)}")
        raise