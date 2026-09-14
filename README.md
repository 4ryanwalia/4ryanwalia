<p align="center">
  <img src="./assets/hero.svg" width="860" alt="hey, i'm ARYAN. Offensive security and OSINT. I find the red flags before someone worse does. Penetration tester, CEH, founder of BugSnaps and MyRecon.">
</p>

<p align="center">
  <img src="./assets/hdr-listening.svg" width="860" alt="currently listening">
</p>

<!-- SPOTIFY:START -->
<!-- Drawn by spotify-live/api/card.js at the moment you load this page, not on
     a schedule. .github/workflows/spotify.yml can rewrite this block back to
     the static ./assets cards if the endpoint ever has to go; it only runs on
     a manual dispatch now. -->
<p align="center">
  <a href="https://open.spotify.com/user/31zbuvzhd6mp2cjl3zeed7x2bamu">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="https://spotify-live-seven.vercel.app/card.svg?theme=light">
      <img src="https://spotify-live-seven.vercel.app/card.svg" alt="What I am listening to on Spotify, drawn when this page loaded" width="480">
    </picture>
  </a>
</p>
<!-- SPOTIFY:END -->

<p align="center">
  <img src="./assets/hdr-building.svg" width="860" alt="what i'm building">
</p>

**[BugSnaps](https://bugsnaps.in)** — my penetration testing and offensive security
practice. Application and infrastructure testing against the OWASP methodology,
for growing businesses that need findings their developers can actually act on
rather than a PDF of raw scanner output.

**[MyRecon](https://www.myrecon.xyz)** — an OSINT platform that came out of the day
job. Username sweeps across 100+ platforms, email breach exposure, and domain,
DNS and IP investigation. On the web, on Google Play, and backed by a breach
archive that updates daily. Passwords are hashed in your browser, so they never
leave your device.

<p align="center">
  <img src="./assets/hdr-hire.svg" width="860" alt="need a pentest?">
</p>

I take on application and infrastructure security work, plus
[footprint removal](https://www.myrecon.xyz/services.html) for people who need
their personal data off the open web.

<p align="center">
  <a href="mailto:aryan@bugsnaps.in"><img src="./assets/link-email.svg" height="38" alt="hire me: aryan@bugsnaps.in"></a>
</p>

Same address for a result you think is wrong — those are the most useful
messages I get. If a platform reports something MyRecon missed, or reports one
that isn't real, tell me and I'll measure it.

<p align="center">
  <img src="./assets/hdr-find.svg" width="860" alt="where to find me">
</p>

<p align="center">
  <a href="https://bugsnaps.in"><img src="./assets/link-bugsnaps.svg" height="38" alt="BugSnaps: offensive security"></a>
  <a href="https://www.myrecon.xyz"><img src="./assets/link-myrecon.svg" height="38" alt="MyRecon: OSINT platform"></a>
  <a href="https://hackerone.com/4ryanwalia"><img src="./assets/link-hackerone.svg" height="38" alt="HackerOne: 4ryanwalia"></a>
</p>
<p align="center">
  <a href="https://www.instagram.com/4ryanwalia"><img src="./assets/link-instagram.svg" height="38" alt="Instagram: 4ryanwalia"></a>
  <a href="https://open.spotify.com/user/31zbuvzhd6mp2cjl3zeed7x2bamu"><img src="./assets/link-spotify.svg" height="38" alt="Spotify: now playing"></a>
  <a href="https://play.google.com/store/apps/details?id=makeme.aryan.makeme"><img src="./assets/link-googleplay.svg" height="38" alt="Google Play: MyRecon"></a>
</p>

<p align="center">
  <img src="./assets/hdr-whoami.svg" width="860" alt="whoami">
</p>

<p align="center">
  <img src="./assets/banner.svg" width="860" alt="Terminal running myrecon --target 4ryanwalia --deep --verify. Identity: Aryan Walia, confirmed. Role: penetration tester, CEH, confirmed. Building: BugSnaps and MyRecon, confirmed.">
</p>

Mapping an organisation's attack surface and mapping a person's public
footprint are the same exercise with a different subject. You enumerate what is
reachable, verify what is real, and discard what only looks like a finding. The
third step is the one almost every OSINT tool skips.

Run a username through most tools in this category and you get a wall of green
ticks. Click a few and you find pages saying the account isn't there. That
isn't a small annoyance — it makes the whole output unusable, because if you
can't tell which results are real you have to check all of them by hand, and at
that point the tool has saved you nothing.

So MyRecon measures instead of assuming. To test whether a platform can be
checked reliably we request a handle we know is real and a string of nonsense
nobody could have registered, then compare the responses byte for byte. Several
well-known platforms return literally identical pages for both. Those get
labelled honestly or excluded — a smaller platform count that is true is worth
more than a bigger one that is partly fiction.

<table>
<tr><td><b>Role</b></td><td>Penetration tester · Founder</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Certification</b></td><td>Certified Ethical Hacker — passed first attempt</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Education</b></td><td>Master's degree, NMIMS Mumbai</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Handle</b></td><td><code>4ryanwalia</code> — same on nearly every platform</td><td><code>CONFIRMED</code></td></tr>
</table>

<p align="center">
  <img src="./assets/hdr-kit.svg" width="860" alt="the field kit">
</p>

<p align="center">
  <img src="./assets/kit.svg" width="860" alt="Field kit. security: Burp Suite, Nmap, Wireshark, Metasploit, OWASP, Kali Linux. build: Python, Kotlin, Flask, Django, Spring Boot, React, Jetpack Compose, GitHub Actions">
</p>

<p align="center">
  <img src="./assets/hdr-ps.svg" width="860" alt="what is running">
</p>

| | What it is | Stack |
|---|---|---|
| **[MyRecon](https://github.com/4ryanwalia/Myrecon)** | Username sweeps across 100+ platforms, email breach exposure, domain/DNS/IP investigation. Web app, Android app, and a daily-updated breach archive. | `Kotlin` `Python` `JS` |
| **[Cryptoji / Coffin](https://github.com/4ryanwalia/Coffin)** | Hybrid-encrypted messages encoded as emoji sequences. Premium burial services for your digital secrets. | `Django` `React` |
| **[KINDA-EDR](https://github.com/4ryanwalia/KINDA-EDR)** | Endpoint detection and response, small enough to read end to end. | `Python` |
| **[Phishing Detection](https://github.com/4ryanwalia/Phishing-detection)** | Classifies a URL as phishing or legitimate from real-world features rather than a blocklist. | `Python` `Jupyter` |
| **[Photo Retrieval](https://github.com/4ryanwalia/intelligent-photo-retrieval)** | Hand it one selfie and it finds you in a folder of event photos using facial embeddings. | `Python` `Streamlit` |
| **[WhisperDesk](https://github.com/4ryanwalia/WhisperDesk)** | Role-based complaint management with genuinely anonymous submissions and live status tracking. | `Spring Boot` `JWT` `MySQL` |

<p align="center">
  <img src="./assets/hdr-telemetry.svg" width="860" alt="telemetry">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/rhythm-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/rhythm-light.svg">
    <img src="./assets/rhythm-dark.svg" alt="Pattern of life: contributions by day of week, and monthly volume across the year" width="740">
  </picture>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/stats-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./assets/stats-light.svg">
    <img src="./assets/stats-dark.svg" alt="Telemetry panel: contributions, public repositories, stars earned, longest run, and languages by volume" width="740">
  </picture>
</p>

<p align="center"><sub>

<b>Pattern of life</b> is the intelligence term for working out a subject's
routine, so it seemed the honest label for this. It is deliberately not a
heatmap of the year — GitHub already draws one further down this page, and a
second copy of it would tell you nothing the first one didn't.

Both panels are rendered from GitHub's own GraphQL API by
<a href="./scripts/stats_card.py">a script in this repo</a>, not by a
third-party stats service. The usual one was returning <code>503</code> when I
checked — which is exactly the problem with hanging your profile off someone
else's free deployment. The section headers, chips and links are drawn by
<a href="./scripts/theme_cards.py">another one</a> for the same reason: apart
from the Spotify card, which is my own endpoint, this page makes no request to
anybody else's server to render itself.

</sub></p>

<p align="center">
  <img src="./assets/hdr-fund.svg" width="860" alt="buy me a coffee">
</p>

<p align="center">
  <img src="./assets/fund.svg" width="740" alt="What the tin pays for: hosting on Render and Vercel, platform verification work, and the daily breach archive rebuild.">
</p>

If MyRecon saved you an afternoon of manual checking — or the breach archive
told you something you needed to know — you can put something in the tin.

<p align="center">
  <a href="https://github.com/sponsors/4ryanwalia"><img src="./assets/link-sponsor.svg" height="38" alt="Sponsor: GitHub Sponsors"></a>
  <a href="https://www.buymeacoffee.com/4ryanwalia"><img src="./assets/link-coffee.svg" height="38" alt="Buy me a coffee: buymeacoffee.com"></a>
</p>

<p align="center"><sub><code>scan complete · 4 attributes confirmed · 0 inferred</code></sub></p>
