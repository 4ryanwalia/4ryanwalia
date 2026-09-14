# Setup

Three things to do once. The profile works the moment you push — the Spotify
card just shows "awaiting credentials" until you finish step 2.

---

## 1. Publish the repo

GitHub shows `README.md` from a **public** repo whose name matches your
username, so this has to be `4ryanwalia/4ryanwalia`.

```bash
cd "C:/Users/91966/OneDrive/Desktop/4ryanwalia-profile" && git init -b main && git add -A && git commit -m "Profile: recon report on its own author" && gh repo create 4ryanwalia/4ryanwalia --public --source=. --push
```

Then visit `https://github.com/4ryanwalia` — the README is on the profile.

---

## 2. Wire up Spotify

### 2a. Create the app

1. Go to <https://developer.spotify.com/dashboard> and **Create app**.
2. Name and description: anything.
3. **Redirect URI** — this must match exactly, including the port:

   ```
   http://127.0.0.1:8888/callback
   ```

   (Spotify rejects `localhost` on new apps; use the IP literal.)
4. Tick **Web API**, save, then open **Settings** and copy the **Client ID**
   and **Client secret**.

### 2b. Get a refresh token

```bash
python scripts/get_refresh_token.py
```

It asks for the two values, opens Spotify in your browser, catches the
redirect on 127.0.0.1, and prints a refresh token. It runs entirely on your
machine and talks to nobody but `accounts.spotify.com`. Run it once; the token
does not expire on its own.

### 2c. Store the three secrets

**Settings → Secrets and variables → Actions → New repository secret**, or:

```bash
gh secret set SPOTIFY_CLIENT_ID --repo 4ryanwalia/4ryanwalia && gh secret set SPOTIFY_CLIENT_SECRET --repo 4ryanwalia/4ryanwalia && gh secret set SPOTIFY_REFRESH_TOKEN --repo 4ryanwalia/4ryanwalia
```

### 2d. Kick it off

```bash
gh workflow run "Spotify card" --repo 4ryanwalia/4ryanwalia && gh run watch --repo 4ryanwalia/4ryanwalia
```

Play something first, or the card will correctly report your last track
instead of a live one.

---

## 3. Check the Buy Me a Coffee slug

`.github/FUNDING.yml` and the README both assume
<https://www.buymeacoffee.com/4ryanwalia>. If your page is at a different
slug, change it in **two** places:

- `.github/FUNDING.yml` → `buy_me_a_coffee:`
- `README.md` → the `buymeacoffee.com/...` link in the `sudo fund --coffee` section

GitHub Sponsors needs nothing further — `github: [4ryanwalia]` in
`FUNDING.yml` puts the Sponsor button on this and any other repo you copy that
file into.

---

## How the Spotify card actually works

| | |
|---|---|
| **Trigger** | `.github/workflows/spotify.yml`, every ~10 min plus manual dispatch |
| **Renderer** | `scripts/spotify_card.py` — Python standard library only, zero `pip install` |
| **Output** | `assets/spotify-dark.svg`, `assets/spotify-light.svg`, and the block between the `SPOTIFY:START` / `SPOTIFY:END` markers in `README.md` |
| **Commits** | only when the track changes, authored by `github-actions[bot]` so your contribution graph stays honest |
| **Token custody** | GitHub Actions secrets → the script → Spotify. No third-party widget host in the path. |

**Album art is inlined as a base64 data URI.** That is not decoration. An SVG
loaded through an `<img>` tag renders in the browser's restricted static mode,
which blocks every external resource the document tries to fetch — so a linked
cover URL renders blank for everyone, no matter how it is served.

**The `?v=` query string is a cache-buster.** Images living in this repo are
served from `github.com/4ryanwalia/4ryanwalia/raw/main/...` behind a CDN rather
than through Camo, but it caches all the same; the script rewrites the README
`srcset`s with a fresh timestamp each run so a new card is actually fetched.

**Failures are silent on purpose.** If Spotify returns a 502 or the token
refresh hiccups, the script exits cleanly and leaves the last good card in
place. A transient upstream error should not blank your profile.

### Editing the card

Change `scripts/spotify_card.py` — the `THEMES` dict for colours, `card()` for
layout. Never edit the block between the README markers; the next run
overwrites it.

Render locally without touching the repo secrets:

```bash
python scripts/spotify_card.py
```

With no credentials in the environment it writes the "awaiting credentials"
card, which is a quick way to check layout changes.

---

## Other pieces

- **`assets/banner.svg`** — hand-written animated SVG, no generator service.
  The line reveals are SMIL `<animate>` on clip rects; edit the `begin` values
  in `<defs>` to retime them.
- **GitHub stats cards** come from the public `github-readme-stats` instance,
  which is rate-limited and occasionally 429s. If it gets flaky, deploy your
  own from <https://github.com/anuraghazra/github-readme-stats> and swap the
  two hostnames in `README.md`.
