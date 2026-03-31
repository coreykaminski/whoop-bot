"""
Railway scheduler entrypoint.
Runs the Whoop briefing at 10:00 AM and 10:00 PM America/New_York.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from main import run_daily_briefing


def run_job():
    print("⏰ Scheduled run started")
    ok = run_daily_briefing(test_mode=False)
    if ok:
        print("✅ Scheduled run finished successfully")
    else:
        print("❌ Scheduled run failed")


def main():
    scheduler = BlockingScheduler(timezone="America/New_York")
    scheduler.add_job(
        run_job,
        CronTrigger(hour="10,22", minute=0, timezone="America/New_York"),
        id="whoop_daily_briefing",
        replace_existing=True,
    )
    print("🗓️ Scheduler running for 10:00 and 22:00 America/New_York")
    scheduler.start()


if __name__ == "__main__":
    main()
