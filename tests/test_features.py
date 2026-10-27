import unittest

import numpy as np
import soundfile as sf

from hearlike.features import estimate_key, extract_features


def write_wav(path, y, sr=22050):
    sf.write(path, y, sr)


class TestFeatures(unittest.TestCase):
    def test_key_of_c_major_chord(self):
        sr = 22050
        t = np.linspace(0, 3, 3 * sr, endpoint=False)
        # C major triad: C4 + E4 + G4.
        y = (
            np.sin(2 * np.pi * 261.63 * t)
            + np.sin(2 * np.pi * 329.63 * t)
            + np.sin(2 * np.pi * 392.00 * t)
        ).astype(np.float32) / 3.0
        write_wav("/tmp/c_major.wav", y, sr)
        feat = extract_features("/tmp/c_major.wav")
        self.assertEqual(feat["key"], "C major")

    def test_click_track_tempo(self):
        sr = 22050
        y = np.zeros(10 * sr, dtype=np.float32)
        # Clicks every 0.5 s -> 120 BPM.
        for i in range(20):
            start = int(i * 0.5 * sr)
            y[start : start + 200] = 0.9
        write_wav("/tmp/clicks.wav", y, sr)
        feat = extract_features("/tmp/clicks.wav")
        self.assertAlmostEqual(feat["tempo"], 120.0, delta=3.0)

    def test_vector_shape(self):
        sr = 22050
        rng = np.random.default_rng(0)
        y = rng.normal(0, 0.1, sr * 2).astype(np.float32)
        write_wav("/tmp/noise.wav", y, sr)
        feat = extract_features("/tmp/noise.wav")
        self.assertEqual(len(feat["mfcc_mean"]), 13)
        self.assertEqual(len(feat["mfcc_std"]), 13)
        self.assertGreater(feat["tempo"], 0)


if __name__ == "__main__":
    unittest.main()
