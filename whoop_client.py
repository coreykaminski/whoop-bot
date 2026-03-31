"""
Whoop API Client
Handles OAuth token management and data fetching from Whoop v2 API.
"""

import json
import os
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_URL = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
TOKEN_FILE = Path(__file__).parent / "tokens.json"


class WhoopClient:
    def __init__(self):
        self.client_id = os.getenv("WHOOP_CLIENT_ID")
        self.client_secret = os.getenv("WHOOP_CLIENT_SECRET")
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()

    def _load_tokens(self):
        """Load saved tokens from disk."""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE) as f:
                data = json.load(f)
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.token_expiry = data.get("token_expiry", "")

    def _save_tokens(self, token_data: dict):
        """Save tokens to disk."""
        expires_in = token_data.get("expires_in", 3600)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        save_data = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", self.refresh_token),
            "token_expiry": expiry.isoformat(),
        }
        with open(TOKEN_FILE, "w") as f:
            json.dump(save_data, f, indent=2)
        self.access_token = save_data["access_token"]
        self.refresh_token = save_data["refresh_token"]
        self.token_expiry = save_data["token_expiry"]

    def refresh_access_token(self):
        """Use refresh token to get a new access token."""
        if not self.refresh_token:
            raise Exception("No refresh token available. Run auth_whoop.py first.")

        resp = requests.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "offline read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement",
        })
        resp.raise_for_status()
        token_data = resp.json()
        self._save_tokens(token_data)
        print("✅ Token refreshed successfully")

    def _headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make authenticated GET request, refreshing token if needed."""
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, headers=self._headers(), params=params)

        if resp.status_code == 401:
            print("🔄 Token expired, refreshing...")
            self.refresh_access_token()
            resp = requests.get(url, headers=self._headers(), params=params)

        resp.raise_for_status()
        return resp.json()

    def _get_with_fallbacks(self, endpoints: list[str], params: dict = None) -> dict:
        """Try multiple endpoint variants; continue only on 404."""
        last_404_error = None
        for endpoint in endpoints:
            try:
                return self._get(endpoint, params=params)
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code == 404:
                    last_404_error = exc
                    continue
                raise

        tried = ", ".join(endpoints)
        if last_404_error:
            raise Exception(f"No matching Whoop endpoint found. Tried: {tried}") from last_404_error
        raise Exception(f"No endpoints configured for request. Tried: {tried}")

    def get_profile(self) -> dict:
        """Get user profile."""
        return self._get("/v2/user/profile/basic")

    def get_body_measurements(self) -> dict:
        """Get body measurements."""
        return self._get("/v2/user/measurement/body")

    def get_recovery(self, limit: int = 7) -> dict:
        """Get recent recovery data."""
        return self._get_with_fallbacks(
            [
                "/v2/activity/recovery",
                "/v2/recovery",
                "/v1/activity/recovery",
                "/v1/recovery",
                # Some API versions expose recovery inside cycle records.
                "/v2/cycle",
                "/v1/activity/cycle",
                "/v1/cycle",
            ],
            params={"limit": limit},
        )

    def get_sleep(self, limit: int = 7) -> dict:
        """Get recent sleep data."""
        return self._get_with_fallbacks(
            [
                "/v2/activity/sleep",
                "/v2/sleep",
                "/v1/activity/sleep",
                "/v1/sleep",
            ],
            params={"limit": limit},
        )

    def get_cycles(self, limit: int = 7) -> dict:
        """Get recent physiological cycles (strain)."""
        return self._get("/v2/cycle", params={"limit": limit})

    def get_workouts(self, limit: int = 7) -> dict:
        """Get recent workouts."""
        return self._get_with_fallbacks(
            [
                "/v2/activity/workout",
                "/v2/workout",
                "/v1/activity/workout",
                "/v1/workout",
            ],
            params={"limit": limit},
        )

    def get_daily_summary(self) -> dict:
        """
        Pull all relevant data for a daily health briefing.
        Gets the last 7 days so Claude can spot trends.
        """
        print("📡 Fetching Whoop data...")

        data = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "profile": self.get_profile(),
            "body": self.get_body_measurements(),
            "recovery": self.get_recovery(limit=7),
            "sleep": self.get_sleep(limit=7),
            "cycles": self.get_cycles(limit=7),
            "workouts": self.get_workouts(limit=14),
        }

        print(f"✅ Got {len(data['recovery'].get('records', []))} recovery records, "
              f"{len(data['sleep'].get('records', []))} sleep records, "
              f"{len(data['workouts'].get('records', []))} workouts")

        return data
