#!/usr/bin/env python3
"""Quick test to verify Bedrock Claude Haiku access."""

import boto3
import json

# Claude Haiku model ID
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def test_haiku():
    prompt = "In one sentence, what is Iowa Hawkeyes basketball known for?"
    
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    print("✅ Bedrock Haiku is working!\n")
    print(f"Prompt: {prompt}")
    print(f"Response: {result['content'][0]['text']}")

if __name__ == '__main__':
    test_haiku()