"""
Whoop OAuth Authentication (one-time setup)
Runs a local server to handle the OAuth callback and save your tokens.
"""

import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
REDIRECT_URI = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback")
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
SCOPES = "offline read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family: sans-serif; text-align: center; padding-top: 100px;">
                <h1>Whoop Connected!</h1>
                <p>You can close this window and go back to the terminal.</p>
                </body></html>
            """)
        else:
            error = params.get("error", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Error: {error}</h1></body></html>".encode())

    def log_message(self, format, *args):
        pass  # Suppress server logs


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET in your .env file first!")
        return

    # Build authorization URL
    auth_params = (
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state=whoop_auth_bot"
    )
    full_auth_url = AUTH_URL + auth_params

    print("🔐 Opening browser for Whoop authorization...")
    print(f"\nIf browser doesn't open, go to:\n{full_auth_url}\n")
    webbrowser.open(full_auth_url)

    # Start local server to catch the callback
    port = int(REDIRECT_URI.split(":")[-1].split("/")[0])
    server = HTTPServer(("localhost", port), CallbackHandler)
    print(f"⏳ Waiting for authorization callback on port {port}...")

    while auth_code is None:
        server.handle_request()

    server.server_close()

    # Exchange auth code for tokens
    print("🔄 Exchanging code for tokens...")
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    })

    if resp.status_code != 200:
        print(f"❌ Token exchange failed: {resp.text}")
        return

    token_data = resp.json()

    # Save tokens
    from datetime import datetime, timedelta, timezone
    expiry = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

    save_data = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_expiry": expiry.isoformat(),
    }

    with open("tokens.json", "w") as f:
        json.dump(save_data, f, indent=2)

    print("\n✅ Authentication successful! Tokens saved to tokens.json")
    print("   Your bot is ready to use. Run: python3 main.py")


if __name__ == "__main__":
    main()
