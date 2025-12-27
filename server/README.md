# Snow Clicker - Telegram Mini App (stub)

This folder contains placeholders for the Telegram bot and Supabase registration flow.

## Setup (placeholders)

1) Copy `.env.example` to `.env`
2) Fill values:
   - TELEGRAM_BOT_TOKEN
   - SUPABASE_URL
   - SUPABASE_ANON_KEY

## Python bot (aiogram)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

Configure the Mini App URL in BotFather so users open it from the bot меню.

Note: using the publishable key requires RLS policies in Supabase to allow
inserts/updates to `users` for the bot requests.

## Supabase

Run SQL in `supabase/schema.sql`, then optional `supabase/seed.sql`.

The Mini App uses placeholders in `script.js` and will switch to local mock mode
if `SUPABASE_URL` contains `YOUR_`.
