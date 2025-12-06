**Perfect! Here's your testing checklist:**

---

## **CourtVision AI - Live Game Testing Checklist**
**Date: December 4, 2025 | Start Time: 4:05 PM PST**

---

### **Pre-Test Setup (Do at 4:00 PM):**

- [ ] Open browser tabs:
  - [ ] DynamoDB Console: https://console.aws.amazon.com/dynamodbv2
  - [ ] CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
  - [ ] Frontend: http://localhost:3000
  - [ ] ESPN Scoreboard: https://www.espn.com/womens-college-basketball/scoreboard

- [ ] Open terminal (ready for AWS CLI commands)

---

### **TEST 1: Verify Data Ingestion (4:05 PM)**

**DynamoDB → courtvision-games**

**Check 1.1: Game Metadata Exists**
- [ ] Query: PK = `GAME#2025-12-04#[today's game]`, SK = `METADATA`
- [ ] Verify fields: homeTeam, awayTeam, homeTeamId, awayTeamId
- [ ] Screenshot metadata item

**Check 1.2: Current Score Updating**
- [ ] Query: PK = same game, SK = `SCORE#CURRENT`
- [ ] Verify: homeScore > 0, awayScore > 0, gameClock changing
- [ ] Screenshot score item

**Check 1.3: Plays Being Stored**
- [ ] Query: PK = same game, SK begins with `PLAY#`
- [ ] Verify: Multiple play records exist
- [ ] Pick one play and verify fields: playerId, playerName, teamId, text
- [ ] Screenshot one play item

---

### **TEST 2: Verify Player Stats with Correct Teams (4:10 PM)**

**DynamoDB → courtvision-games**

**Check 2.1: Player Stats Exist**
- [ ] Query: PK begins with `PLAYER#`
- [ ] Find 2-3 player records
- [ ] Screenshot the list

**Check 2.2: Team Field is Correct (NOT "Unknown")**
- [ ] Click on one player stat record
- [ ] Verify `team` field shows actual team name (e.g., "Oklahoma", "NC State")
- [ ] ❌ If says "Unknown" → Processing Lambda team mapping FAILED
- [ ] ✅ If shows team name → Processing Lambda team mapping WORKS
- [ ] Screenshot player stat with team name

**Check 2.3: Stats Look Reasonable**
- [ ] Verify: points > 0, fgMade/fgAttempted make sense
- [ ] Compare to ESPN box score for that player
- [ ] Note any discrepancies

---

### **TEST 3: Verify Win Probability Calculation (4:15 PM)**

**CloudWatch Logs → courtvision-ai-winprob**

**Check 3.1: Win Prob Lambda Triggered**
- [ ] Go to: /aws/lambda/courtvision-ai-winprob
- [ ] Filter by "last 30 minutes"
- [ ] Look for recent log entries
- [ ] Screenshot log stream list

**Check 3.2: Real Shooting Stats Logged**
- [ ] Open most recent log stream
- [ ] Search for: `"📊"` or `"shooting"`
- [ ] Look for lines like: `"📊 Oklahoma shooting: 48.5% FG (16/33), 33.3% 3PT (3/9)"`
- [ ] ❌ If says "⚠️ No shooting stats available yet" → Check if enough plays processed
- [ ] ✅ If shows percentages → Shooting calculation WORKS
- [ ] Screenshot log with shooting stats

**Check 3.3: Win Prob Stored in DynamoDB**
- [ ] DynamoDB → Query: PK = game, SK begins with `AI#WIN_PROB#`
- [ ] Find records with recent timestamps
- [ ] Verify fields: homeWinProbability, awayWinProbability, reasoning, gameMinute
- [ ] Screenshot win prob record

---

### **TEST 4: Frontend Verification (4:20 PM)**

**Browser: http://localhost:3000**

**Check 4.1: Dashboard Shows Today's Games**
- [ ] Games appear on homepage
- [ ] Scores are updating (not 0-0)
- [ ] Screenshot dashboard

