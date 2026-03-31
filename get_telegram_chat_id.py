"""
Get your Telegram Chat ID.
Run this AFTER you've messaged your bot at least once.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ Set TELEGRAM_BOT_TOKEN in your .env file first!")
        return

    print("📱 Fetching updates from your Telegram bot...")
    print("   (Make sure you've sent your bot a message first!)\n")

    resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
    data = resp.json()

    if not data.get("ok") or not data.get("result"):
        print("❌ No messages found. Send your bot a message on Telegram first, then run this again.")
        return

    # Get unique chats
    chats = {}
    for update in data["result"]:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        if chat.get("id"):
            chats[chat["id"]] = {
                "id": chat["id"],
                "name": chat.get("first_name", "") + " " + chat.get("last_name", ""),
                "username": chat.get("username", ""),
            }

    print("Found these chats:\n")
    for chat_id, info in chats.items():
        print(f"  Chat ID: {chat_id}")
        print(f"  Name:    {info['name'].strip()}")
        print(f"  User:    @{info['username']}")
        print()

    if len(chats) == 1:
        chat_id = list(chats.keys())[0]
        print(f"👆 Add this to your .env file:")
        print(f"   TELEGRAM_CHAT_ID={chat_id}")


if __name__ == "__main__":
    main()
