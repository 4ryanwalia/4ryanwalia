#!/usr/bin/env python3
"""Render a live "now playing" card from the Spotify Web API.

Deliberately dependency-free: the only things that ever hold the refresh token
are GitHub Actions and the standard library. No pip install, no third-party
service, no supply chain to audit.

Writes:
  assets/spotify-dark.svg   card for dark-mode readers
  assets/spotify-light.svg  card for light-mode readers
  assets/spotify-state.json fingerprint, so an unchanged track makes no commit
and rewrites the block between SPOTIFY:START / SPOTIFY:END in README.md.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
README = os.path.join(ROOT, "README.md")
STATE = os.path.join(ASSETS, "spotify-state.json")

TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"

UA = "myrecon-profile-card/1.0 (+https://github.com/4ryanwalia)"
CTX = ssl.create_default_context()

W, H = 480, 170
ART = 116

THEMES = {
    "dark": {
        "card": "#111a2b", "border": "#1f2b42",
        "text": "#e8eef7", "dim": "#9aabc4", "mute": "#7d8aa3",
        "accent": "#4a8bf7", "track": "#22304c", "ok": "#34d399",
        "warn": "#f59e0b", "logo_fg": "#0a0f1a",
    },
    "light": {
        "card": "#f7f9fd", "border": "#e2e8f0",
        "text": "#0f172a", "dim": "#475569", "mute": "#5f6f86",
        "accent": "#2563eb", "track": "#dde5f0", "ok": "#047857",
        "warn": "#a84d08", "logo_fg": "#ffffff",
    },
}

FONT = "ui-sans-serif,system-ui,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# ---------------------------------------------------------------- text sizing

_NARROW = set("ijlt!|.,;:()[]{}/ ")
_NARROW.update(["'", "`", "\\"])
_WIDE = set("MWmw@%")


def text_width(s: str, size: float) -> float:
    """Approximate rendered width. Good enough to decide where to truncate."""
    total = 0.0
    for ch in s:
        if ch in _NARROW:
            total += 0.34
        elif ch in _WIDE:
            total += 0.90
        elif ch.isupper() or ch.isdigit():
            total += 0.64
        else:
            total += 0.545
    return total * size


def fit(s: str, size: float, max_w: float) -> str:
    if text_width(s, size) <= max_w:
        return s
    while s and text_width(s + "…", size) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


# ------------------------------------------------------------------- spotify

def post_form(url: str, data: dict, headers: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={**headers, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return json.loads(r.read().decode())


def get_json(url: str, token: str):
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + token, "User-Agent": UA}
    )
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            if r.status == 204:
                return None
            raw = r.read()
            return json.loads(raw.decode()) if raw.strip() else None
    except urllib.error.HTTPError as e:
        if e.code in (204, 404):
            return None
        raise


def access_token(cid: str, secret: str, refresh: str) -> str:
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    out = post_form(
        TOKEN_URL,
        {"grant_type": "refresh_token", "refresh_token": refresh},
        {"Authorization": "Basic " + basic,
         "Content-Type": "application/x-www-form-urlencoded"},
    )
    return out["access_token"]


def fetch_art(url: str):
    """Inline the cover as a data URI. An SVG loaded through an <img> tag
    renders in the browser's restricted static mode, which blocks every external
    fetch it attempts, so embedding is the only thing that works."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
            blob = r.read()
        if len(blob) > 700_000:
            return None
        mime = "image/png" if blob[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        return "data:" + mime + ";base64," + base64.b64encode(blob).decode()
    except Exception as e:  # art is decorative; never fail the run over it
        print("  ! album art unavailable: " + str(e), file=sys.stderr)
        return None


def pick_art(images: list) -> str:
    """Prefer ~300px: sharp enough to look right, small enough to inline."""
    if not images:
        return ""
    ranked = sorted(images, key=lambda i: abs((i.get("width") or 640) - 300))
    return ranked[0].get("url", "")


def ms(v) -> str:
    v = max(0, int(v or 0)) // 1000
    return f"{v // 60}:{v % 60:02d}"


def ago(iso: str) -> str:
    try:
        then = datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except Exception:
        return ""
    secs = (datetime.now(timezone.utc) - then).total_seconds()
    if secs < 90:
        return "just now"
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def collect() -> dict:
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()

    if not (cid and secret and refresh):
        return {"state": "unconfigured"}

    token = access_token(cid, secret, refresh)

    now = get_json(NOW_URL, token)
    item = (now or {}).get("item")
    if item and item.get("type") == "track":
        return {
            "state": "playing" if (now or {}).get("is_playing") else "paused",
            "title": item.get("name", ""),
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "album": (item.get("album") or {}).get("name", ""),
            "art": pick_art((item.get("album") or {}).get("images", [])),
            "url": (item.get("external_urls") or {}).get("spotify", ""),
            "progress": (now or {}).get("progress_ms") or 0,
            "duration": item.get("duration_ms") or 0,
        }

    recent = get_json(RECENT_URL, token) or {}
    items = recent.get("items") or []
    if items:
        t = items[0].get("track") or {}
        return {
            "state": "recent",
            "title": t.get("name", ""),
            "artist": ", ".join(a["name"] for a in t.get("artists", [])),
            "album": (t.get("album") or {}).get("name", ""),
            "art": pick_art((t.get("album") or {}).get("images", [])),
            "url": (t.get("external_urls") or {}).get("spotify", ""),
            "played_at": items[0].get("played_at", ""),
            "duration": t.get("duration_ms") or 0,
        }

    return {"state": "silent"}


# --------------------------------------------------------------------- render

def logo(x: float, y: float, c: dict) -> str:
    return (
        f'<g transform="translate({x},{y})">'
        '<circle r="10" fill="#1DB954"/>'
        f'<g stroke="{c["logo_fg"]}" stroke-width="1.7" stroke-linecap="round" fill="none">'
        '<path d="M-6.1,-3.4 Q0,-6.4 6.3,-2.3"/>'
        '<path d="M-5.1,0.3 Q0,-2.2 5.3,1.3"/>'
        '<path d="M-4.0,3.9 Q0,1.9 4.4,4.7"/>'
        "</g></g>"
    )


def equaliser(x: float, base: float, c: dict, live: bool) -> str:
    bars = []
    for i, h in enumerate([11, 16, 7, 13, 9]):
        bx = x + i * 5.5
        if not live:
            bars.append(
                f'<rect x="{bx}" y="{base - 4}" width="3" height="4" rx="1.5" fill="{c["mute"]}"/>'
            )
            continue
        dur = 0.72 + i * 0.17
        bars.append(
            f'<rect x="{bx}" y="{base - 4}" width="3" height="4" rx="1.5" fill="{c["ok"]}">'
            f'<animate attributeName="height" values="4;{h};6;{h - 3};4" '
            f'dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{base - 4};{base - h};{base - 6};'
            f'{base - h + 3};{base - 4}" dur="{dur}s" repeatCount="indefinite"/>'
            "</rect>"
        )
    return "".join(bars)


def card(d: dict, theme: str) -> str:
    c = THEMES[theme]
    state = d.get("state", "silent")
    live = state == "playing"
    col_x, col_w = 148.0, float(W - 148 - 20)

    if state == "unconfigured":
        label, label_fill = "AWAITING CREDENTIALS", c["warn"]
        title = "Spotify not wired up yet"
        artist = "add the three repo secrets - see SETUP.md"
        album = ""
    elif state == "silent":
        label, label_fill = "NO SIGNAL", c["mute"]
        title = "Nothing playing"
        artist = "and nothing in the recent history"
        album = ""
    elif live:
        label, label_fill = "NOW PLAYING", c["ok"]
        title, artist, album = d["title"], d["artist"], d["album"]
    elif state == "paused":
        label, label_fill = "PAUSED", c["warn"]
        title, artist, album = d["title"], d["artist"], d["album"]
    else:
        stamp = ago(d.get("played_at", ""))
        label = "LAST PLAYED · " + stamp if stamp else "LAST PLAYED"
        label_fill = c["mute"]
        title, artist, album = d["title"], d["artist"], d["album"]

    art_y = (H - ART) / 2
    art_uri = d.get("art_uri")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{esc(label)}: {esc(title)} by {esc(artist)}">',
        f"<title>{esc(label)} — {esc(title)} · {esc(artist)}</title>",
        "<defs>",
        f'<clipPath id="art"><rect x="20" y="{art_y}" width="{ART}" height="{ART}" rx="9"/></clipPath>',
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c["accent"]}" stop-opacity="0.30"/>'
        '<stop offset="1" stop-color="#1DB954" stop-opacity="0.18"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{c["card"]}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="none" stroke="{c["border"]}"/>',
    ]

    if art_uri:
        out.append(
            f'<image x="20" y="{art_y}" width="{ART}" height="{ART}" clip-path="url(#art)" '
            f'preserveAspectRatio="xMidYMid slice" href="{art_uri}"/>'
        )
    else:
        out.append(
            f'<rect x="20" y="{art_y}" width="{ART}" height="{ART}" rx="9" fill="url(#fade)"/>'
            f'<text x="{20 + ART / 2}" y="{art_y + ART / 2 + 12}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="34" fill="{c["mute"]}">♫</text>'
        )
    out.append(
        f'<rect x="20.5" y="{art_y + 0.5}" width="{ART - 1}" height="{ART - 1}" rx="9" '
        f'fill="none" stroke="{c["border"]}"/>'
    )

    out.append(logo(W - 34, 30, c))
    out.append(equaliser(col_x, 46, c, live))
    out.append(
        f'<text x="{col_x + 33}" y="46" font-family="{MONO}" font-size="10.5" '
        f'letter-spacing="0.09em" font-weight="700" fill="{label_fill}">{esc(label)}</text>'
    )
    out.append(
        f'<text x="{col_x}" y="74" font-family="{FONT}" font-size="15.5" font-weight="700" '
        f'fill="{c["text"]}">{esc(fit(title, 15.5, col_w))}</text>'
    )
    out.append(
        f'<text x="{col_x}" y="95" font-family="{FONT}" font-size="12.5" '
        f'fill="{c["dim"]}">{esc(fit(artist, 12.5, col_w))}</text>'
    )
    if album:
        out.append(
            f'<text x="{col_x}" y="113" font-family="{FONT}" font-size="11" '
            f'fill="{c["mute"]}">{esc(fit(album, 11, col_w))}</text>'
        )

    bar_x, bar_w, bar_y = col_x, 254.0, 132.0
    if state in ("playing", "paused"):
        dur = max(1, int(d.get("duration") or 1))
        pos = min(dur, int(d.get("progress") or 0))
        filled = bar_w * (pos / dur)
        out.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="4" rx="2" fill="{c["track"]}"/>'
            f'<rect x="{bar_x}" y="{bar_y}" width="{filled:.1f}" height="4" rx="2" fill="{c["accent"]}"/>'
        )
        if live:
            out.append(
                f'<circle cx="{bar_x + filled:.1f}" cy="{bar_y + 2}" r="3.5" fill="{c["accent"]}">'
                '<animate attributeName="r" values="3.5;4.6;3.5" dur="1.9s" repeatCount="indefinite"/>'
                "</circle>"
            )
        # The scheduler can leave this card sitting for half an hour. Without a
        # timestamp a frozen progress bar under a NOW PLAYING label asserts
        # something live that may be long over, so say when it was true.
        fetched = datetime.now(timezone.utc).strftime("%H:%M")
        out.append(
            f'<text x="{bar_x}" y="152" font-family="{MONO}" font-size="9.5" '
            f'fill="{c["mute"]}">{ms(pos)}</text>'
            f'<text x="{bar_x + bar_w / 2}" y="152" text-anchor="middle" '
            f'font-family="{MONO}" font-size="9" fill="{c["mute"]}">'
            f'as of {fetched} utc</text>'
            f'<text x="{bar_x + bar_w}" y="152" text-anchor="end" font-family="{MONO}" '
            f'font-size="9.5" fill="{c["mute"]}">{ms(dur)}</text>'
        )
    else:
        fetched = datetime.now(timezone.utc).strftime("%H:%M")
        out.append(
            f'<text x="{col_x}" y="140" font-family="{MONO}" font-size="9.5" '
            f'fill="{c["mute"]}">source: spotify web api · fetched {fetched} utc</text>'
        )

    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------- README

