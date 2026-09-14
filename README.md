<p align="center">
  <img src="./assets/banner.svg" width="860" alt="Terminal running myrecon --target 4ryanwalia --deep --verify. Identity: Aryan Walia, confirmed. Role: penetration tester, CEH, confirmed. Building: BugSnaps and MyRecon, confirmed.">
</p>

<p align="center">
  <a href="https://bugsnaps.in"><img alt="BugSnaps — offensive security" src="https://img.shields.io/badge/BugSnaps-offensive%20security-4a8bf7?style=for-the-badge&labelColor=0a0f1a"></a>
  <a href="https://www.myrecon.xyz"><img alt="MyRecon — OSINT platform" src="https://img.shields.io/badge/MyRecon-OSINT%20platform-34d399?style=for-the-badge&labelColor=0a0f1a"></a>
  <a href="https://hackerone.com/4ryanwalia"><img alt="HackerOne profile" src="https://img.shields.io/badge/HackerOne-4ryanwalia-f59e0b?style=for-the-badge&labelColor=0a0f1a"></a>
  <a href="mailto:aryan@bugsnaps.in"><img alt="Email" src="https://img.shields.io/badge/aryan@bugsnaps.in-e8eef7?style=for-the-badge&labelColor=0a0f1a"></a>
</p>

---

## `$ whoami`

I'm **Aryan Walia** — a penetration tester who got tired of reports that list
possibilities as though they were findings, and started building tools that
refuse to guess.

