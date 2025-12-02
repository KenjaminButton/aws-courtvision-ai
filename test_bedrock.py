#!/usr/bin/env python3
"""
Test script to verify AWS Bedrock access with Claude
Run this locally before integrating into Lambda
"""

import json
import boto3
from botocore.exceptions import ClientError

def test_bedrock_access():
    """Test basic Bedrock API call with Claude"""
    
    # Initialize Bedrock client
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'  # Change to your region if different
    )
    
    # Simple test prompt
    prompt = "Hello! Can you respond with just 'Bedrock is working' if you receive this?"
    
    # Bedrock API request body for Claude
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        print("🔄 Testing Bedrock API call...")
        print(f"Model: claude-3-5-sonnet-20241022-v2:0")
        print(f"Prompt: {prompt}\n")
        
        # Invoke the model
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Extract the text response
        assistant_message = response_body['content'][0]['text']
        
        print("✅ Bedrock API call successful!")
        print(f"Response: {assistant_message}\n")
        
        # Show token usage
        usage = response_body.get('usage', {})
        print(f"📊 Token Usage:")
        print(f"   Input tokens: {usage.get('input_tokens', 0)}")
        print(f"   Output tokens: {usage.get('output_tokens', 0)}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ Bedrock API Error: {error_code}")
        print(f"   Message: {error_message}\n")
        
        if error_code == 'AccessDeniedException':
            print("🔧 Next Step: Submit use case details")
            print("   This is AWS's new requirement for first-time Anthropic model users")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🏀 CourtVision AI - Bedrock Test\n")
    print("=" * 50)
    
    success = test_bedrock_access()
    
    print("=" * 50)
    if success:
        print("✅ Bedrock is ready for CourtVision AI!")
    else:
        print("❌ See error above - we'll fix it together")