START = "<!-- SPOTIFY:START -->"
END = "<!-- SPOTIFY:END -->"


def readme_block(d: dict, stamp: str) -> str:
    state = d.get("state")
    if state == "playing":
        cap = "Playing right now"
    elif state == "paused":
        cap = "Paused mid-track"
    elif state == "recent":
        cap = "Last track played"
    elif state == "unconfigured":
        cap = "Feed not configured yet"
    else:
        cap = "Radio silence"

    alt = (cap + ": " + d.get("title", "") + " — " + d.get("artist", "")).strip(" :—")
    href = d.get("url") or "https://open.spotify.com/"
    return (
        START + "\n"
        "<!-- rewritten by .github/workflows/spotify.yml - edit the script, not this block -->\n"
        '<p align="center">\n'
        '  <a href="' + esc(href) + '">\n'
        "    <picture>\n"
        '      <source media="(prefers-color-scheme: dark)" '
        'srcset="./assets/spotify-' + stamp + '-dark.svg">\n'
        '      <source media="(prefers-color-scheme: light)" '
        'srcset="./assets/spotify-' + stamp + '-light.svg">\n'
        '      <img src="./assets/spotify-' + stamp + '-dark.svg" '
        'alt="' + esc(alt) + '" width="480">\n'
        "    </picture>\n"
        "  </a>\n"
        "</p>\n" + END
    )


