import unittest

from analysis import detect_peaks, extreme, rupture_candidate


class AnalysisTests(unittest.TestCase):
    def test_extreme_signs_ties_and_endpoints(self):
        self.assertEqual(extreme([0, 4, 4, -8], "Maximum positif"), 1)
        self.assertEqual(extreme([0, 4, 4, -8], "Minimum négatif"), 3)
        self.assertEqual(extreme([0, 4, 4, -8], "Maximum absolu"), 3)
        self.assertIsNone(extreme([-1, 0], "Maximum positif"))
        self.assertIsNone(extreme([1, 2], "Minimum négatif"))

    def test_plateaus_and_signs(self):
        peaks = detect_peaks([0, 5, 5, 0, -4, -4, 0], relief=1, distance=1)
        self.assertEqual([(p.index, p.force, p.relief) for p in peaks], [(1, 5, 5), (4, -4, 4)])
        self.assertEqual(detect_peaks([0, 1, 2, 3]), [])
        self.assertEqual(detect_peaks([3, 3, 3]), [])
        self.assertEqual(detect_peaks([4]), [])

    def test_relief_and_spacing(self):
        values = [0, 5, 4, 8, 0]
        self.assertEqual([p.index for p in detect_peaks(values, relief=2, distance=1)], [3])
        self.assertEqual([p.index for p in detect_peaks(values, relief=0, distance=3)], [3])
        self.assertEqual([p.index for p in detect_peaks(values, relief=0, distance=2)], [1, 3])

    def test_rupture_window_and_no_forced_break(self):
        self.assertEqual(rupture_candidate([0, 20, 19, 2], drop=10, window=2, minimum=15), (1, 3))
        self.assertIsNone(rupture_candidate([0, 20, 19, 18], drop=10, window=2, minimum=15))
        self.assertIsNone(rupture_candidate([0, 20, 16, 12, 8], drop=10, window=2, minimum=15))
        self.assertIsNone(rupture_candidate([0, 5, 0], drop=3, window=2, minimum=10))
        self.assertEqual(rupture_candidate([0, -20, -2], drop=10, minimum=15, direction="Négative"), (1, 2))


if __name__ == "__main__":
    unittest.main()
