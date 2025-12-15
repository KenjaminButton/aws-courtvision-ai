# Adding New Seasons to CourtVision AI

This guide explains how to add a new basketball season to your CourtVision AI application.

## Quick Reference

| Season | Value | Label | Dates |
|--------|-------|-------|-------|
| 2024-25 | 2025 | "2024-25 Season" | Nov 2024 - Apr 2025 |
| 2025-26 | 2026 | "2025-26 Season" | Nov 2025 - Apr 2026 |
| 2026-27 | 2027 | "2026-27 Season" | Nov 2026 - Apr 2027 |

**Note:** The `value` is the ending year of the season (e.g., 2025-26 season → value 2026)

---

## Step 1: Update Frontend Season Configuration

Edit `frontend/src/contexts/SeasonContext.tsx`:

```typescript
export const AVAILABLE_SEASONS = [
  { value: 2027, label: '2026-27 Season', current: true },  // NEW - Set as current
  { value: 2026, label: '2025-26 Season', current: false }, // Previous current
  { value: 2025, label: '2024-25 Season', current: false }, // Historical
] as const;
```

**Rules:**
- Add new seasons at the TOP of the array (most recent first)
- Set `current: true` for the active season
- Set `current: false` for all other seasons
- The `current: true` season will be the default when the app loads

---

## Step 2: Fetch Game Data for the New Season

### Option A: Update your fetch script

In your backend scripts, update the season parameter:

```python
# scripts/fetch_iowa_schedule.py

SEASON = "2026-27"  # Update this
SEASON_VALUE = 2027  # For API calls
```

Then run:
```bash
cd scripts
python3 fetch_iowa_schedule.py
```

### Option B: Manual API call

Your API should accept a season parameter:
```
GET /games?season=2027
```

Make sure your Lambda function and ESPN fetch logic handle the new season.

---

## Step 3: Verify Data is Available

Test your API:
```bash
curl "https://your-api.execute-api.us-east-1.amazonaws.com/prod/games?season=2027"
```

Should return:
```json
{
  "season": "2027",
  "games": [...],
  "count": 34
}
```

---

## Step 4: Test in Frontend

1. Start dev server: `npm run dev`
2. Check dropdown shows new season
3. Select new season, verify games load
4. Click a game, verify details work

---

## Troubleshooting

### "No games found" for new season
- Check if ESPN has released the schedule yet (usually October)
- Verify your fetch script ran successfully
- Check DynamoDB for `SEASON#2027` entries

### Games not loading after switching seasons
- Open DevTools → Network tab
- Check API call: `/games?season=2027`
- Verify response contains games array

### Old season still showing as default
- Make sure `current: true` is set for the new season
- Clear browser cache or hard refresh (Cmd+Shift+R)

---

## Backend API Requirements

Your `/games` endpoint should accept a `season` query parameter:

```python
def get_games(event, context):
    season = event.get('queryStringParameters', {}).get('season', '2026')
    
    # Query DynamoDB
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': f"SEASON#{season}"}
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'season': season,
            'games': response['Items'],
            'count': len(response['Items'])
        })
    }
```

---

## Automating for Future Seasons

Consider creating a script that runs at the start of each season:

```bash
#!/bin/bash
# scripts/setup_new_season.sh

NEW_SEASON=$1  # e.g., "2027"

echo "Setting up season $NEW_SEASON..."

# Fetch schedule from ESPN
python3 fetch_iowa_schedule.py --season $NEW_SEASON

# Update frontend config (requires manual edit for 'current')
echo "Remember to update SeasonContext.tsx with current: true for $NEW_SEASON"

echo "Done! Now deploy frontend."
```

---

## Timeline Reminder

| Date | Action |
|------|--------|
| October | ESPN releases next season schedule |
| Early November | Season starts, fetch initial games |
| Throughout Season | Games auto-update after completion |
| April | Season ends, set current: false |
| Next October | Add new season, repeat |

---

## Questions?

If something isn't working:
1. Check browser console for errors
2. Check API response in Network tab
3. Verify DynamoDB has data for the season
4. Make sure SeasonContext.tsx is saved and app is rebuilt