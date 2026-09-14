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

    longest, current = streaks(days)
    return {
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


# -------------------------------------------------------------- contributions

CELL, GAP = 11, 2
PITCH = CELL + GAP
GRID_X, GRID_Y = 42, 52
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def contributions_svg(d: dict, theme: str) -> str:
    c = THEMES[theme]
    cols = len(d["weeks"])
    grid_w = cols * PITCH - GAP
    W = GRID_X + grid_w + 22
    H = GRID_Y + 7 * PITCH - GAP + 46

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Contribution graph: '
        f'{d["total"]} contributions over the last year, active on {d["active"]} '
        f'of {d["span"]} days.">',
        f"<title>{d['total']} contributions · {d['active']} active days</title>",
        "<defs>",
        # The sweep: a soft column of light travelling across the grid, the way
        # a radar trace crosses a scope.
        f'<linearGradient id="sweep-{theme}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{c["accent"]}" stop-opacity="0"/>'
        f'<stop offset="0.55" stop-color="{c["accent"]}" stop-opacity="0.16"/>'
        f'<stop offset="0.85" stop-color="{c["accent"]}" stop-opacity="0.42"/>'
        f'<stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/>'
        "</linearGradient>",
        f'<clipPath id="scope-{theme}"><rect x="{GRID_X}" y="{GRID_Y}" '
        f'width="{grid_w}" height="{7 * PITCH - GAP}"/></clipPath>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{c["card"]}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" '
        f'fill="none" stroke="{c["border"]}"/>',
        f'<text x="20" y="28" font-family="{MONO}" font-size="11.5" '
        f'font-weight="700" letter-spacing="0.10em" fill="{c["accent"]}">'
        f"CONTRIBUTION SIGNAL</text>",
        f'<text x="{W - 20}" y="28" text-anchor="end" font-family="{MONO}" '
        f'font-size="11" fill="{c["mute"]}">{d["span"]}-day window</text>',
    ]

    # Month labels, printed once at each month's first week.
    seen = set()
    for i, week in enumerate(d["weeks"]):
        if not week:
            continue
        first = date.fromisoformat(week[0]["date"])
        if first.month not in seen and first.day <= 7:
            seen.add(first.month)
            out.append(
                f'<text x="{GRID_X + i * PITCH}" y="{GRID_Y - 8}" '
                f'font-family="{MONO}" font-size="9.5" fill="{c["mute"]}">'
                f"{MONTHS[first.month - 1]}</text>"
            )

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="{GRID_X - 8}" y="{GRID_Y + row * PITCH + 9}" '
            f'text-anchor="end" font-family="{MONO}" font-size="9" '
            f'fill="{c["mute"]}">{label}</text>'
        )

    for i, week in enumerate(d["weeks"]):
        for day in week:
            x = GRID_X + i * PITCH
            y = GRID_Y + day["weekday"] * PITCH
            fill = c["ramp"][level(day["count"], d["peak"])]
            out.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{fill}"><title>{day["date"]}: {day["count"]}</title></rect>'
            )

    out.append(
        f'<g clip-path="url(#scope-{theme})">'
        f'<rect x="{GRID_X - 60}" y="{GRID_Y}" width="60" '
        f'height="{7 * PITCH - GAP}" fill="url(#sweep-{theme})">'
        f'<animate attributeName="x" from="{GRID_X - 60}" to="{GRID_X + grid_w}" '
        f'dur="4.5s" repeatCount="indefinite"/>'
        "</rect></g>"
    )

    base = GRID_Y + 7 * PITCH - GAP + 26
    out.append(
        f'<text x="20" y="{base}" font-family="{MONO}" font-size="10" '
        f'fill="{c["mute"]}">detections <tspan fill="{c["text"]}" '
        f'font-weight="700">{d["total"]}</tspan>  ·  active '
        f'<tspan fill="{c["text"]}">{d["active"]}d</tspan>  ·  peak '
        f'<tspan fill="{c["text"]}">{d["peak"]}/day</tspan>  ·  longest run '
        f'<tspan fill="{c["text"]}">{d["longest"]}d</tspan>  ·  current '
        f'<tspan fill="{c["ok"] if d["current"] else c["mute"]}">'
        f'{d["current"]}d</tspan></text>'
    )

    legend_x = W - 20 - 26 - 5 * 15
    out.append(
        f'<text x="{legend_x - 8}" y="{base}" text-anchor="end" '
        f'font-family="{MONO}" font-size="9" fill="{c["mute"]}">less</text>'
    )
    for i, shade in enumerate(c["ramp"]):
        out.append(
            f'<rect x="{legend_x + i * 15}" y="{base - 9}" width="11" height="11" '
            f'rx="2.5" fill="{shade}"/>'
        )
    out.append(
        f'<text x="{legend_x + 5 * 15 + 1}" y="{base}" font-family="{MONO}" '
        f'font-size="9" fill="{c["mute"]}">more</text>'
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
        for name, svg in (("contributions", contributions_svg(data, theme)),
                          ("stats", stats_svg(data, theme))):
            path = os.path.join(ASSETS, f"{name}-{theme}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(svg)
    print("cards rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
