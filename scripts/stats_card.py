#!/usr/bin/env python3
"""Render the contribution graph and stats panel from GitHub's own API.

Written because github-readme-stats' public instance answers 503 more often
than it answers, and a profile that depends on someone else's free Vercel
deployment is a profile that is blank half the time.

Same rules as the Spotify card: standard library only, runs in Actions, reads
nothing it cannot verify.

Writes assets/contributions-{dark,light}.svg and assets/stats-{dark,light}.svg
"""

from __future__ import annotations

import html
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
GRAPHQL = "https://api.github.com/graphql"
CTX = ssl.create_default_context()
UA = "myrecon-profile-card/1.0 (+https://github.com/4ryanwalia)"

USER = os.environ.get("PROFILE_USER", "4ryanwalia")

THEMES = {
    "dark": {
        "card": "#111a2b", "border": "#1f2b42", "text": "#e8eef7",
        "dim": "#9aabc4", "mute": "#7d8aa3", "accent": "#4a8bf7",
        "grid": "#16223a", "rule": "#1f2b42", "ok": "#34d399",
        # Empty through busiest. Blue rather than GitHub's green so the graph
        # belongs to this page instead of looking borrowed from another one.
        "ramp": ["#16223a", "#1d3a66", "#2a5fb0", "#4a8bf7", "#8fbaff"],
    },
    "light": {
        "card": "#f7f9fd", "border": "#e2e8f0", "text": "#0f172a",
        "dim": "#475569", "mute": "#5f6f86", "accent": "#2563eb",
        "grid": "#e8eef7", "rule": "#e2e8f0", "ok": "#047857",
        "ramp": ["#e8eef7", "#bed3f5", "#7ba5e8", "#3d78d4", "#1e4fa3"],
    },
}

FONT = "ui-sans-serif,system-ui,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def fetch() -> dict:
    # PROFILE_TOKEN first: the workflow's built-in GITHUB_TOKEN can read repos
    # but is not guaranteed to be allowed at contributionsCollection. A PAT
    # with read:user is the documented way in, so prefer one when present.
    token = (os.environ.get("PROFILE_TOKEN", "").strip()
             or os.environ.get("GITHUB_TOKEN", "").strip())
    if not token:
        raise SystemExit("PROFILE_TOKEN or GITHUB_TOKEN is required.")
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers={
        "Authorization": "bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": UA,
    })
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        payload = json.loads(r.read().decode())
    if payload.get("errors"):
        raise SystemExit("GraphQL error: " + json.dumps(payload["errors"]))
    return payload["data"]["user"]


# ----------------------------------------------------------------- derivation

def streaks(days: list) -> tuple:
    """Longest and current run of consecutive days with at least one commit.

    Today counts as a grace day when it is still empty: it is not over yet, so
    a zero there should not read as a broken streak.
    """
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    tail = list(days)
    today = datetime.now(timezone.utc).date().isoformat()
    while tail and tail[-1]["date"] > today:
        tail.pop()
    if tail and tail[-1]["date"] == today and tail[-1]["count"] == 0:
        tail.pop()

    current = 0
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current += 1
    return longest, current


def digest(user: dict) -> dict:
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"],
               "weekday": d["weekday"]} for d in w["contributionDays"]]
             for w in cal["weeks"]]
    days = [d for w in weeks for d in w]

    langs: dict = {}
    stars = 0
    for repo in user["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            entry = langs.setdefault(name, {"size": 0, "color": edge["node"]["color"]})
            entry["size"] += edge["size"]
    ranked = sorted(langs.items(), key=lambda kv: -kv[1]["size"])[:5]
    total_bytes = sum(v["size"] for v in langs.values()) or 1

    weekday = [0] * 7
    monthly: dict = {}
    for day in days:
        weekday[day["weekday"]] += day["count"]
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]
    months = sorted(monthly.items())[-12:]

    longest, current = streaks(days)
    return {
        "weekday": weekday,
        "months": months,
        "weeks": weeks,
        "total": cal["totalContributions"],
        "active": sum(1 for d in days if d["count"] > 0),
        "span": len(days),
        "peak": max((d["count"] for d in days), default=0),
        "longest": longest,
        "current": current,
        "repos": user["repositories"]["totalCount"],
        "stars": stars,
        "followers": user["followers"]["totalCount"],
        "langs": [(n, v["size"], v["color"] or "#7d8aa3",
                   100.0 * v["size"] / total_bytes) for n, v in ranked],
    }


