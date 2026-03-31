"""
Telegram Sender
Sends messages via Telegram Bot API.
"""

import os
import requests


def send_telegram_message(text: str) -> bool:
    """Send a message to your Telegram chat via your bot."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise Exception("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Split long messages (Telegram limit is 4096 chars)
    if len(text) > 4096:
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
    else:
        chunks = [text]

    for chunk in chunks:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
        })

        if resp.status_code != 200:
            # Retry without markdown if formatting fails
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": chunk,
            })

        if resp.status_code != 200:
            print(f"❌ Telegram error: {resp.text}")
            return False

    print("✅ Telegram message sent!")
    return True
