# spotify-live

Renders the now-playing card **at request time** rather than on a schedule.

The GitHub Action in the parent repo can only be as fresh as GitHub's cron,
which queues on shared runners and routinely lands 15–40 minutes apart. This
endpoint runs when someone actually loads the profile, so the card is current
as of that page view.

No dependencies. The only things that ever hold the refresh token are Vercel's
environment variables and `api/card.js`.

---

Live at <https://spotify-live-seven.vercel.app/card.svg>, which is the URL the
profile README points at. Add `?theme=light` for the light variant; the README
picks between them with a `<picture>` element.

---

## Credentials

Don't set them here by hand. From the repo root:

```bash
python scripts/get_refresh_token.py
```

That walks the Spotify OAuth redirect in your own browser, then pipes
`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` and `SPOTIFY_REFRESH_TOKEN` into
`vercel env add` over stdin, redeploys, and checks the endpoint came back
configured. It sets the matching GitHub Actions secrets in the same pass, so
the fallback renderer stays usable.

Vercel bakes environment variables in at build time. Setting them without a
redeploy leaves the running function exactly as unconfigured as it was — which
is the one failure mode here that looks fine from the terminal and broken on
the profile.

## Deploy a code change

```bash
cd "C:/Users/91966/OneDrive/Desktop/4ryanwalia-profile/spotify-live" && vercel --prod
```

## Check it

```bash
curl -s "https://spotify-live-seven.vercel.app/card.svg" | head -c 160
```

You want `aria-label="NOW PLAYING: ...`.

---

## What animates

Declarative SMIL survives the browser's restricted static mode even though
scripting does not, so all of this runs in the reader's browser from a plain
`<img>`:

- the equaliser — bouncing while a track plays, breathing slowly when not, so
  the card never reads as a broken image
- the progress bar and its playhead
- a per-second elapsed counter, one text node per second, each revealed for
  exactly its own second
- titles and artists too long for the column, which scroll rather than being
  cut off
- a fade-in on every render, which is a visible receipt that the image was
  drawn for this page view rather than served from a cache

---

## How fresh is "instant", honestly

The endpoint itself is exact — it asks Spotify when the request arrives, and
sends `no-store` so nothing in the path is supposed to hold it.

GitHub proxies external README images through Camo, which is a cache. The
`no-store` headers are the strongest signal available for telling it not to
keep a copy, and in practice the card updates on page load. It is not a
guarantee — that is why the card still prints the time it was rendered rather
than claiming to be live without evidence.

This is as close to real time as a README image can get. A README is a static
document; nothing inside it can poll.
