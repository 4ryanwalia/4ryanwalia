/**
 * TEMPORARY diagnostic. Reports whether each variable is visible to the
 * function and how long it is — never the value itself. Delete after use.
 */
export default function handler(req, res) {
  const probe = (name) => {
    const raw = process.env[name];
    return {
      present: typeof raw === "string",
      length: typeof raw === "string" ? raw.length : 0,
      blankAfterTrim: typeof raw === "string" ? raw.trim().length === 0 : null,
    };
  };
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({
    node: process.version,
    SPOTIFY_CLIENT_ID: probe("SPOTIFY_CLIENT_ID"),
    SPOTIFY_CLIENT_SECRET: probe("SPOTIFY_CLIENT_SECRET"),
    SPOTIFY_REFRESH_TOKEN: probe("SPOTIFY_REFRESH_TOKEN"),
    spotifyKeysVisible: Object.keys(process.env).filter((k) =>
      k.startsWith("SPOTIFY_")
    ),
  });
}
