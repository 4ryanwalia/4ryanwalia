#!/usr/bin/env python3
"""Render the profile's themed furniture: section headers, the field kit, and
every link chip.

One recon terminal, top to bottom. Each section header is a prompt line that
types its own command; the chips below them are drawn here rather than fetched
from img.shields.io, which is the same argument already made for the stats
panel -- nothing on this profile should be able to go down because somebody
else's free deployment did.

Run it by hand after changing anything in here:

    python scripts/theme_cards.py

Deterministic: same input, same bytes out, so a no-op run leaves the repo
clean and never produces a commit.

Two rules the layout depends on:

* Everything is monospace, so a character is exactly 0.6em wide and the
  geometry is arithmetic rather than guesswork.
* Nothing is interactive. An SVG loaded through an <img> renders in the
  browser's restricted static mode: no scripts, and no <a> inside the image.
  That is why each link is its own small file wrapped in markdown's own <a>,
  instead of one wide row with hotspots that would silently do nothing.
"""

from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# The palette the hero, banner, fund and Spotify cards already use. Changing a
# value here changes it everywhere except those four hand-written files.
INK = "#e8eef7"
DIM = "#9aabc4"
MUTE = "#7d8aa3"
LINE = "#1f2b42"
EDGE = "#2c3c5a"
PANEL = "#111a2b"
DEEP = "#0a0f1a"
BLUE = "#4a8bf7"
GREEN = "#34d399"

WIDTH = 860


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def cw(size: float) -> float:
    """Width of one monospace character at `size`."""
    return size * 0.6


def write(name: str, body: str) -> None:
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("  " + name)


def svg(w: float, h: float, label: str, body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%g" height="%g" '
        'viewBox="0 0 %g %g" role="img" aria-label="%s">'
        "<title>%s</title>%s</svg>"
    ) % (w, h, w, h, esc(label), esc(label), body)


# --------------------------------------------------------------- section header

# (slug, command, what the section is -- used as the alt text)
SECTIONS = [
    ("listening", "spotify --now-playing --follow", "currently listening"),
    ("building", "cat ~/ventures/*.md", "what i'm building"),
    ("hire", 'mail -s "engagement" aryan@bugsnaps.in', "need a pentest"),
    ("find", "myrecon --sweep 4ryanwalia", "where to find me"),
    ("whoami", "whoami --verify", "whoami"),
    ("kit", "ls ~/field-kit", "the field kit"),
    ("ps", "ps aux | grep aryan", "what is running"),
    ("telemetry", "myrecon --scan self --telemetry", "telemetry"),
    ("fund", "sudo fund --coffee", "buy me a coffee"),
]

HDR_H = 48
PROMPT_USER = "aryan@recon"
PROMPT_TAIL = ":~$ "


