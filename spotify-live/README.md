# spotify-live

Renders the now-playing card **at request time** rather than on a schedule.

The GitHub Action in the parent repo can only be as fresh as GitHub's cron,
which queues on shared runners and routinely lands 15–40 minutes apart. This
endpoint runs when someone actually loads the profile, so the card is current
as of that page view.

No dependencies. The only things that ever hold the refresh token are Vercel's
environment variables and `api/card.js`.

---

## Deploy

You need to log in first — it opens a browser, so I can't do it for you:

```bash
vercel login
```

Then, from this directory:

```bash
cd "C:/Users/91966/OneDrive/Desktop/4ryanwalia-profile/spotify-live" && vercel --prod
```

Accept the defaults. Vercel prints a production URL — that is what the profile
README needs to point at.

## Set the three environment variables

Same values already in the GitHub repo secrets:

```bash
vercel env add SPOTIFY_CLIENT_ID production && vercel env add SPOTIFY_CLIENT_SECRET production && vercel env add SPOTIFY_REFRESH_TOKEN production
```

Each prompts for the value and stores it encrypted. Then redeploy so the
running build picks them up:

```bash
vercel --prod
```

## Check it

```bash
curl -s "https://YOUR-PROJECT.vercel.app/card.svg" | head -c 200
```

You should see `<svg ...><title>NOW PLAYING — ...`. Add `?theme=light` for the
light variant.

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
