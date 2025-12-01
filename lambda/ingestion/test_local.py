#!/usr/bin/env python3
import handler

# Simulate Lambda invoke
result = handler.handler(event={}, context=None)

print("\n" + "="*50)
print("RESULT:")
print("="*50)
print(result)