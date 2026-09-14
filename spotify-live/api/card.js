/**
 * Renders the now-playing card at request time instead of on a schedule.
 *
 * The GitHub Action version can only be as fresh as GitHub's cron, which
 * queues on shared runners and routinely lands 15-40 minutes apart. This runs
 * when someone actually loads the profile, so the card is current as of that
 * page view.
 *
 * Dependency-free on purpose, same rule as the rest of this repo: the only
 * things that ever hold the refresh token are Vercel's env vars and this file.
 *
 *   /api/card            dark
 *   /api/card?theme=light
 */

const W = 480;
const H = 170;
const ART = 116;

const THEMES = {
  dark: {
    card: "#111a2b", border: "#1f2b42", text: "#e8eef7", dim: "#9aabc4",
    mute: "#7d8aa3", accent: "#4a8bf7", track: "#22304c", ok: "#34d399",
    warn: "#f59e0b", logoFg: "#0a0f1a",
  },
  light: {
    card: "#f7f9fd", border: "#e2e8f0", text: "#0f172a", dim: "#475569",
    mute: "#5f6f86", accent: "#2563eb", track: "#dde5f0", ok: "#047857",
    warn: "#a84d08", logoFg: "#ffffff",
  },
};

const FONT =
  "ui-sans-serif,system-ui,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
const MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace";

const NARROW = new Set("ijlt!|.,;:()[]{}/ '`\\".split(""));
const WIDE = new Set("MWmw@%".split(""));

/** Approximate rendered width, only precise enough to decide where to cut. */
function textWidth(s, size) {
  let total = 0;
  for (const ch of s) {
    if (NARROW.has(ch)) total += 0.34;
    else if (WIDE.has(ch)) total += 0.9;
    else if (/[A-Z0-9]/.test(ch)) total += 0.64;
    else total += 0.545;
  }
  return total * size;
}

