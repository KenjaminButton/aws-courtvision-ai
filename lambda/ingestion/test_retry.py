#!/usr/bin/env python3
import handler
import requests
from unittest.mock import patch, MagicMock

print("Testing retry logic with simulated failures...")
print("="*50)

# Test 1: Simulate timeout then success
print("\n1. Testing timeout recovery:")
print("   Simulating: timeout, timeout, success")

call_count = [0]

def mock_get_timeout_then_success(url, timeout):
    call_count[0] += 1
    if call_count[0] <= 2:
        raise requests.exceptions.Timeout("Simulated timeout")
    
    # Success on 3rd attempt
    mock_response = MagicMock()
    mock_response.json.return_value = {'events': []}
    return mock_response

with patch('requests.get', side_effect=mock_get_timeout_then_success):
    try:
        result = handler.fetch_espn_scoreboard()
        print(f"   ✅ Succeeded after {call_count[0]} attempts")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

# Test 2: Simulate all failures
print("\n2. Testing complete failure:")
print("   Simulating: timeout, timeout, timeout (all fail)")

call_count[0] = 0

def mock_get_all_fail(url, timeout):
    call_count[0] += 1
    raise requests.exceptions.Timeout("Simulated timeout")

with patch('requests.get', side_effect=mock_get_all_fail):
    try:
        result = handler.fetch_espn_scoreboard()
        print(f"   ❌ Should have failed but didn't")
    except Exception as e:
        print(f"   ✅ Failed gracefully after {call_count[0]} attempts: {type(e).__name__}")

print("\n✅ Retry logic tests complete!")