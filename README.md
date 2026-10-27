# 🎧 hearlike

Find songs that sound like a song you like — by actually listening to the audio.

Type a song. hearlike grabs its 30-second preview, measures tempo, key,
energy, brightness, and timbre from the waveform itself, does the same for a
pool of candidates, and ranks them by how close they sound — with a
human-readable reason for every match ("same key, 72 vs 74 BPM, similar
energy"). No genre tags, no lyrics, no "people who liked X also liked Y."

## Why this exists

Every recommendation engine you've used reasons about music from *text*:
genre labels, artist associations, popularity, lyrics. Two songs can share a
genre tag and feel nothing alike, and a language model can't tell — it has no
ears. hearlike measures the sound.

It also exists because the old way broke: in November 2024 Spotify deprecated
its audio-features and recommendations endpoints for third-party developers,
which killed the tools built on them. hearlike doesn't depend on Spotify at
all. It uses the iTunes Search API (public, no key, no login) for previews and
computes every feature locally with librosa.

How it differs from the nearest neighbors:

- **Lyrics/metadata recommenders** (e.g. TF-IDF on lyrics): same failure mode
  as a chatbot — text, not sound.
- **Static-dataset k-NN demos**: rank a fixed CSV of old Spotify features.
  They can't analyze a song you name.
- **AudioMuse-AI**: excellent sonic analysis, but only for your own
  self-hosted music library. hearlike discovers *new* songs.
- **Commercial similar-song sites**: closed source, accounts, paywalls.
  hearlike is open, zero-key, and runs on your machine.

## Install

```bash
pip install -e .
```

You also need ffmpeg (librosa uses it to decode the `.m4a` previews):

```bash
brew install ffmpeg        # macOS
sudo apt install ffmpeg    # Ubuntu/Debian
```

## Use

```bash
# CLI: seed song, then ranked matches with reasons + preview links
hearlike "Marvins Room" --artist Drake --limit 10 \
  --query "PARTYNEXTDOOR" --query "The Weeknd" --query "Bryson Tiller"

# Web UI with playable previews
python -m streamlit run hearlike/app.py
```

Candidate pool: the seed artist's other songs, the seed's genre, and any
`--query` searches you add. Feature vectors are cached in
`~/.cache/hearlike`, so repeat runs are fast.

## How similarity works

| Component | Weight | What it measures |
| --- | --- | --- |
| Tempo | 30% | Log-ratio distance; half/double time counts as close (70 vs 140 BPM) |
| Key | 25% | Circle-of-fifths distance + major/minor mismatch penalty |
| Timbre | 25% | Standardized MFCC means and stds (the texture of the sound) |
| Energy | 10% | RMS loudness, z-scored across the pool |
| Brightness | 10% | Spectral centroid, z-scored across the pool |

Key is estimated by correlating the song's chromagram against
Krumhansl-Schmuckler major/minor profiles. Score is `100 / (1 + 2·distance)`,
so an identical song scores 100.

## Limitations, stated plainly

- **30-second previews, not full songs.** That's the ceiling for every
  independent tool now — streaming platforms don't license full audio to
  third parties. BPM is robust on clips; key detection is noisier.
- **Catalog = what iTunes search returns.** Not literally every song ever.
- **First run is slow**: every candidate preview gets downloaded and
  analyzed once, then cached.
- **Preview audio ≠ the full track**: an intro-heavy preview can skew energy
  and brightness. The "why" breakdown exists so you can judge matches
  yourself instead of trusting a black box.

## License

MIT
