"""iTunes Search API client.

The iTunes Search API is public and needs no key or login. Every song result
can carry a 30-second preview URL, which is the audio hearlike analyzes.
"""

from __future__ import annotations

import requests

SEARCH_URL = "https://itunes.apple.com/search"


class Track(dict):
    """A song from iTunes, with the fields hearlike needs."""

    @property
    def track_id(self) -> int:
        return self["trackId"]

    @property
    def title(self) -> str:
        return self.get("trackName", "")

    @property
    def artist(self) -> str:
        return self.get("artistName", "")

    @property
    def album(self) -> str:
        return self.get("collectionName", "")

    @property
    def genre(self) -> str:
        return self.get("primaryGenreName", "")

    @property
    def preview_url(self) -> str | None:
        return self.get("previewUrl")

    @property
    def store_url(self) -> str:
        return self.get("trackViewUrl", "")

    @property
    def artwork(self) -> str:
        return self.get("artworkUrl100", "")

    def label(self) -> str:
        return f"{self.title} — {self.artist}"


def search(term: str, limit: int = 20) -> list[Track]:
    """Search iTunes for songs matching a term. Returns [] on any failure."""
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"term": term, "media": "music", "entity": "song", "limit": limit},
            timeout=20,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []
    return [Track(r) for r in resp.json().get("results", []) if r.get("previewUrl")]


def _norm(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def search_seed(title: str, artist: str | None = None) -> Track | None:
    """Find the best iTunes match for a seed song, preferring an artist match."""
    term = f"{title} {artist}" if artist else title
    results = search(term, limit=10)
    if not results:
        return None
    want_title = _norm(title)
    if artist:
        want_artist = _norm(artist)
        for track in results:
            if want_artist in _norm(track.artist) and want_title in _norm(track.title):
                return track
    return results[0]


def gather_candidates(
    seed: Track, extra_queries: list[str], per_query: int = 10, cap: int = 40
) -> list[Track]:
    """Build a candidate pool: the seed artist's other songs, the seed's genre,
    plus any user-supplied queries. Deduped, seed excluded, previews only."""
    queries = [seed.artist, seed.genre] + extra_queries
    seen: set[int] = {seed.track_id}
    pool: list[Track] = []
    for query in queries:
        if not query:
            continue
        for track in search(query, limit=per_query):
            if track.track_id in seen:
                continue
            seen.add(track.track_id)
            pool.append(track)
            if len(pool) >= cap:
                return pool
    return pool


def download_preview(url: str, dest_path: str) -> bool:
    """Download a preview clip to dest_path. Returns False on any failure."""
    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
    except requests.RequestException:
        return False
    return True
