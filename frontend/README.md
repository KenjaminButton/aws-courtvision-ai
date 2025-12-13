# CourtVision AI - Frontend

Iowa Hawkeyes Basketball Analytics Dashboard built with React + TypeScript + Tailwind CSS.

## 🏀 Features

- **Season Game List** - Browse all Iowa Hawkeyes games with win/loss filtering
- **Game Detail View** - Score summary, patterns detected, box scores
- **Interactive Replay** - Watch play-by-play at 1x, 3x, or 10x speed
- **Pattern Detection** - Visual display of scoring runs and hot streaks
- **Iowa Branding** - Black and gold theme with athletic typography

## 🛠 Tech Stack

- **React 18** - UI Framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router v6** - Client-side routing
- **Recharts** - Data visualization
- **Lucide Icons** - Beautiful icons

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Header.tsx       # Navigation header
│   ├── GameCard.tsx     # Game list items
│   ├── ScoreBoard.tsx   # Score display
│   ├── PlayByPlay.tsx   # Play list & replay controls
│   ├── PatternBadge.tsx # Pattern display
│   ├── BoxScore.tsx     # Player statistics table
│   └── LoadingStates.tsx# Loading, error, empty states
├── pages/              # Page components
│   ├── HomePage.tsx    # Season games list
│   └── GamePage.tsx    # Individual game view
├── hooks/              # Custom React hooks
│   └── useApi.ts       # Data fetching hooks
├── services/           # API layer
│   └── api.ts          # API client
├── types/              # TypeScript types
│   └── index.ts        # Shared type definitions
├── App.tsx             # Root component
├── main.tsx            # Entry point
└── index.css           # Tailwind + custom styles
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Your API Gateway URL (from SAM deployment)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local and add your API URL
# VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

### Deploy to S3 + CloudFront

```bash
# Build the app
npm run build

# Sync to S3 bucket
aws s3 sync dist/ s3://courtvision-frontend-ACCOUNT_ID --delete

# Invalidate CloudFront cache (if using)
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## 🎨 Design System

### Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Iowa Gold | `#FFCD00` | Primary accent, highlights |
| Iowa Black | `#000000` | Background, text |
| Gold Dark | `#E5B800` | Hover states |
| Gold Light | `#FFE066` | Light accents |

### Typography

- **Display Font**: Bebas Neue (athletic headlines)
- **Body Font**: Inter (readable body text)
- **Mono Font**: JetBrains Mono (scores, stats)

### CSS Classes

```css
/* Iowa-themed button */
.btn-iowa { ... }
.btn-iowa-outline { ... }

/* Game cards */
.game-card { ... }

/* Score display */
.score-display { ... }

/* Pattern badges */
.pattern-badge { ... }

/* Stats table */
.stats-table { ... }
```

## 📡 API Integration

The frontend expects these API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/games` | GET | List games (query: `?season=2025`) |
| `/games/{gameId}` | GET | Game details with boxscore |
| `/games/{gameId}/plays` | GET | Play-by-play data |

### Adding Your API URL

1. Copy `.env.example` to `.env.local`
2. Update `VITE_API_URL` with your API Gateway URL
3. Restart the dev server

```env
VITE_API_URL=https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

## 🧩 Adding New Components

1. Create component in `src/components/`
2. Export from `src/components/index.ts`
3. Import where needed:

```tsx
import { GameCard, ScoreBoard } from '../components';
```

## 📱 Responsive Design

The app is fully responsive:
- **Mobile**: Single column, compact cards
- **Tablet**: 2-column grid
- **Desktop**: 3-column grid, full stats tables

## 🔧 Configuration

### Tailwind Config

Custom theme values are in `tailwind.config.js`:
- Iowa colors
- Athletic fonts
- Custom animations

### TypeScript Config

Strict mode enabled with path aliases:
```json
{
  "paths": {
    "@/*": ["src/*"]
  }
}
```

## 📝 Next Steps

1. [ ] Add shot chart visualization
2. [ ] Implement player dashboard page
3. [ ] Add season stats aggregation
4. [ ] Connect real pattern detection API
5. [ ] Add loading skeletons to all pages
6. [ ] Implement search/filter functionality

## 🐛 Troubleshooting

### API calls failing?
- Check `.env.local` has correct API URL
- Verify CORS is enabled on API Gateway
- Check browser console for errors

### Styles not loading?
- Run `npm install` to ensure Tailwind is installed
- Check `tailwind.config.js` content paths

### Build errors?
- Run `npm run lint` to check for TypeScript errors
- Ensure all dependencies are installed

## 📄 License

MIT License - Built for the Hawkeyes! 🏀