def patch_readme(d: dict, stamp: str) -> bool:
    if not os.path.exists(README):
        return False
    with open(README, encoding="utf-8") as fh:
        text = fh.read()
    if START not in text or END not in text:
        print("  ! README markers missing; skipping README rewrite", file=sys.stderr)
        return False
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    updated = head + readme_block(d, stamp) + tail
    if updated == text:
        return False
    with open(README, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)
    return True


# ------------------------------------------------------------------------ run

def main() -> int:
    try:
        data = collect()
    except Exception as e:
        # Leave the last good card in place rather than replacing it with an
        # error state. A transient 502 should not blank the profile.
        print("spotify fetch failed: " + str(e), file=sys.stderr)
        return 0

    print("state=" + str(data.get("state")) + " track=" + repr(data.get("title", "-")))

    # The fingerprint ignores elapsed time on purpose: otherwise every run
    # during the same track would be a commit.
    fingerprint = json.dumps(
        {k: data.get(k) for k in ("state", "title", "artist", "album", "url")},
        sort_keys=True,
    )
    previous = ""
    previous_stamp = ""
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as fh:
                saved = json.load(fh)
            previous = saved.get("fingerprint", "")
            previous_stamp = saved.get("stamp", "")
        except Exception:
            previous = ""
            previous_stamp = ""

    if fingerprint == previous and os.path.exists(os.path.join(ASSETS, "spotify-dark.svg")):
        print("unchanged - nothing to commit")
        return 0

    # Never trade a real card for a placeholder. If the credentials go missing
    # -- a blanked secret, a revoked token -- the honest move is to leave the
    # last real reading in place and complain in the log, not to publish
    # "awaiting credentials" over a working profile.
    if data.get("state") == "unconfigured" and os.path.exists(
            os.path.join(ASSETS, "spotify-dark.svg")):
        print("credentials missing - keeping the existing card", file=sys.stderr)
        print("check SPOTIFY_CLIENT_ID / _SECRET / _REFRESH_TOKEN are non-empty",
              file=sys.stderr)
        return 1

    data["art_uri"] = fetch_art(data.get("art", ""))
    os.makedirs(ASSETS, exist_ok=True)

    # One filename per distinct card. GitHub's CDN caches by path and
    # ignores the query string, so "?v=" never busted anything; a path it
    # has not seen is the only thing it cannot answer from cache.
    stamp = hashlib.sha1(
        (fingerprint + str(time.time())).encode()).hexdigest()[:10]

    for theme in ("dark", "light"):
        svg = card(data, theme)
        # The stable name stays too, for anything linking straight at it.
        for path in (
                os.path.join(ASSETS, "spotify-" + theme + ".svg"),
                os.path.join(ASSETS, "spotify-" + stamp + "-" + theme + ".svg")):
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(svg)

    patch_readme(data, stamp)

    # Sweep the pair this one replaces, so the directory does not grow a
    # file per track played, forever.
    for theme in ("dark", "light"):
        stale = os.path.join(
            ASSETS, "spotify-" + previous_stamp + "-" + theme + ".svg")
        if previous_stamp and previous_stamp != stamp and os.path.exists(stale):
            os.remove(stale)

    with open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"fingerprint": fingerprint, "stamp": stamp,
                   "updated": int(time.time())}, fh, indent=2)
        fh.write("\n")

    print("card updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