That habit became a company and a product. **[BugSnaps](https://bugsnaps.in)** is
my offensive security practice: application and infrastructure testing against
the OWASP methodology, with remediation a development team can actually act on
instead of a PDF of raw scanner output. **[MyRecon](https://www.myrecon.xyz)** is
what happened when I pointed the same discipline at OSINT — it reports what it
can support, at the confidence it can support it, and says plainly when it
doesn't know.

That last part is rarer than it should be. Run a username through most tools in
this category and you get a wall of green ticks; click a few and the accounts
aren't there. So MyRecon measures instead of assuming — we request a handle we
know is real and a string of nonsense nobody could have registered, compare the
two responses byte for byte, and any platform that returns the same page for
both gets labelled honestly or excluded. A smaller platform count that is true
beats a bigger one that is partly fiction.

<table>
<tr><td><b>Role</b></td><td>Penetration tester · Founder</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Certification</b></td><td>Certified Ethical Hacker — passed first attempt</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Education</b></td><td>Master's degree, NMIMS Mumbai</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Shipping</b></td><td>MyRecon on the web and on Google Play</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Handle</b></td><td><code>4ryanwalia</code> — same on nearly every platform</td><td><code>CONFIRMED</code></td></tr>
<tr><td><b>Location</b></td><td>India · UTC+05:30</td><td><code>SELF-REPORTED</code></td></tr>
</table>

---

## `$ myrecon --stream audio`

Straight off the Spotify Web API — the track playing right now, or the last one
if I've stopped. The card below rebuilds itself every ten minutes.

<!-- SPOTIFY:START -->
<!-- rewritten by .github/workflows/spotify.yml - edit the script, not this block -->
<p align="center">
  <a href="https://open.spotify.com/track/2L1OXzqVPpVxotHfLglUcB">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="./assets/spotify-dark.svg?v=1789398201">
      <source media="(prefers-color-scheme: light)" srcset="./assets/spotify-light.svg?v=1789398201">
      <img src="./assets/spotify-dark.svg?v=1789398201" alt="Last track played: Chauffeur — Diljit Dosanjh, Tory Lanez, Ikky" width="480">
    </picture>
  </a>
</p>
<!-- SPOTIFY:END -->

<sub>

**How it works, since you asked.** No third-party widget service holds my
refresh token. A [GitHub Action](./.github/workflows/spotify.yml) runs a
[stdlib-only Python script](./scripts/spotify_card.py) that refreshes the token,
asks Spotify what's playing, inlines the album art as a data URI, and renders
the SVG you're looking at. Zero dependencies installed, so there's no supply
chain sitting between the secret and the API call — which felt like the only
defensible way to do this given the day job. It commits only when the track
actually changes, and commits as the bot, so it never colours my contribution
graph green for listening to music.

</sub>

---

## `$ ls ~/field-kit`

**Offensive security**

![Burp Suite](https://img.shields.io/badge/Burp%20Suite-FF6633?style=flat-square&logo=burpsuite&logoColor=white)
![Nmap](https://img.shields.io/badge/Nmap-4a8bf7?style=flat-square&logo=gnometerminal&logoColor=white)
![Wireshark](https://img.shields.io/badge/Wireshark-1679A7?style=flat-square&logo=wireshark&logoColor=white)
![Metasploit](https://img.shields.io/badge/Metasploit-2596CD?style=flat-square&logo=metasploit&logoColor=white)
![OWASP](https://img.shields.io/badge/OWASP-000000?style=flat-square&logo=owasp&logoColor=white)
![Kali](https://img.shields.io/badge/Kali%20Linux-557C94?style=flat-square&logo=kalilinux&logoColor=white)

**Build**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-6DB33F?style=flat-square&logo=springboot&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Jetpack Compose](https://img.shields.io/badge/Jetpack%20Compose-4285F4?style=flat-square&logo=jetpackcompose&logoColor=white)

**Run**

![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Play Store](https://img.shields.io/badge/Google%20Play-414141?style=flat-square&logo=googleplay&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)

---

## `$ ps aux | grep aryan`

| | What it is | Stack |
|---|---|---|
| **[MyRecon](https://github.com/4ryanwalia/Myrecon)** | Username sweeps across 100+ platforms, email breach exposure, domain/DNS/IP investigation. Web app, Android app, and a daily-updated breach archive. Passwords are hashed in your browser, so they never leave the device. | `Kotlin` `Python` `JS` |
| **[Cryptoji / Coffin](https://github.com/4ryanwalia/Coffin)** | Hybrid-encrypted messages encoded as emoji sequences. Premium burial services for your digital secrets. | `Django` `React` |
| **[KINDA-EDR](https://github.com/4ryanwalia/KINDA-EDR)** | Endpoint detection and response, small enough to read end to end. | `Python` |
| **[Phishing Detection](https://github.com/4ryanwalia/Phishing-detection)** | Classifies a URL as phishing or legitimate from real-world features rather than a blocklist. | `Python` `Jupyter` |
| **[Photo Retrieval](https://github.com/4ryanwalia/intelligent-photo-retrieval)** | Hand it one selfie and it finds you in a folder of event photos using facial embeddings. | `Python` `Streamlit` |
| **[WhisperDesk](https://github.com/4ryanwalia/WhisperDesk)** | Role-based complaint management with genuinely anonymous submissions and live status tracking. | `Spring Boot` `JWT` `MySQL` |

I also publish the research behind MyRecon rather than keeping it as an
advantage, because the failure mode it describes affects every tool in the
category — [including mine](https://www.myrecon.xyz/guides/why-username-checkers-report-fake-accounts.html).

---

## `$ git log --stat`

<p align="center">
  <img height="165" alt="GitHub statistics" src="https://github-readme-stats.vercel.app/api?username=4ryanwalia&show_icons=true&include_all_commits=true&hide_border=true&bg_color=0a0f1a&title_color=4a8bf7&text_color=9aabc4&icon_color=34d399&ring_color=4a8bf7">
  <img height="165" alt="Most used languages" src="https://github-readme-stats.vercel.app/api/top-langs/?username=4ryanwalia&layout=compact&langs_count=8&hide_border=true&bg_color=0a0f1a&title_color=4a8bf7&text_color=9aabc4">
</p>

---

## `$ sudo fund --coffee`

MyRecon is free, keyless where it can be, and has no paywall on the part that
matters. If it saved you an afternoon of manual checking — or if the breach
archive told you something you needed to know — you can put something in the
tin. It goes straight back into hosting and the next batch of platform
verification work.

<p align="center">
  <a href="https://github.com/sponsors/4ryanwalia"><img alt="Sponsor 4ryanwalia on GitHub" src="https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?style=for-the-badge&logo=githubsponsors&logoColor=white&labelColor=0a0f1a"></a>
  &nbsp;
  <a href="https://www.buymeacoffee.com/4ryanwalia"><img alt="Buy me a coffee" src="https://img.shields.io/badge/Buy%20me%20a%20coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black&labelColor=0a0f1a"></a>
</p>

---

## `$ contact --verified`

Email is the reliable route. I'm `4ryanwalia` nearly everywhere else.

<p align="center">
  <a href="mailto:aryan@bugsnaps.in"><b>aryan@bugsnaps.in</b></a> &nbsp;·&nbsp;
  <a href="https://bugsnaps.in">bugsnaps.in</a> &nbsp;·&nbsp;
  <a href="https://www.myrecon.xyz">myrecon.xyz</a> &nbsp;·&nbsp;
  <a href="https://hackerone.com/4ryanwalia">HackerOne</a> &nbsp;·&nbsp;
  <a href="https://open.spotify.com/user/31zbuvzhd6mp2cjl3zeed7x2bamu">Spotify</a>
</p>

<sub>

Best message you can send me is a result you think is wrong. If a platform
reports something MyRecon missed, or reports one that isn't real, tell me and
I'll measure it.

</sub>

<p align="center"><sub><code>scan complete · 6 attributes confirmed · 1 self-reported · 0 inferred</code></sub></p>