def header(slug: str, command: str, alt: str, index: int, total: int) -> str:
    size = 14.0
    c = cw(size)
    y = 30.0
    x0 = 34.0

    user_w = len(PROMPT_USER) * c
    tail_w = len(PROMPT_TAIL) * c
    cmd_x = x0 + user_w + tail_w
    cmd_w = len(command) * c

    # Roughly a fast touch-typist, floored so short commands still read as
    # typed rather than appearing whole.
    dur = max(0.55, min(1.9, len(command) * 0.045))

    parts = [
        '<rect width="%d" height="%d" rx="9" fill="%s"/>' % (WIDTH, HDR_H, PANEL),
        '<rect x="0.5" y="0.5" width="%d" height="%d" rx="9" fill="none" stroke="%s"/>'
        % (WIDTH - 1, HDR_H - 1, LINE),
        # A blue edge down the left, clipped to the panel's own rounding.
        '<path d="M9 0 H16 V%d H9 A9 9 0 0 1 0 %d V9 A9 9 0 0 1 9 0 Z" fill="%s" opacity="0.85"/>'
        % (HDR_H, HDR_H - 9, BLUE),
        '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="%s">%s</text>'
        % (x0, y, MONO, size, GREEN, esc(PROMPT_USER)),
        '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="%s">%s</text>'
        % (x0 + user_w, y, MONO, size, MUTE, esc(PROMPT_TAIL.rstrip())),
        # The command is revealed by widening a clip window rather than by
        # swapping text nodes -- one animation instead of one node per glyph.
        '<clipPath id="type"><rect x="%g" y="%g" width="0" height="22">'
        '<animate attributeName="width" from="0" to="%g" dur="%gs" fill="freeze"/>'
        "</rect></clipPath>" % (cmd_x, y - 15, cmd_w, dur),
        '<text x="%g" y="%g" clip-path="url(#type)" font-family="%s" font-size="%g" '
        'fill="%s">%s</text>' % (cmd_x, y, MONO, size, INK, esc(command)),
        # The caret rides the clip edge, then blinks once the line is typed.
        '<rect x="%g" y="%g" width="%g" height="17" fill="%s">'
        '<animate attributeName="x" from="%g" to="%g" dur="%gs" fill="freeze"/>'
        '<animate attributeName="opacity" values="1;1;0;0;1" dur="1.06s" '
        'begin="%gs" repeatCount="indefinite"/></rect>'
        % (cmd_x, y - 13, c, BLUE, cmd_x, cmd_x + cmd_w, dur, dur),
        '<text x="%d" y="%g" text-anchor="end" font-family="%s" font-size="10.5" '
        'letter-spacing="0.08em" fill="%s">%02d / %02d</text>'
        % (WIDTH - 22, y - 1, MONO, EDGE, index, total),
    ]
    return svg(WIDTH, HDR_H, alt, "".join(parts))


# ------------------------------------------------------------------- field kit

KIT = [
    ("security/", [
        ("Burp Suite", "#ff6633"), ("Nmap", "#4a8bf7"), ("Wireshark", "#1679a7"),
        ("Metasploit", "#2596cd"), ("OWASP", "#8cb2c8"), ("Kali Linux", "#557c94"),
    ]),
    ("build/", [
        ("Python", "#3776ab"), ("Kotlin", "#7f52ff"), ("Flask", "#cbd5e1"),
        ("Django", "#44b78b"), ("Spring Boot", "#6db33f"), ("React", "#61dafb"),
        ("Jetpack Compose", "#4285f4"), ("GitHub Actions", "#2088ff"),
    ]),
]

CHIP_H = 28.0
CHIP_PAD = 13.0
CHIP_DOT = 11.0
CHIP_SIZE = 12.0


def chip(x: float, y: float, text: str, colour: str, delay: float) -> tuple:
    """One pill. Returns (markup, width) so the caller can keep packing."""
    w = CHIP_DOT + 9 + len(text) * cw(CHIP_SIZE) + CHIP_PAD
    body = (
        '<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
        'dur="0.4s" begin="%gs" fill="freeze"/>'
        '<rect x="%g" y="%g" width="%g" height="%g" rx="7" fill="%s" stroke="%s"/>'
        '<circle cx="%g" cy="%g" r="3.2" fill="%s"/>'
        '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="%s">%s</text></g>'
    ) % (
        delay,
        x, y, w, CHIP_H, DEEP, EDGE,
        x + CHIP_DOT, y + CHIP_H / 2, colour,
        x + CHIP_DOT + 9, y + CHIP_H / 2 + 4.2, MONO, CHIP_SIZE, INK, esc(text),
    )
    return body, w


