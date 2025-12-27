# Snow Clicker - Telegram Mini App (stub)

This folder contains placeholders for the Telegram bot and Supabase registration flow.

## Setup (placeholders)

1) Copy `.env.example` to `.env`
2) Fill values:
   - TELEGRAM_BOT_TOKEN
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY
   - WEBAPP_URL

## Python bot (aiogram)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

## Supabase

Run SQL in `supabase/schema.sql`, then optional `supabase/seed.sql`.

The Mini App uses placeholders in `script.js` and will switch to local mock mode
if `SUPABASE_URL` contains `YOUR_`.
