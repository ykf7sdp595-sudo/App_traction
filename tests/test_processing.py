import unittest
from processing import Settings, moving_average, process


class ProcessingTests(unittest.TestCase):
    def test_empty_active_numeric_fields(self):
        configs = [Settings(offset_mode="Valeur saisie", offset=None),
                   Settings(preload=True, threshold=None), Settings(smoothing=True, window=None),
                   Settings(crop=True, interval=(None, 4)),
                   Settings(offset_mode="Moyenne d'une zone", reference=(1, None))]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                process({"force": [1, 2, 3, 4, 5]}, config)

    def setUp(self):
        self.raw = {"force": [2, 2, 5, 8, 2], "time": [4, 5, 6, 7, 8],
                    "displacement": [0, 1, 2, 1, 0]}

    def test_identity_and_no_mutation(self):
        data, points, notes = process(self.raw, Settings())
        self.assertEqual(data, self.raw)
        self.assertEqual(points, [1, 2, 3, 4, 5])
        self.assertEqual(notes, [])
        data["force"][0] = 100
        self.assertEqual(self.raw["force"][0], 2)

    def test_order_offset_preload_origin_crop(self):
        config = Settings(offset_mode="Moyenne d'une zone", reference=(1, 2),
                          preload=True, threshold=3, zero_time=True,
                          zero_displacement=True, crop=True, interval=(4, 5))
        data, points, _ = process(self.raw, config)
        self.assertEqual(points, [4, 5])
        self.assertEqual(data, {"force": [6, 0], "time": [1, 2], "displacement": [-1, -2]})
        self.assertEqual(self.raw["force"], [2, 2, 5, 8, 2])

    def test_negative_and_absolute_preload(self):
        for direction in ("Négative", "Valeur absolue"):
            data, points, _ = process({"force": [0, -1, -5, 3]}, Settings(preload=True, threshold=4, direction=direction))
            self.assertEqual(points, [3, 4])
            self.assertEqual(data["force"], [-5, 3])

    def test_filter_edges_and_zone_order(self):
        self.assertEqual(moving_average([0, 0, 9, 0, 0], 3), [0, 3, 3, 3, 0])
        data, points, _ = process({"force": [0, 0, 9, 0, 0]}, Settings(smoothing=True, window=3, crop=True, interval=(3, 3)))
        self.assertEqual(data["force"], [3])
        self.assertEqual(points, [3])
        self.assertEqual(moving_average([2, 2, 2], 3), [2, 2, 2])

    def test_invalid_settings(self):
        configs = [Settings(preload=True, threshold=99), Settings(preload=True, threshold=0),
                   Settings(crop=True, interval=(4, 2)), Settings(smoothing=True, window=4),
                   Settings(smoothing=True, window=7), Settings(offset_mode="Moyenne d'une zone", reference=(0, 2)),
                   Settings(preload=True, threshold=7, crop=True, interval=(1, 2))]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                process(self.raw, config)
        with self.assertRaises(ValueError):
            process({"time": [1, 2]}, Settings(smoothing=True))


if __name__ == "__main__":
    unittest.main()
