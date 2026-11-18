import unittest
from curve_summary import build_summary


def item(identity, force):
    return dict(curve=dict(identity=identity, label=identity), points=[1, 2, 3],
                y=force, signals=dict(force=force))


class SummaryTests(unittest.TestCase):
    def test_events_missing_values_and_statistics(self):
        rendered = [item("a", [2, 4, 6]), item("b", [4, 8, 12])]
        events = {"a": [dict(title="Contact", point=1, visible=True),
                         dict(title="Verrou", point=2, visible=True),
                         dict(title="Fin", point=3, visible=True)],
                  "b": [dict(title="Contact", point=2, visible=True)]}
        rows, stats = build_summary(rendered, events, {}, "Force (N)")
        self.assertEqual(len(rows[0]), 6)  # courbe, 2 extrêmes, 3 marqueurs
        self.assertEqual(rows[0]["Évènement — Contact (N)"], 2)
        self.assertEqual(rows[1]["Évènement — Contact (N)"], 8)
        self.assertIsNone(rows[1]["Évènement — Verrou (N)"])
        self.assertEqual(stats[0]["Évènement — Contact (N)"], 5)
        self.assertAlmostEqual(stats[3]["Évènement — Contact (N)"], 18 ** 0.5)
        self.assertIsNone(stats[3]["Évènement — Verrou (N)"])
        rows, _ = build_summary(rendered, events, {"a": True}, "Force (N)")
        self.assertEqual(len(rows), 1)
        self.assertNotIn("Évènement — Verrou (N)", rows[0])
        self.assertEqual(build_summary(rendered, events, {"a": True, "b": True}, "Force (N)"), ([], []))

    def test_duplicate_names_and_hidden_or_cropped_events(self):
        events = {"a": [dict(title="Test", point=1, visible=True),
                         dict(title="Test", point=3, visible=True),
                         dict(title="Masqué", point=2, visible=False),
                         dict(title="Hors zone", point=9, visible=True)]}
        rows, _ = build_summary([item("a", [1, 2, 3])], events, {}, "Force (N)")
        self.assertEqual(rows[0]["Évènement — Test [2] (N)"], 3)
        self.assertEqual(len(rows[0]), 5)