def level(count: int, peak: int) -> int:
    """Four filled bands. Thresholds scale to this account's own peak, so the
    graph reads the same whether the busiest day is 7 commits or 70."""
    if count <= 0:
        return 0
    if peak <= 1:
        return 4
    share = count / peak
    if share <= 0.25:
        return 1
    if share <= 0.5:
        return 2
    if share <= 0.75:
        return 3
    return 4


# ------------------------------------------------------------ pattern of life

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def rhythm_svg(d: dict, theme: str) -> str:
    """Which days the subject actually ships on, and how the year trended.

    Deliberately not a heatmap of the year: GitHub already draws that two
    sections further down the profile, and a second copy of it says nothing
    the first one did not. "Pattern of life" is the intelligence term for
    working out a subject's routine, which is exactly what this is.
    """
    c = THEMES[theme]
    W, H = 740, 238
    busiest = max(range(7), key=lambda i: d["weekday"][i])
    quietest = min(range(7), key=lambda i: d["weekday"][i])
    top = max(d["weekday"]) or 1

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Pattern of life: busiest '
        f'on {DAYS[busiest]}, quietest on {DAYS[quietest]}, with monthly volume '
        f'over the last year.">',
        "<title>Pattern of life</title>",
        "<defs>",
        f'<linearGradient id="fill-{theme}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{c["accent"]}" stop-opacity="0.34"/>'
        f'<stop offset="1" stop-color="{c["accent"]}" stop-opacity="0.02"/>'
        "</linearGradient>",
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{c["card"]}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="none" stroke="{c["border"]}"/>',
        f'<text x="20" y="28" font-family="{MONO}" font-size="11.5" '
        f'font-weight="700" letter-spacing="0.10em" fill="{c["accent"]}">'
        f"PATTERN OF LIFE</text>",
        f'<text x="{W - 20}" y="28" text-anchor="end" font-family="{MONO}" '
        f'font-size="10.5" fill="{c["mute"]}">derived from {d["span"]} days</text>',
        f'<line x1="372" y1="44" x2="372" y2="{H - 44}" stroke="{c["rule"]}"/>',
        f'<text x="20" y="52" font-family="{MONO}" font-size="9.5" '
        f'letter-spacing="0.08em" fill="{c["mute"]}">BY DAY OF WEEK</text>',
    ]

    for i, name in enumerate(DAYS):
        y = 72 + i * 21
        value = d["weekday"][i]
        width = max(3.0, 232 * value / top)
        shade = c["accent"] if i == busiest else c["ramp"][2]
        out.append(
            f'<text x="20" y="{y + 4}" font-family="{MONO}" font-size="10.5" '
            f'fill="{c["dim"] if i == busiest else c["mute"]}">{name}</text>'
            f'<rect x="56" y="{y - 5}" width="232" height="10" rx="5" '
            f'fill="{c["grid"]}"/>'
            f'<rect x="56" y="{y - 5}" width="{width:.1f}" height="10" rx="5" '
            f'fill="{shade}"/>'
            f'<text x="{352}" y="{y + 4}" text-anchor="end" font-family="{MONO}" '
            f'font-size="10" fill="{c["mute"]}">{value}</text>'
        )

    out.append(
        f'<text x="396" y="52" font-family="{MONO}" font-size="9.5" '
        f'letter-spacing="0.08em" fill="{c["mute"]}">MONTHLY VOLUME</text>'
    )

    months = d["months"] or [("", 0)]
    peak = max(v for _k, v in months) or 1
    left, right = 400.0, 716.0
    base, height = 186.0, 104.0
    step = (right - left) / max(1, len(months) - 1)
    pts = [(left + i * step, base - height * (v / peak))
           for i, (_k, v) in enumerate(months)]

    area = (f'M {pts[0][0]:.1f},{base} '
            + " ".join(f"L {x:.1f},{y:.1f}" for x, y in pts)
            + f" L {pts[-1][0]:.1f},{base} Z")
    line = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out.append(
        f'<line x1="{left}" y1="{base}" x2="{right}" y2="{base}" '
        f'stroke="{c["rule"]}"/>'
        f'<path d="{area}" fill="url(#fill-{theme})"/>'
        f'<path d="{line}" fill="none" stroke="{c["accent"]}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )
    for i, ((key, value), (x, y)) in enumerate(zip(months, pts)):
        if value == peak:
            out.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{c["accent"]}"/>'
                f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
                f'font-family="{MONO}" font-size="9.5" font-weight="700" '
                f'fill="{c["text"]}">{value}</text>'
            )
        if key and (i % 2 == 0 or i == len(months) - 1):
            out.append(
                f'<text x="{x:.1f}" y="{base + 14}" text-anchor="middle" '
                f'font-family="{MONO}" font-size="9" fill="{c["mute"]}">'
                f"{MONTHS[int(key[5:7]) - 1]}</text>"
            )

    out.append(
        f'<text x="20" y="{H - 16}" font-family="{MONO}" font-size="10" '
        f'fill="{c["mute"]}">busiest <tspan fill="{c["text"]}" font-weight="700">'
        f'{DAYS[busiest]}</tspan>  ·  quietest <tspan fill="{c["text"]}">'
        f'{DAYS[quietest]}</tspan>  ·  longest run <tspan fill="{c["text"]}">'
        f'{d["longest"]}d</tspan>  ·  current <tspan '
        f'fill="{c["ok"] if d["current"] else c["mute"]}">{d["current"]}d</tspan>'
        f"</text>"
    )
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- stats panel

