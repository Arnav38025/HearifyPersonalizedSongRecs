"""Command line: hearlike "Marvins Room" --artist Drake --limit 10"""

from __future__ import annotations

import argparse
import sys

from . import cache, itunes, similarity
from .features import extract_features


def analyze(track: itunes.Track) -> dict | None:
    """Analyze a track's preview, reusing the disk cache when possible."""
    feats = cache.load_features()
    cached = feats.get(str(track.track_id))
    if cached:
        return cached
    path = cache.preview_path(track.track_id)
    if not path.exists():
        if not track.preview_url or not itunes.download_preview(track.preview_url, str(path)):
            return None
    try:
        feat = extract_features(str(path))
    except Exception:
        return None
    feats[str(track.track_id)] = feat
    cache.save_features(feats)
    return feat


def find_similar(
    title: str, artist: str | None, extra_queries: list[str], limit: int, pool_cap: int
) -> tuple[itunes.Track, dict, list]:
    seed = itunes.search_seed(title, artist)
    if seed is None:
        raise SystemExit(f"could not find '{title}' on iTunes")
    print(f"seed: {seed.label()} [{seed.genre}]")
    seed_feat = analyze(seed)
    if seed_feat is None:
        raise SystemExit("could not analyze the seed preview")
    print(
        f"  {seed_feat['tempo']:.0f} BPM · {seed_feat['key']} · "
        f"energy {seed_feat['energy']:.3f}"
    )
    pool = itunes.gather_candidates(seed, extra_queries, cap=pool_cap)
    print(f"candidate pool: {len(pool)} songs")
    analyzed = []
    for track in pool:
        feat = analyze(track)
        if feat is not None:
            analyzed.append((track, feat))
    print(f"analyzed: {len(analyzed)} songs")
    ranked = similarity.rank(seed_feat, analyzed)
    return seed, seed_feat, ranked[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hearlike",
        description="Find songs that sound like a song you like, by listening to the audio.",
    )
    parser.add_argument("title", help="seed song title")
    parser.add_argument("--artist", default=None, help="seed song artist")
    parser.add_argument(
        "--query", action="append", default=[],
        help="extra iTunes search to widen the candidate pool (repeatable)",
    )
    parser.add_argument("--limit", type=int, default=10, help="matches to show")
    parser.add_argument("--pool-cap", type=int, default=40, help="candidate pool size")
    args = parser.parse_args(argv)

    _, seed_feat, ranked = find_similar(
        args.title, args.artist, args.query, args.limit, args.pool_cap
    )
    print()
    for i, (track, feat, score, comps) in enumerate(ranked, 1):
        reasons = "; ".join(similarity.explain(seed_feat, feat, comps))
        print(f"{i}. {score:.0f}%  {track.label()}")
        print(f"   {feat['tempo']:.0f} BPM · {feat['key']} · {reasons}")
        print(f"   preview: {track.preview_url}")
        print(f"   listen: {track.store_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
