# CourtVision AI

**Historical basketball analytics for Iowa Hawkeyes Women's Basketball**

---

## Overview

CourtVision AI is a sports analytics platform that analyzes historical games, detects patterns (scoring runs, hot streaks), tracks player performance, and provides AI-powered insights. Built to showcase AWS serverless architecture and data pipeline skills.

### Why This Project?

- **Always demo-able** - Uses historical data, no dependency on live game schedules
- **Deep insights** - Pattern detection tells better stories than raw stats
- **Full-stack AWS** - DynamoDB, Lambda, Kinesis, API Gateway, Bedrock, and more

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React, TypeScript, Tailwind CSS |
| **API** | AWS API Gateway, Lambda (Python) |
| **Database** | DynamoDB (single-table design) |
| **Streaming** | Kinesis (play-by-play processing) |
| **Storage** | S3 (raw game data) |
| **AI** | AWS Bedrock (Claude) for insights |
| **Data Source** | ESPN public API |

---

## Project Structure

```
courtvision-ai/
├── frontend/       # React application
├── backend/        # AWS Lambda functions
├── scripts/        # Data collection & analysis tools
├── docs/           # Documentation
└── README.md
```

---

## Features

- **Season Game Library** - Browse all Iowa games by season
- **Pattern Detection** - Scoring runs, hot streaks, momentum shifts
- **Interactive Game Replay** - Watch games unfold play-by-play
- **Player Dashboards** - Season stats, shot charts, trends
- **AI Commentary** - Game summaries and insights via Bedrock

---

## Current Status

🚧 **In Development**

- [x] Project structure
- [ ] AWS infrastructure setup
- [ ] Data collection scripts
- [ ] Backend API
- [ ] Frontend MVP
- [ ] AI insights integration

---

## Getting Started

*Setup instructions coming soon*

---

## Documentation

See the `/docs` folder for:
- Project blueprint
- Implementation timeline
- Architecture decisions

---

## License

This project is for educational and portfolio purposes.