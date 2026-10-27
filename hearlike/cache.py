"""On-disk cache for preview audio and extracted features.

Feature vectors are cached by iTunes track id, so repeat runs (and the demo)
don't re-download or re-analyze songs. Nothing secret lives here: track ids
and numbers derived from public 30-second previews.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def cache_dir() -> Path:
    path = Path(os.environ.get("HEARLIKE_CACHE", Path.home() / ".cache" / "hearlike"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def preview_path(track_id: int) -> Path:
    return cache_dir() / f"{track_id}.m4a"


def _features_file() -> Path:
    return cache_dir() / "features.json"


def load_features() -> dict:
    try:
        return json.loads(_features_file().read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_features(features: dict) -> None:
    _features_file().write_text(json.dumps(features))