def stats_svg(d: dict, theme: str) -> str:
    c = THEMES[theme]
    W, H = 740, 176

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="{d["total"]} contributions, '
        f'{d["repos"]} public repositories, {d["stars"]} stars, '
        f'{d["followers"]} followers.">',
        f"<title>Profile telemetry</title>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{c["card"]}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="none" stroke="{c["border"]}"/>',
        f'<text x="20" y="28" font-family="{MONO}" font-size="11.5" '
        f'font-weight="700" letter-spacing="0.10em" fill="{c["accent"]}">'
        f"TELEMETRY</text>",
        f'<line x1="372" y1="18" x2="372" y2="{H - 18}" stroke="{c["rule"]}"/>',
    ]

    tiles = (
        (d["total"], "contributions", 24, 76),
        (d["repos"], "public repos", 200, 76),
        (d["stars"], "stars earned", 24, 140),
        (d["longest"], "longest run (days)", 200, 140),
    )
    for value, label, x, y in tiles:
        out.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="30" '
            f'font-weight="800" fill="{c["text"]}">{value}</text>'
            f'<text x="{x}" y="{y + 17}" font-family="{MONO}" font-size="9.5" '
            f'letter-spacing="0.06em" fill="{c["mute"]}">{label.upper()}</text>'
        )

    out.append(
        f'<text x="396" y="48" font-family="{MONO}" font-size="9.5" '
        f'letter-spacing="0.08em" fill="{c["mute"]}">LANGUAGES BY VOLUME</text>'
    )
    bar_x, bar_w = 524, 148
    for i, (name, _size, colour, pct) in enumerate(d["langs"]):
        y = 70 + i * 22
        out.append(
            f'<text x="396" y="{y + 4}" font-family="{FONT}" font-size="11.5" '
            f'fill="{c["dim"]}">{esc(name)}</text>'
            f'<rect x="{bar_x}" y="{y - 5}" width="{bar_w}" height="8" rx="4" '
            f'fill="{c["grid"]}"/>'
            f'<rect x="{bar_x}" y="{y - 5}" width="{max(4.0, bar_w * pct / 100):.1f}" '
            f'height="8" rx="4" fill="{esc(colour)}"/>'
            f'<text x="{W - 20}" y="{y + 4}" text-anchor="end" font-family="{MONO}" '
            f'font-size="10" fill="{c["mute"]}">{pct:.0f}%</text>'
        )

    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------------ run

def main() -> int:
    try:
        data = digest(fetch())
    except SystemExit:
        raise
    except Exception as e:
        # Same policy as the Spotify card: keep the last good render rather
        # than replacing a working panel with an error.
        print("stats fetch failed: " + str(e), file=sys.stderr)
        return 0

    print(f"contributions={data['total']} active={data['active']} "
          f"longest={data['longest']} current={data['current']} "
          f"repos={data['repos']} stars={data['stars']}")

    os.makedirs(ASSETS, exist_ok=True)
    for theme in ("dark", "light"):
        for name, svg in (("rhythm", rhythm_svg(data, theme)),
                          ("stats", stats_svg(data, theme))):
            path = os.path.join(ASSETS, f"{name}-{theme}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(svg)
    print("cards rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
