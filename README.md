# ⚽ Career Quiz

A mobile-first web app where players create parties, invite friends via WhatsApp, and compete daily to identify football players from their career history.

## Quick Start

### 1. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → paste and run `supabase/migration.sql`
3. Copy your **Project URL** and **anon key** from Settings → API

### 2. Configure Environment

Create a `.env` file:
```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

### 3. Install and Run

```bash
npm install
npm run dev
```

### 4. Populate Players (required to play)

```bash
cd pipeline
pip install requests python-dotenv

# Create .env with service key
echo "SUPABASE_URL=https://xxx.supabase.co" > .env
echo "SUPABASE_SERVICE_KEY=eyJ..." >> .env

# Run the pipeline
python scrape_players.py
```

### 5. Deploy to Netlify

```bash
# Push to GitHub first, then:
# 1. Connect repo to Netlify
# 2. Set environment variables in Netlify dashboard
# 3. Deploy!
```

## Architecture

```
career-quiz/
├── src/
│   ├── App.jsx           # Main React app
│   └── lib/supabase.js   # Supabase client
├── supabase/
│   └── migration.sql     # Database schema
├── pipeline/
│   └── scrape_players.py # Data pipeline
└── netlify.toml          # Netlify config
```

## Features

- 🎮 Daily quiz rounds with progressive club reveals
- 👥 Create parties and invite friends via WhatsApp
- 🏆 Real-time leaderboards
- 📱 Mobile-first design
- ⚡ Supabase Realtime for live updates

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: Supabase (Postgres + Realtime)
- **Data**: Wikidata + Wikipedia
- **Hosting**: Netlify
