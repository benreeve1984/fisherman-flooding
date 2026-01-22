# Flood Pulse - Shabbington

A mobile-first web app for Shabbington village to track flood conditions and road passability.

## Features

- Live river level display from EA Thame Bridge station
- Rainfall totals (24/48/72h) from nearby stations
- Community-reported road status for two flood-prone entrances
- Data stored for future model training

## Tech Stack

- **Framework**: FastHTML (Python ASGI + HTMX)
- **Database**: Neon Postgres (via Vercel Marketplace)
- **Deployment**: Vercel

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your DATABASE_URL

# Run the app
python main.py
```

The app will be available at http://localhost:5001

## Environment Variables

- `DATABASE_URL` - Neon Postgres connection string
- `IP_SALT` - Random string for IP hashing (rate limiting)

## Deployment

1. Push to GitHub
2. Connect to Vercel
3. Add Neon Postgres integration from Vercel Marketplace
4. Add `IP_SALT` environment variable
5. Deploy

## Data Attribution

- River and flood data from Environment Agency real-time data API (Beta)
- Rainfall data from Environment Agency real-time data API (Beta)

## Disclaimer

Community-reported guidance only. Do not drive into floodwater.
