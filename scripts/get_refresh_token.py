#!/usr/bin/env python3
"""One-time helper: trade a Spotify login for a long-lived refresh token.

Run it once on your own machine, paste the result into a repository secret,
and never run it again. Stdlib only, like the card renderer — the client
secret you type here goes to accounts.spotify.com and nowhere else.

    python scripts/get_refresh_token.py

Register this exact redirect URI on your Spotify app first:

    http://127.0.0.1:8888/callback
"""

from __future__ import annotations

import base64
import http.server
import json
import secrets
import ssl
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from getpass import getpass

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-currently-playing user-read-recently-played user-read-playback-state"
AUTH = "https://accounts.spotify.com/authorize"
TOKEN = "https://accounts.spotify.com/api/token"
CTX = ssl.create_default_context()

result: dict = {}
done = threading.Event()


class Callback(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib naming
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        result.update({k: v[0] for k, v in query.items()})
        body = (
            b"<body style='background:#0a0f1a;color:#e8eef7;font:16px system-ui;"
            b"display:grid;place-items:center;height:100vh;margin:0'>"
            b"<div><h2 style='color:#34d399'>Authorised.</h2>"
            b"<p>Close this tab and look at your terminal.</p></div></body>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        done.set()

    def log_message(self, *args):  # keep the terminal clean
        pass


def main() -> int:
    client_id = input("Spotify Client ID: ").strip()
    client_secret = getpass("Spotify Client Secret (hidden): ").strip()
    if not (client_id and client_secret):
        print("Both values are required.", file=sys.stderr)
        return 1

    state = secrets.token_urlsafe(16)
    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": state,
        "show_dialog": "true",
    })

    server = http.server.HTTPServer(("127.0.0.1", 8888), Callback)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("\nOpening Spotify in your browser. If it does not open, visit:\n")
    print(url + "\n")
    webbrowser.open(url)

    if not done.wait(timeout=300):
        print("Timed out waiting for the redirect.", file=sys.stderr)
        return 1
    server.shutdown()

    if result.get("error"):
        print("Spotify refused: " + result["error"], file=sys.stderr)
        return 1
    if result.get("state") != state:
        # Guards against a stray request landing on the callback port.
        print("State mismatch — discarding this response.", file=sys.stderr)
        return 1

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": REDIRECT,
    }).encode()
    req = urllib.request.Request(TOKEN, data=body, headers={
        "Authorization": "Basic " + basic,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        payload = json.loads(r.read().decode())

    token = payload.get("refresh_token")
    if not token:
        print("No refresh token came back: " + json.dumps(payload), file=sys.stderr)
        return 1

    print("\n" + "=" * 62)
    print("SPOTIFY_REFRESH_TOKEN")
    print(token)
    print("=" * 62)
    print("\nStore it as a repository secret. Do not commit it, and do not")
    print("paste it anywhere that keeps history.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
