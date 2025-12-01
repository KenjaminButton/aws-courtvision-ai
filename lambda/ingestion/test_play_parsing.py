#!/usr/bin/env python3
import handler
import json

# Sample play from the completed game
sample_play = {
    "id": "401724074101904701",
    "sequenceNumber": "101904701",
    "type": {"id": "558", "text": "JumpShot"},
    "text": "Elina Aarnisalo missed Jumper.",
    "awayScore": 0,
    "homeScore": 0,
    "period": {"number": 1, "displayValue": "1st Quarter"},
    "clock": {"displayValue": "9:52"},
    "scoringPlay": False,
    "scoreValue": 2,
    "team": {"id": "26"}
}

game_id = "GAME#2024-11-30#FRESNO-STATE-BULLDOGS-UCLA-BRUINS"

print("Testing parse_play_data...")
print("="*50)

parsed = handler.parse_play_data(sample_play, game_id)

if parsed:
    print("✅ Successfully parsed play\n")
    print(json.dumps(parsed, indent=2))
else:
    print("❌ Failed to parse play")