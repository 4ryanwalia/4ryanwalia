#!/usr/bin/env python3
"""One-time helper: trade a Spotify login for a long-lived refresh token,
then load it into both places that need it.

Run it once on your own machine and never again. You log in to Spotify in
your own browser; this script never sees a password. By default it hands the
resulting credentials straight to `gh secret set` and `vercel env add` over
stdin, so the token is never printed, never written to disk, and never lands
in shell history.

Two destinations because there are two renderers:

  * Vercel  — the live endpoint the README points at, which asks Spotify at
              the moment someone loads the profile.
  * GitHub  — the Action that renders the same card into ./assets, kept as a
              fallback if the endpoint ever has to be abandoned.

Stdlib only, like the card renderer — the client secret you type goes to
accounts.spotify.com and nowhere else.

    python scripts/get_refresh_token.py

Register this exact redirect URI on your Spotify app first:

    http://127.0.0.1:8888/callback
"""

from __future__ import annotations

import base64
import http.server
import json
import os
import secrets
import shutil
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from getpass import getpass

REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-currently-playing user-read-recently-played user-read-playback-state"
AUTH = "https://accounts.spotify.com/authorize"
TOKEN = "https://accounts.spotify.com/api/token"
CTX = ssl.create_default_context()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_DIR = os.path.join(ROOT, "spotify-live")
# The project's stable production alias. Vercel also gives every deployment its
# own immutable URL, but those change on each push; this is the one the README
# is allowed to hardcode.
LIVE_CARD = "https://spotify-live-seven.vercel.app/card.svg"

NAMES = ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN")

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

    print("\nGot a refresh token.\n")
    answer = input(
        "Push all three into Vercel and the repo secrets, and redeploy the\n"
        "live endpoint, without printing them anywhere? [Y/n]: "
    ).strip().lower()

    if answer in ("", "y", "yes"):
        return store(client_id, client_secret, token)

    # Fallback for anyone without gh. Printing a live credential to a terminal
    # puts it in scrollback and shell history, so it is not the default.
    print("\n" + "=" * 62)
    print("SPOTIFY_REFRESH_TOKEN")
    print(token)
    print("=" * 62)
    print("\nStore it as a repository secret, then clear your scrollback.\n")
    return 0


def run(exe: str, *args, **kw) -> subprocess.CompletedProcess:
    """Invoke a CLI by absolute path.

    Windows ships `vercel` as a .cmd shim, and CreateProcess cannot execute one
    directly, so a bare ["vercel", ...] raises WinError 193. Resolving through
    shutil.which honours PATHEXT, and a shim gets handed to cmd.exe. Never
    shell=True: these calls carry a live credential on stdin and a shell would
    put the surrounding command line in reach of quoting bugs.
    """
    path = shutil.which(exe)
    if not path:
        raise FileNotFoundError(exe)
    argv = [path, *args]
    if os.name == "nt" and path.lower().endswith((".cmd", ".bat")):
        argv = ["cmd", "/c", *argv]
    return subprocess.run(argv, capture_output=True, **kw)


def store(client_id: str, client_secret: str, token: str) -> int:
    """Hand each value to `gh` and `vercel` over stdin.

    Over stdin rather than an argument on purpose: an argument is visible in
    the process list to anything else running on the machine, and stdin is not.
    """
    pairs = tuple(zip(NAMES, (client_id, client_secret, token)))

    repo = input("Repository [4ryanwalia/4ryanwalia]: ").strip() or "4ryanwalia/4ryanwalia"
    print("\ngithub — fallback Action")
    for name, value in pairs:
        proc = run("gh", "secret", "set", name, "--repo", repo, input=value.encode())
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="replace").strip()
            print(f"  ! failed to set {name}: {err}", file=sys.stderr)
            print("    Is gh installed and authenticated? Try: gh auth status",
                  file=sys.stderr)
            return 1
        print(f"  set {name}")

    if vercel(pairs) != 0:
        return 1

    print("\nAll set. Nothing was printed and nothing was written to disk.")
    return 0


def vercel(pairs) -> int:
    """Load the same three values into the live endpoint and redeploy.

    Vercel bakes environment variables in at build time, so setting them
    without a redeploy leaves the running function exactly as unconfigured as
    it was.
    """
    print("\nvercel — live endpoint")
    if not shutil.which("vercel"):
        print("  ! vercel CLI not found. Install it with:  npm i -g vercel",
              file=sys.stderr)
        print("    Then re-run this script, or set the three variables by hand.",
              file=sys.stderr)
        return 1
    if not os.path.isdir(os.path.join(LIVE_DIR, ".vercel")):
        print(f"  ! {LIVE_DIR} is not linked to a Vercel project.", file=sys.stderr)
        print("    Run `vercel link` in that directory first.", file=sys.stderr)
        return 1

    for name, value in pairs:
        # Remove first: `env add` refuses to overwrite, and a re-run of this
        # script after a rotated secret is the normal case, not an edge one.
        run("vercel", "env", "rm", name, "production", "--yes", cwd=LIVE_DIR)
        proc = run("vercel", "env", "add", name, "production",
                   cwd=LIVE_DIR, input=value.encode())
        if proc.returncode != 0:
            err = proc.stderr.decode(errors="replace").strip()
            print(f"  ! failed to set {name}: {err}", file=sys.stderr)
            return 1
        print(f"  set {name}")

    print("  redeploying so the build picks them up…")
    proc = run("vercel", "--prod", "--yes", cwd=LIVE_DIR)
    if proc.returncode != 0:
        print("  ! deploy failed: " + proc.stderr.decode(errors="replace").strip(),
              file=sys.stderr)
        return 1

    return verify()


def verify() -> int:
    """Confirm the endpoint now answers with a real card.

    Worth the extra few seconds: the failure this catches -- credentials set
    but not picked up -- is invisible from the terminal and very visible on
    the profile.
    """
    print("  checking " + LIVE_CARD)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(LIVE_CARD, timeout=20, context=CTX) as r:
                head = r.read(400).decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            head = f"(unreachable: {exc})"
        if "AWAITING CREDENTIALS" not in head and "<svg" in head:
            label = head.split("aria-label=\"", 1)[-1].split(":", 1)[0]
            print(f"  live — the card reads {label!r}")
            return 0
        if attempt < 5:
            time.sleep(5)

    print("  ! the endpoint still reports it has no credentials.", file=sys.stderr)
    print("    Check them with:  vercel env ls production", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
