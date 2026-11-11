# Externalize Chart and Score Sourcing to 3icecream

Directly scraping Konami's e-amusement service introduces extreme maintenance overhead, IP rate-limiting, and authentication fragility. We decided to treat 3icecream (sanbai) as the upstream authority for chart metadata (`songdata.js`) and user scores (`/dev/api/v1/get_scores` and webhook notifications). This trade-off drastically simplifies PPR X's operational footprint while coupling system availability and data ingestion freshness to 3icecream's API contracts and uptime.
