import unittest

from hearlike import similarity


def vec(tempo=100.0, tonic=0, mode="major", energy=0.10, bright=2000.0):
    return {
        "tempo": tempo,
        "key_tonic": tonic,
        "key_mode": mode,
        "key": f"{tonic} {mode}",
        "energy": energy,
        "brightness": bright,
        "mfcc_mean": [0.0] * 13,
        "mfcc_std": [0.0] * 13,
    }


class TestSimilarity(unittest.TestCase):
    def test_identical_scores_100(self):
        seed = vec()
        stats = similarity.PoolStats([seed, vec()])
        score, _ = similarity.match_score(seed, vec(), stats)
        self.assertAlmostEqual(score, 100.0)

    def test_octave_tempo_is_close(self):
        # 70 vs 140 BPM: half/double time feels related, not distant.
        self.assertLess(similarity.tempo_distance(70, 140), 0.05)
        self.assertGreater(similarity.tempo_distance(70, 110), 0.3)

    def test_key_distance(self):
        # C major -> G major is one step on the circle of fifths.
        self.assertLess(
            similarity.key_distance(vec(tonic=0), vec(tonic=7)),
            similarity.key_distance(vec(tonic=0), vec(tonic=6)),
        )
        # Mode mismatch costs extra.
        self.assertGreater(
            similarity.key_distance(vec(mode="major"), vec(mode="minor")),
            similarity.key_distance(vec(mode="major"), vec(mode="major")),
        )

    def test_ranking_order(self):
        seed = vec()
        near = vec(tempo=102.0)
        far = vec(tempo=160.0, tonic=6, mode="minor", energy=0.9, bright=9000.0)
        ranked = similarity.rank(seed, [("far", far), ("near", near)])
        self.assertEqual(ranked[0][0], "near")
        self.assertGreater(ranked[0][2], ranked[1][2])

    def test_explain_mentions_same_key(self):
        seed = vec()
        stats = similarity.PoolStats([seed, vec()])
        _, comps = similarity.match_score(seed, vec(), stats)
        reasons = similarity.explain(seed, vec(), comps)
        self.assertTrue(any("same key" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
