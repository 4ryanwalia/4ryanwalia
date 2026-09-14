# Setup

Three things to do once. The profile works the moment you push — the Spotify
card just says "awaiting credentials" until you finish step 2.

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

### 2b. Get a token and load it everywhere, in one go

```bash
python scripts/get_refresh_token.py
```

It asks for the client ID and secret, opens Spotify in **your** browser so you
log in yourself, catches the redirect on 127.0.0.1, and exchanges the code for
a refresh token. Then it pipes all three values into `gh secret set` *and*
`vercel env add` over stdin — so the token is never printed, never written to
disk, and never enters your shell history — redeploys the live endpoint, and
checks that the endpoint stops saying "awaiting credentials". Answer `n` at the
prompt and it prints the refresh token instead, for machines without `gh`.

Two destinations because there are two renderers, and they are not equals:

- **Vercel** runs `spotify-live/api/card.js`, which is what the README points
  at. It asks Spotify when someone loads your profile.
- **GitHub Actions** runs `scripts/spotify_card.py`, which renders the same
  card into `assets/`. It is the fallback, and it only runs when you press the
  button.

Nothing here ever sees your Spotify password: that is the entire point of the
OAuth redirect. The script talks to `accounts.spotify.com`, to `gh` and to
`vercel`, and to nothing else. Run it once; the refresh token does not expire
on its own.

If you would rather set them by hand, the names are `SPOTIFY_CLIENT_ID`,
`SPOTIFY_CLIENT_SECRET` and `SPOTIFY_REFRESH_TOKEN`, in two places: the repo's
**Settings → Secrets and variables → Actions**, and the Vercel project's
**Settings → Environment Variables** (Production). Vercel bakes them in at
build time, so redeploy after changing them or the running function keeps the
old values.

### 2c. Check it

```bash
curl -s "https://spotify-live-seven.vercel.app/card.svg" | head -c 160
```

You want `aria-label="NOW PLAYING: ...`. Play something first, or the card will
correctly report your last track instead of a live one.

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

The README points at a Vercel function, not at a file in this repo:

| | |
|---|---|
| **Trigger** | someone loads your profile |
| **Renderer** | `spotify-live/api/card.js` — no dependencies, one file |
| **Output** | an SVG streamed straight to the browser, `no-store` |
| **Token custody** | Vercel environment variables → the function → Spotify. No third-party widget host in the path. |

and keeps a fallback that does it the slow way:

| | |
|---|---|
| **Trigger** | `.github/workflows/spotify.yml`, **manual dispatch only** |
| **Renderer** | `scripts/spotify_card.py` — Python standard library only, zero `pip install` |
| **Output** | `assets/spotify-*.svg`, and a rewrite of the block between the `SPOTIFY:START` / `SPOTIFY:END` markers in `README.md` |
| **Commits** | only when the track changes, authored by `github-actions[bot]` so your contribution graph stays honest |

Running that workflow **replaces the live card with a static one** — that is
its job. It has no cron for exactly that reason. Use it if the endpoint ever
has to be abandoned; otherwise leave it alone.

**Album art is inlined as a base64 data URI.** That is not decoration. An SVG
loaded through an `<img>` tag renders in the browser's restricted static mode,
which blocks every external resource the document tries to fetch — so a linked
cover URL renders blank for everyone, no matter how it is served.

**The animation is real, the clock is a projection.** Declarative SMIL survives
restricted static mode even though scripting does not, so the equaliser, the
progress bar and the per-second elapsed counter all run in the reader's
browser. The starting point is exact — the function asked Spotify as the image
was fetched — and from there the bar runs on the reader's own clock, because
nothing inside a README is allowed to poll. Skip a track and a reload puts it
right.

**How fresh "live" really is.** The function is exact and sends `no-store`.
GitHub proxies external README images through Camo, which is a cache, and
`no-store` is the strongest available way of asking it not to hold a copy — not
a guarantee. That is why the card prints the time it was drawn rather than
claiming to be live without evidence.

**Failures are honest, not silent.** If Spotify 502s or the token refresh
hiccups, the endpoint still returns a valid card that says so, with HTTP 200. A
500 would show your profile a broken-image icon.

### Editing the card

Change `spotify-live/api/card.js` — the `THEMES` object for colours, `card()`
for layout — then `cd spotify-live && vercel --prod`. Never edit the block
between the README markers by hand unless you have retired the endpoint; the
fallback workflow overwrites it.

`scripts/spotify_card.py` is the fallback's renderer and is a separate
implementation of the same design. If you change one and care about the
fallback, change both.

---

## Other pieces

- **`assets/banner.svg`** — hand-written animated SVG, no generator service.
  The line reveals are SMIL `<animate>` on clip rects; edit the `begin` values
  in `<defs>` to retime them.
- **The stats panel** is rendered in-repo by `scripts/stats_card.py` on the
  schedule in `.github/workflows/stats.yml`. It used to come from the public
  `github-readme-stats` instance, which was returning 503; nothing on this
  profile depends on a third-party widget host any more.
