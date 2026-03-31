# Whoop → Claude → Telegram Daily Health Bot

An automated daily health briefing that pulls your Whoop data, analyzes it with Claude (Opus/Sonnet), and sends you a Telegram message every morning.

## Architecture

```
[Whoop API] → [Python Script] → [Claude API] → [Telegram Bot] → You
                    ↑
            [Cron / Scheduler]
```

## Setup (15 min)

### 1. Whoop API Credentials

1. Go to https://developer.whoop.com and sign in with your Whoop account
2. Create a **Team** (required first time)
3. Create an **App** with these settings:
   - Name: "Daily Health Bot" (anything you want)
   - Redirect URI: `http://localhost:8080/callback`
   - Scopes: Select ALL of these:
     - `read:recovery`
     - `read:cycles`
     - `read:sleep`
     - `read:workout`
     - `read:profile`
     - `read:body_measurement`
     - `offline` (for refresh tokens)
4. Save your **Client ID** and **Client Secret**

### 2. Telegram Bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Save the **Bot Token** BotFather gives you
4. Message your new bot (send it anything like "hi")
5. Run: `python3 get_telegram_chat_id.py` to get your Chat ID

### 3. Anthropic API Key

1. Go to https://console.anthropic.com
2. Create an API key
3. Save it

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Authenticate with Whoop (one-time)

```bash
python3 auth_whoop.py
```

This opens a browser for you to log in to Whoop and authorize the app. Your tokens are saved to `tokens.json` and auto-refresh.

### 7. Test It

```bash
python3 main.py
```

You should get a Telegram message with your daily health briefing!

### 8. Automate (Cron)

Add to your crontab (`crontab -e`):

```
# Run every morning at 8am
0 8 * * * cd /path/to/whoop-telegram-bot && python3 main.py >> bot.log 2>&1
```

Or deploy to Railway / AWS Lambda / any VPS with a scheduler.

## What You Get

Your daily Telegram message includes:
- **Recovery Score** analysis with context
- **Sleep** quality breakdown (RHR, HRV, duration, efficiency)
- **Strain** from yesterday with workout details
- **Trend alerts** (e.g., declining HRV, elevated RHR → possible illness)
- **Actionable recommendations** (training intensity, sleep tips, supplement suggestions)

## Files

| File | Purpose |
|------|---------|
| `main.py` | Main script — pulls data, analyzes, sends message |
| `whoop_client.py` | Whoop API client with auto token refresh |
| `claude_analyzer.py` | Sends data to Claude for analysis |
| `telegram_sender.py` | Sends message via Telegram bot |
| `auth_whoop.py` | One-time OAuth flow to get tokens |
| `get_telegram_chat_id.py` | Helper to find your Telegram chat ID |
| `.env.example` | Template for your credentials |
