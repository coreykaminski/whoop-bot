"""
Whoop Daily Health Bot
Pulls Whoop data → Analyzes with Claude → Sends to Telegram

Usage:
    python3 main.py           # Normal daily briefing
    python3 main.py --test    # Test mode (prints to console, no Telegram)
"""

import sys
import json
from dotenv import load_dotenv

load_dotenv()

from whoop_client import WhoopClient
from claude_analyzer import analyze_whoop_data
from telegram_sender import send_telegram_message


def _build_test_fallback_briefing(data: dict) -> str:
    """Build a minimal local briefing when Claude is unavailable in test mode."""
    recovery_count = len(data.get("recovery", {}).get("records", []))
    sleep_count = len(data.get("sleep", {}).get("records", []))
    cycle_count = len(data.get("cycles", {}).get("records", []))
    workout_count = len(data.get("workouts", {}).get("records", []))
    return (
        "Claude API unavailable, but Whoop fetch is working.\n\n"
        f"- Recovery records: {recovery_count}\n"
        f"- Sleep records: {sleep_count}\n"
        f"- Cycle records: {cycle_count}\n"
        f"- Workout records: {workout_count}\n\n"
        "Next step: add Anthropic credits, then run `python3 main.py`."
    )


def run_daily_briefing(test_mode: bool = False) -> bool:
    try:
        # 1. Pull Whoop data
        whoop = WhoopClient()
        data = whoop.get_daily_summary()

        # 2. Analyze with Claude
        try:
            briefing = analyze_whoop_data(data)
        except Exception as e:
            if test_mode and "credit balance is too low" in str(e).lower():
                briefing = _build_test_fallback_briefing(data)
                print("⚠️ Claude credits unavailable; using local test briefing.")
            else:
                raise

        if test_mode:
            print("\n" + "=" * 60)
            print("DAILY HEALTH BRIEFING (TEST MODE)")
            print("=" * 60)
            print(briefing)
            print("=" * 60)

            # Also save raw data for debugging
            with open("last_whoop_data.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
            print("\n📄 Raw data saved to last_whoop_data.json")
        else:
            # 3. Send via Telegram
            success = send_telegram_message(briefing)
            if not success:
                print("❌ Failed to send Telegram message")
                return False

        print("\n🎉 Done!")
        return True

    except Exception as e:
        error_msg = f"❌ Whoop Bot Error: {str(e)}"
        print(error_msg)

        # Try to notify via Telegram even on error
        if not test_mode:
            try:
                send_telegram_message(f"⚠️ Your Whoop health bot encountered an error:\n\n{str(e)}")
            except Exception:
                pass

        return False


def main():
    test_mode = "--test" in sys.argv
    success = run_daily_briefing(test_mode=test_mode)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
