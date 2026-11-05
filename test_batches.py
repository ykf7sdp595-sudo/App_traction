import unittest
from dataclasses import replace
from batches import lot_statistics
from processing import Settings
from readers import read_measurement


def curve(name, force, lot="A"):
    content = "Allongement;Force standard\n" + "\n".join(f"{i};{v}" for i, v in enumerate(force))
    return dict(identity=name, name=name, label=name, lot=lot, valid=True, include_stats=True,
                visible=True, data=read_measurement(content.encode()),
                mapping={"force": 1, "displacement": 0, "time": None},
                units={"force": "N", "displacement": "mm", "time": "s"}, settings=Settings())


class BatchTests(unittest.TestCase):
    def test_reference_statistics_and_separate_lots(self):
        curves = [curve("a", [1, 2]), curve("b", [1, 4]), curve("c", [1, 6]), curve("d", [10], "B")]
        details, summary = lot_statistics(curves)
        self.assertEqual(len(details), 4)
        self.assertEqual(summary[0]["Moyenne (N)"], 4)
        self.assertEqual(summary[0]["Médiane (N)"], 4)
        self.assertEqual(summary[0]["Écart-type échantillon (N)"], 2)
        self.assertIsNone(summary[1]["Écart-type échantillon (N)"])

    def test_exclusions_and_visibility(self):
        a, b, c = curve("a", [4]), curve("b", [-2]), curve("c", [6])
        a["visible"] = False
        c["include_stats"] = False
        details, summary = lot_statistics([a, b, c])
        self.assertEqual(summary[0]["Retenues"], 1)
        self.assertEqual(summary[0]["Exclues"], 2)
        self.assertEqual(summary[0]["Moyenne (N)"], 4)
        self.assertEqual(details[2]["Statut"], "Exclusion manuelle")

    def test_absolute_and_failed_processing(self):
        a = curve("a", [-6, 2])
        details, _ = lot_statistics([a], "Maximum absolu")
        self.assertEqual(details[0]["Valeur (N)"], 6)
        a["settings"] = Settings(preload=True, threshold=99)
        details, summary = lot_statistics([a])
        self.assertIn("jamais atteint", details[0]["Statut"])
        self.assertEqual(summary[0]["Retenues"], 0)
        self.assertIsNone(summary[0]["Moyenne (N)"])

    def test_filter_opt_in(self):
        a = curve("a", [0, 9, 0])
        a["settings"] = Settings(smoothing=True, window=3)
        self.assertEqual(lot_statistics([a])[0][0]["Valeur (N)"], 9)
        self.assertEqual(lot_statistics([a], filtered=True)[0][0]["Valeur (N)"], 4.5)