**Check 4.2: Live Game View**
- [ ] Click on a game
- [ ] Live score displays correctly
- [ ] Quarter and game clock shown
- [ ] WebSocket status: "Connected"
- [ ] Screenshot game view

**Check 4.3: AI Commentary**
- [ ] Commentary feed has items
- [ ] Player names are correct (not "Unknown")
- [ ] Stats mentioned in commentary match ESPN
- [ ] New commentary appears as plays happen
- [ ] Screenshot commentary section

**Check 4.4: Win Probability Bar**
- [ ] Probability bar visible
- [ ] Percentages add up to 100%
- [ ] Bar reflects current game state
- [ ] Screenshot win prob bar

**Check 4.5: Win Probability Reasoning**
- [ ] AI reasoning text visible below bar
- [ ] Mentions actual shooting percentages (e.g., "Oklahoma's 48% FG shooting...")
- [ ] ❌ If says "45% FG" → Using hardcoded values (FAILED)
- [ ] ✅ If says varied percentages matching DynamoDB → Using real stats (WORKS)
- [ ] Screenshot reasoning with shooting stats

**Check 4.6: Win Probability Graph**
- [ ] Graph displays with data points
- [ ] X-axis shows "Game Minutes" (0, 10, 20, 30, 40)
- [ ] Halftime marker at minute 20 (yellow dashed line)
- [ ] Line moves across time as game progresses
- [ ] ❌ If flat or only 1 point → AI Orchestrator not triggering
- [ ] Screenshot graph

---

### **TEST 5: Compare to ESPN (4:25 PM)**

**ESPN Box Score vs CourtVision**

**Check 5.1: Pick One Player**
- [ ] Find player on ESPN box score (e.g., "Player X: 12 PTS, 4-8 FG, 2-4 3PT")
- [ ] Find same player in DynamoDB
- [ ] Compare: points, fgMade/fgAttempted, threeMade/threeAttempted
- [ ] Note accuracy percentage

**Check 5.2: Team Shooting Percentages**
- [ ] ESPN team stats: Team FG%, Team 3PT%
- [ ] CourtVision win prob reasoning: Stated FG%, 3PT%
- [ ] Compare accuracy
- [ ] Note if within 1-2% tolerance

---

### **TEST 6: Real-Time Updates (4:30 PM)**

**Watch Live Updates**

**Check 6.1: Score Updates**
- [ ] Watch game on ESPN
- [ ] When team scores, does frontend update within 60-90 seconds?
- [ ] Note latency

**Check 6.2: Commentary Generation**
- [ ] After scoring play, does new commentary appear?
- [ ] Does it mention correct player and stats?
- [ ] Note latency

**Check 6.3: Win Prob Updates**
- [ ] After significant run or lead change, does probability update?
- [ ] Does reasoning reflect new game state?

---

### **Issue Tracking:**

If something fails, note here:

**Issue 1:**
- Component: _________
- Expected: _________
- Actual: _________
- Screenshot: _________

**Issue 2:**
- Component: _________
- Expected: _________
- Actual: _________
- Screenshot: _________

---

### **Success Criteria:**

**MUST PASS (Critical):**
- [ ] Player stats have correct team names (not "Unknown")
- [ ] Win prob reasoning mentions REAL shooting % (not 45%, 35%)
- [ ] Win prob graph X-axis shows game minutes (0-40)
- [ ] Frontend updates in real-time via WebSocket

**NICE TO HAVE:**
- [ ] Commentary quality is varied and accurate
- [ ] Stats match ESPN within 95% accuracy
- [ ] No errors in CloudWatch logs

---

### **Post-Test Actions:**

If tests pass:
- [ ] Take celebration screenshots
- [ ] Update PROGRESS.md with test results
- [ ] Commit: "test: Day 30 live game validation - all features working"

If tests fail:
- [ ] Document failures with screenshots
- [ ] Check CloudWatch logs for errors
- [ ] Fix and redeploy
- [ ] Re-test

---

**Save this checklist! See you at 4:05 PM!** 🏀✨