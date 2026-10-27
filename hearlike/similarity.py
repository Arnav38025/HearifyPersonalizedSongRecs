"""Similarity: turn feature vectors into a ranking with reasons.

Tempo uses a log-ratio distance that treats half/double time as close (70 BPM
and 140 BPM feel related). Key uses circle-of-fifths distance plus a mode
penalty. Energy, brightness, and timbre are z-scored across the candidate pool
so every component speaks the same language before weighting.
"""

from __future__ import annotations

import math

import numpy as np

WEIGHTS = {"tempo": 0.30, "key": 0.25, "timbre": 0.25, "energy": 0.10, "brightness": 0.10}


def tempo_distance(t1: float, t2: float) -> float:
    """0..1. Octave-equivalent tempos score 0 (70 vs 140 BPM)."""
    if t1 <= 0 or t2 <= 0:
        return 1.0
    ratio = math.log2(t1 / t2)
    wrapped = min(abs(ratio - k) for k in (-1, 0, 1))
    return min(wrapped * 2.0, 1.0)


def _fifths_position(tonic: int) -> int:
    return (tonic * 7) % 12


def key_distance(a: dict, b: dict) -> float:
    """0..1 from circle-of-fifths distance plus a mode-mismatch penalty."""
    d = abs(_fifths_position(a["key_tonic"]) - _fifths_position(b["key_tonic"]))
    d = min(d, 12 - d)
    score = (d / 6.0) * 0.7
    if a["key_mode"] != b["key_mode"]:
        score += 0.3
    return min(score, 1.0)


def _z(value, mean, std):
    """Elementwise z-score; works for scalars and arrays (zero std -> 1)."""
    denom = np.where(np.asarray(std) > 1e-9, std, 1.0)
    return (np.asarray(value) - np.asarray(mean)) / denom


def _capped_z_diff(z1: float, z2: float) -> float:
    return min(abs(z1 - z2) / 3.0, 1.0)


class PoolStats:
    """Per-feature mean/std across a candidate pool, for z-scoring."""

    def __init__(self, vectors: list[dict]):
        self.energy_mean = float(np.mean([v["energy"] for v in vectors]))
        self.energy_std = float(np.std([v["energy"] for v in vectors]))
        self.bright_mean = float(np.mean([v["brightness"] for v in vectors]))
        self.bright_std = float(np.std([v["brightness"] for v in vectors]))
        mfcc_mean = np.array([v["mfcc_mean"] for v in vectors])
        mfcc_std = np.array([v["mfcc_std"] for v in vectors])
        self.mfcc_mean_mean = mfcc_mean.mean(axis=0)
        self.mfcc_mean_std = mfcc_mean.std(axis=0)
        self.mfcc_std_mean = mfcc_std.mean(axis=0)
        self.mfcc_std_std = mfcc_std.std(axis=0)

    def timbre_distance(self, a: dict, b: dict) -> float:
        """0..1 Euclidean distance over standardized MFCC means and stds."""
        a_mean = _z(np.array(a["mfcc_mean"]), self.mfcc_mean_mean, self.mfcc_mean_std)
        b_mean = _z(np.array(b["mfcc_mean"]), self.mfcc_mean_mean, self.mfcc_mean_std)
        a_std = _z(np.array(a["mfcc_std"]), self.mfcc_std_mean, self.mfcc_std_std)
        b_std = _z(np.array(b["mfcc_std"]), self.mfcc_std_mean, self.mfcc_std_std)
        d_mean = float(np.linalg.norm(a_mean - b_mean)) / math.sqrt(13)
        d_std = float(np.linalg.norm(a_std - b_std)) / math.sqrt(13)
        return min(((d_mean + 0.5 * d_std) / 1.5) / 3.0, 1.0)


def components(seed: dict, cand: dict, stats: PoolStats) -> dict[str, float]:
    return {
        "tempo": tempo_distance(seed["tempo"], cand["tempo"]),
        "key": key_distance(seed, cand),
        "timbre": stats.timbre_distance(seed, cand),
        "energy": _capped_z_diff(
            _z(seed["energy"], stats.energy_mean, stats.energy_std),
            _z(cand["energy"], stats.energy_mean, stats.energy_std),
        ),
        "brightness": _capped_z_diff(
            _z(seed["brightness"], stats.bright_mean, stats.bright_std),
            _z(cand["brightness"], stats.bright_mean, stats.bright_std),
        ),
    }


def match_score(seed: dict, cand: dict, stats: PoolStats) -> tuple[float, dict[str, float]]:
    """Return (0-100 match score, per-component distances). Identical = 100."""
    comps = components(seed, cand, stats)
    total = sum(WEIGHTS[k] * comps[k] for k in WEIGHTS)
    return 100.0 / (1.0 + 2.0 * total), comps


def rank(seed: dict, candidates: list[tuple[dict, dict]]) -> list[tuple[dict, dict, float, dict]]:
    """Rank (track, features) pairs against the seed. Best match first."""
    stats = PoolStats([seed] + [feat for _, feat in candidates])
    scored = [
        (track, feat, *match_score(seed, feat, stats)) for track, feat in candidates
    ]
    scored.sort(key=lambda item: item[2], reverse=True)
    return scored


def explain(seed: dict, cand: dict, comps: dict[str, float]) -> list[str]:
    """Human-readable reasons, closest components first."""
    reasons = []
    if comps["tempo"] < 0.15:
        reasons.append(f"tempo nearly identical ({seed['tempo']:.0f} vs {cand['tempo']:.0f} BPM)")
    elif comps["tempo"] < 0.35:
        reasons.append(f"tempo close ({seed['tempo']:.0f} vs {cand['tempo']:.0f} BPM)")
    if seed["key"] == cand["key"]:
        reasons.append(f"same key ({seed['key']})")
    elif comps["key"] < 0.3:
        reasons.append(f"neighboring key ({seed['key']} vs {cand['key']})")
    if comps["energy"] < 0.3:
        reasons.append("similar energy")
    if comps["brightness"] < 0.3:
        reasons.append("similar brightness")
    if comps["timbre"] < 0.3:
        reasons.append("similar texture")
    if not reasons:
        reasons.append("closest overall match in the pool")
    return reasons
