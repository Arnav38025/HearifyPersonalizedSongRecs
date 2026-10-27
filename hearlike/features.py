"""Audio feature extraction with librosa.

Every number here is measured from the actual audio, not read from a tag or
an API field. That is the whole point: two songs can share a genre label and
sound nothing alike, but they can't share a tempo, key, and timbre by accident.
"""

from __future__ import annotations

import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Schmuckler key profiles: how strongly each pitch class belongs to
# a key, from listener experiments. Correlating a song's chroma against these
# (rotated to every tonic, major and minor) gives its key.
_MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)


def estimate_key(chroma: np.ndarray) -> tuple[int, str]:
    """Estimate (tonic pitch class 0-11, 'major'/'minor') from a chroma vector."""
    best_tonic, best_mode, best_score = 0, "major", -2.0
    for tonic in range(12):
        for mode, profile in (("major", _MAJOR_PROFILE), ("minor", _MINOR_PROFILE)):
            rotated = np.roll(profile, tonic)
            score = float(np.corrcoef(chroma, rotated)[0, 1])
            if score > best_score:
                best_tonic, best_mode, best_score = tonic, mode, score
    return best_tonic, best_mode


def key_name(tonic: int, mode: str) -> str:
    return f"{NOTE_NAMES[tonic]} {mode}"


def _load_audio(path: str):
    """Load audio as (y, sr). Falls back to an ffmpeg transcode for formats
    libsndfile can't read — iTunes previews are .m4a (AAC), which it can't."""
    import librosa

    try:
        return librosa.load(path, sr=22050, mono=True)
    except Exception:
        pass
    import os
    import subprocess
    import tempfile

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", path,
             "-ac", "1", "-ar", "22050", tmp.name],
            check=True, timeout=60,
        )
        return librosa.load(tmp.name, sr=22050, mono=True)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def extract_features(audio_path: str) -> dict:
    """Extract hearlike's feature vector from an audio file.

    Returns a JSON-able dict: tempo (BPM), key, energy (RMS loudness),
    brightness (spectral centroid), and MFCC means/stds (timbre).
    """
    import librosa

    y, sr = _load_audio(audio_path)
    if len(y) == 0:
        raise ValueError(f"no audio decoded from {audio_path}")

    # librosa moved tempo estimation across releases; try each location.
    tempo_fn = getattr(librosa.feature, "tempo", None)
    if tempo_fn is None:
        try:
            from librosa.feature import rhythm as _rhythm

            tempo_fn = _rhythm.tempo
        except ImportError:
            tempo_fn = librosa.beat.tempo
    tempo = float(tempo_fn(y=y, sr=sr)[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    tonic, mode = estimate_key(chroma)
    rms = float(np.mean(librosa.feature.rms(y=y)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    return {
        "tempo": round(tempo, 1),
        "key_tonic": tonic,
        "key_mode": mode,
        "key": key_name(tonic, mode),
        "energy": round(rms, 4),
        "brightness": round(centroid, 1),
        "mfcc_mean": [round(float(v), 4) for v in mfcc.mean(axis=1)],
        "mfcc_std": [round(float(v), 4) for v in mfcc.std(axis=1)],
    }