function fit(s, size, maxW) {
  if (textWidth(s, size) <= maxW) return s;
  let out = s;
  while (out.length && textWidth(out + "…", size) > maxW) {
    out = out.slice(0, -1);
  }
  return out.trimEnd() + "…";
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function ms(v) {
  const secs = Math.max(0, Math.floor((v || 0) / 1000));
  return `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
}

function ago(iso) {
  const then = Date.parse(iso || "");
  if (Number.isNaN(then)) return "";
  const secs = (Date.now() - then) / 1000;
  if (secs < 90) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

// ---------------------------------------------------------------- spotify

async function accessToken(id, secret, refresh) {
  const basic = Buffer.from(`${id}:${secret}`).toString("base64");
  const r = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${basic}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refresh,
    }),
  });
  if (!r.ok) throw new Error(`token refresh ${r.status}`);
  return (await r.json()).access_token;
}

async function getJson(url, token) {
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (r.status === 204 || r.status === 404) return null;
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  const body = await r.text();
  return body.trim() ? JSON.parse(body) : null;
}

/** Prefer ~300px: sharp enough, small enough to inline. */
function pickArt(images) {
  if (!images?.length) return "";
  return [...images]
    .sort((a, b) => Math.abs((a.width || 640) - 300) - Math.abs((b.width || 640) - 300))[0]
    .url;
}

/**
 * Inline the cover. An SVG loaded through an <img> renders in the browser's
 * restricted static mode and cannot fetch anything external, so a linked URL
 * would be blank for every viewer.
 */
async function fetchArt(url) {
  if (!url) return null;
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    const buf = Buffer.from(await r.arrayBuffer());
    if (buf.length > 700000) return null;
    const png = buf.subarray(0, 8).toString("hex") === "89504e470d0a1a0a";
    return `data:image/${png ? "png" : "jpeg"};base64,${buf.toString("base64")}`;
  } catch {
    return null; // art is decorative; never fail the card over it
  }
}

async function collect() {
  const id = (process.env.SPOTIFY_CLIENT_ID || "").trim();
  const secret = (process.env.SPOTIFY_CLIENT_SECRET || "").trim();
  const refresh = (process.env.SPOTIFY_REFRESH_TOKEN || "").trim();
  if (!id || !secret || !refresh) return { state: "unconfigured" };

  const token = await accessToken(id, secret, refresh);

  const now = await getJson(
    "https://api.spotify.com/v1/me/player/currently-playing", token);
  const item = now?.item;
  if (item && item.type === "track") {
    return {
      state: now.is_playing ? "playing" : "paused",
      title: item.name || "",
      artist: (item.artists || []).map((a) => a.name).join(", "),
      album: item.album?.name || "",
      art: pickArt(item.album?.images),
      url: item.external_urls?.spotify || "",
      progress: now.progress_ms || 0,
      duration: item.duration_ms || 0,
    };
  }

  const recent = await getJson(
    "https://api.spotify.com/v1/me/player/recently-played?limit=1", token);
  const first = recent?.items?.[0];
  if (first) {
    const t = first.track || {};
    return {
      state: "recent",
      title: t.name || "",
      artist: (t.artists || []).map((a) => a.name).join(", "),
      album: t.album?.name || "",
      art: pickArt(t.album?.images),
      url: t.external_urls?.spotify || "",
      playedAt: first.played_at || "",
      duration: t.duration_ms || 0,
    };
  }

  return { state: "silent" };
}

// ----------------------------------------------------------------- render

function logo(x, y, c) {
  return (
    `<g transform="translate(${x},${y})"><circle r="10" fill="#1DB954"/>` +
    `<g stroke="${c.logoFg}" stroke-width="1.7" stroke-linecap="round" fill="none">` +
    `<path d="M-6.1,-3.4 Q0,-6.4 6.3,-2.3"/>` +
    `<path d="M-5.1,0.3 Q0,-2.2 5.3,1.3"/>` +
    `<path d="M-4.0,3.9 Q0,1.9 4.4,4.7"/></g></g>`
  );
}

function equaliser(x, base, c, live) {
  return [11, 16, 7, 13, 9].map((h, i) => {
    const bx = x + i * 5.5;
    if (!live) {
      return `<rect x="${bx}" y="${base - 4}" width="3" height="4" rx="1.5" fill="${c.mute}"/>`;
    }
    const dur = 0.72 + i * 0.17;
    return (
      `<rect x="${bx}" y="${base - 4}" width="3" height="4" rx="1.5" fill="${c.ok}">` +
      `<animate attributeName="height" values="4;${h};6;${h - 3};4" dur="${dur}s" repeatCount="indefinite"/>` +
      `<animate attributeName="y" values="${base - 4};${base - h};${base - 6};${base - h + 3};${base - 4}" dur="${dur}s" repeatCount="indefinite"/>` +
      `</rect>`
    );
  }).join("");
}

function card(d, themeName) {
  const c = THEMES[themeName] || THEMES.dark;
  const state = d.state || "silent";
  const live = state === "playing";
  const colX = 148;
  const colW = W - 148 - 20;

  let label, labelFill, title, artist, album;
  if (state === "unconfigured") {
    label = "AWAITING CREDENTIALS"; labelFill = c.warn;
    title = "Spotify not wired up yet";
    artist = "set the three env vars in Vercel";
    album = "";
  } else if (state === "error") {
    label = "UPSTREAM ERROR"; labelFill = c.warn;
    title = "Spotify did not answer";
    artist = "the card will right itself on the next load";
    album = "";
  } else if (state === "silent") {
    label = "NO SIGNAL"; labelFill = c.mute;
    title = "Nothing playing";
    artist = "and nothing in the recent history";
    album = "";
  } else if (live) {
    label = "NOW PLAYING"; labelFill = c.ok;
    ({ title, artist, album } = d);
  } else if (state === "paused") {
    label = "PAUSED"; labelFill = c.warn;
    ({ title, artist, album } = d);
  } else {
    const stamp = ago(d.playedAt);
    label = stamp ? `LAST PLAYED · ${stamp}` : "LAST PLAYED";
    labelFill = c.mute;
    ({ title, artist, album } = d);
  }

  const artY = (H - ART) / 2;
  const out = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}: ${esc(title)} by ${esc(artist)}">`,
    `<title>${esc(label)} — ${esc(title)} · ${esc(artist)}</title>`,
    `<defs><clipPath id="art"><rect x="20" y="${artY}" width="${ART}" height="${ART}" rx="9"/></clipPath>`,
    `<linearGradient id="fade" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c.accent}" stop-opacity="0.30"/><stop offset="1" stop-color="#1DB954" stop-opacity="0.18"/></linearGradient></defs>`,
    `<rect width="${W}" height="${H}" rx="12" fill="${c.card}"/>`,
    `<rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="12" fill="none" stroke="${c.border}"/>`,
  ];

  if (d.artUri) {
    out.push(`<image x="20" y="${artY}" width="${ART}" height="${ART}" clip-path="url(#art)" preserveAspectRatio="xMidYMid slice" href="${d.artUri}"/>`);
  } else {
    out.push(
      `<rect x="20" y="${artY}" width="${ART}" height="${ART}" rx="9" fill="url(#fade)"/>` +
      `<text x="${20 + ART / 2}" y="${artY + ART / 2 + 12}" text-anchor="middle" font-family="${FONT}" font-size="34" fill="${c.mute}">♫</text>`
    );
  }
  out.push(`<rect x="20.5" y="${artY + 0.5}" width="${ART - 1}" height="${ART - 1}" rx="9" fill="none" stroke="${c.border}"/>`);

  out.push(logo(W - 34, 30, c));
  out.push(equaliser(colX, 46, c, live));
  out.push(`<text x="${colX + 33}" y="46" font-family="${MONO}" font-size="10.5" letter-spacing="0.09em" font-weight="700" fill="${labelFill}">${esc(label)}</text>`);
  out.push(`<text x="${colX}" y="74" font-family="${FONT}" font-size="15.5" font-weight="700" fill="${c.text}">${esc(fit(title, 15.5, colW))}</text>`);
  out.push(`<text x="${colX}" y="95" font-family="${FONT}" font-size="12.5" fill="${c.dim}">${esc(fit(artist, 12.5, colW))}</text>`);
  if (album) {
    out.push(`<text x="${colX}" y="113" font-family="${FONT}" font-size="11" fill="${c.mute}">${esc(fit(album, 11, colW))}</text>`);
  }

  const barX = colX;
  const barW = 254;
  const barY = 132;
  if (state === "playing" || state === "paused") {
    const dur = Math.max(1, d.duration || 1);
    const pos = Math.min(dur, d.progress || 0);
    const filled = (barW * pos) / dur;
    out.push(`<rect x="${barX}" y="${barY}" width="${barW}" height="4" rx="2" fill="${c.track}"/>`);

    if (live) {
      // This endpoint renders per request, so `pos` is exact at page load.
      // From there the bar and the counter run on the viewer's own clock --
      // the only way a static image can keep time, since nothing in a README
      // is allowed to poll. It is a projection from a true starting point:
      // skip the track and a reload puts it right.
      const remaining = Math.min(dur - pos, 600000); // cap the animation at 10m
      const secs = Math.max(1, Math.round(remaining / 1000));
      const endFilled = (barW * (pos + remaining)) / dur;

      out.push(
        `<rect x="${barX}" y="${barY}" width="${filled.toFixed(1)}" height="4" rx="2" fill="${c.accent}">` +
        `<animate attributeName="width" from="${filled.toFixed(1)}" to="${endFilled.toFixed(1)}" dur="${secs}s" fill="freeze"/>` +
        `</rect>`
      );
      out.push(
        `<circle cy="${barY + 2}" r="3.5" fill="${c.accent}">` +
        `<animate attributeName="cx" from="${(barX + filled).toFixed(1)}" to="${(barX + endFilled).toFixed(1)}" dur="${secs}s" fill="freeze"/>` +
        `<animate attributeName="r" values="3.5;4.6;3.5" dur="1.9s" repeatCount="indefinite"/>` +
        `</circle>`
      );

      // SMIL cannot animate text content, so the elapsed readout is one text
      // node per second, each revealed for exactly its own second.
      const startSec = Math.floor(pos / 1000);
      let frames = "";
      for (let i = 0; i <= secs; i++) {
        frames +=
          `<text x="${barX}" y="152" font-family="${MONO}" font-size="9.5" fill="${c.mute}" opacity="0">` +
          `${ms((startSec + i) * 1000)}<set attributeName="opacity" to="1" begin="${i}s" dur="1s"/></text>`;
      }
      out.push(frames);
      out.push(
        `<circle cx="${barX + barW / 2 - 24}" cy="149" r="3" fill="${c.ok}">` +
        `<animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/></circle>` +
        `<text x="${barX + barW / 2 - 16}" y="152" font-family="${MONO}" font-size="9" letter-spacing="0.08em" fill="${c.ok}">LIVE</text>`
      );
    } else {
      out.push(`<rect x="${barX}" y="${barY}" width="${filled.toFixed(1)}" height="4" rx="2" fill="${c.accent}"/>`);
      out.push(`<text x="${barX}" y="152" font-family="${MONO}" font-size="9.5" fill="${c.mute}">${ms(pos)}</text>`);
      out.push(`<text x="${barX + barW / 2}" y="152" text-anchor="middle" font-family="${MONO}" font-size="9" fill="${c.mute}">paused · ${new Date().toISOString().slice(11, 16)} utc</text>`);
    }

    out.push(`<text x="${barX + barW}" y="152" text-anchor="end" font-family="${MONO}" font-size="9.5" fill="${c.mute}">${ms(dur)}</text>`);
  } else {
    out.push(`<text x="${colX}" y="140" font-family="${MONO}" font-size="9.5" fill="${c.mute}">source: spotify web api · live at ${new Date().toISOString().slice(11, 16)} utc</text>`);
  }

  out.push("</svg>");
  return out.join("");
}

// -------------------------------------------------------------------- http

export default async function handler(req, res) {
  const theme =
    new URL(req.url, "http://x").searchParams.get("theme") === "light"
      ? "light"
      : "dark";

  let data;
  try {
    data = await collect();
    data.artUri = await fetchArt(data.art);
  } catch (err) {
    // Render an honest card rather than a broken image. A 500 here would show
    // the reader a broken-image icon on the profile.
    console.error("spotify:", err?.message || err);
    data = { state: "error" };
  }

  res.setHeader("Content-Type", "image/svg+xml; charset=utf-8");
  // Ask every cache in the path, GitHub's image proxy included, not to hold
  // this. Freshness is the entire reason this endpoint exists.
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("Expires", "0");
  res.status(200).send(card(data, theme));
}

// Exported for the render test in scratch; the HTTP entry point is default.
export { card };