def field_kit() -> str:
    gap = 8.0
    label_w = 86.0
    x_start = 20.0 + label_w
    max_x = WIDTH - 20.0

    parts = []
    y = 18.0
    n = 0
    for group, items in KIT:
        row_top = y
        x = x_start
        for text, colour in items:
            body, w = chip(x, y, text, colour, n * 0.045)
            if x + w > max_x:            # wrap, and keep the left rail clear
                x = x_start
                y += CHIP_H + gap
                body, w = chip(x, y, text, colour, n * 0.045)
            parts.append(body)
            x += w + gap
            n += 1
        parts.append(
            '<text x="20" y="%g" font-family="%s" font-size="11.5" fill="%s">%s</text>'
            % (row_top + CHIP_H / 2 + 4, MONO, BLUE, esc(group))
        )
        y += CHIP_H + 18.0

    height = y + 4.0
    frame = (
        '<rect width="%d" height="%g" rx="9" fill="%s"/>'
        '<rect x="0.5" y="0.5" width="%d" height="%g" rx="9" fill="none" stroke="%s"/>'
        % (WIDTH, height, PANEL, WIDTH - 1, height - 1, LINE)
    )
    alt = "Field kit. " + ". ".join(
        g.rstrip("/") + ": " + ", ".join(t for t, _ in items) for g, items in KIT
    )
    return svg(WIDTH, height, alt, frame + "".join(parts))


# ----------------------------------------------------------------- link chips

# Each is its own file so markdown can wrap it in a real <a>. Kept on the deep
# navy in both GitHub themes on purpose: the hero, banner and fund cards are
# dark-only too, so a light variant here would be the odd one out.
LINKS = [
    ("bugsnaps", "BugSnaps", "offensive security", BLUE),
    ("myrecon", "MyRecon", "OSINT platform", GREEN),
    ("hackerone", "HackerOne", "4ryanwalia", "#f59e0b"),
    ("instagram", "Instagram", "4ryanwalia", "#e4405f"),
    ("spotify", "Spotify", "now playing", "#1db954"),
    ("googleplay", "Google Play", "MyRecon", "#9aabc4"),
    ("email", "hire me", "aryan@bugsnaps.in", BLUE),
    ("sponsor", "Sponsor", "GitHub Sponsors", "#ea4aaa"),
    ("coffee", "Buy me a coffee", "buymeacoffee.com", "#ffdd00"),
]

LINK_H = 38.0


def link_chip(label: str, value: str, colour: str, phase: float) -> str:
    ls, vs = 12.5, 12.5
    pad, gap, dot = 14.0, 10.0, 12.0
    lw = len(label) * cw(ls)
    vw = len(value) * cw(vs)
    w = dot + 9 + lw + gap + vw + pad
    mid = LINK_H / 2

    parts = [
        '<rect width="%g" height="%g" rx="9" fill="%s"/>' % (w, LINK_H, DEEP),
        '<rect x="0.5" y="0.5" width="%g" height="%g" rx="9" fill="none" stroke="%s"/>'
        % (w - 1, LINK_H - 1, EDGE),
        '<circle cx="%g" cy="%g" r="3.6" fill="%s">'
        '<animate attributeName="opacity" values="1;0.35;1" dur="3.2s" '
        'begin="%gs" repeatCount="indefinite"/></circle>' % (dot, mid, colour, phase),
        '<text x="%g" y="%g" font-family="%s" font-size="%g" font-weight="600" '
        'fill="%s">%s</text>' % (dot + 9, mid + 4.4, MONO, ls, INK, esc(label)),
        '<text x="%g" y="%g" font-family="%s" font-size="%g" fill="%s">%s</text>'
        % (dot + 9 + lw + gap, mid + 4.4, MONO, vs, MUTE, esc(value)),
    ]
    return svg(w, LINK_H, "%s: %s" % (label, value), "".join(parts))


# ------------------------------------------------------------------------ main

def main() -> int:
    os.makedirs(ASSETS, exist_ok=True)
    print("section headers")
    total = len(SECTIONS)
    for i, (slug, command, alt) in enumerate(SECTIONS, start=1):
        write("hdr-%s.svg" % slug, header(slug, command, alt, i, total))

    print("field kit")
    write("kit.svg", field_kit())

    print("link chips")
    for i, (slug, label, value, colour) in enumerate(LINKS):
        write("link-%s.svg" % slug, link_chip(label, value, colour, i * 0.35))

    print("\nDone. Nothing here is fetched at page load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
