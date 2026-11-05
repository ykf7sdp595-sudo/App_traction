"""Test du parcours Streamlit sans navigateur (dépendances installées requises)."""

from pathlib import Path
import json
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


def chart_element(app):
    payload = app.session_state.chart_payload
    return SimpleNamespace(proto=SimpleNamespace(spec=payload["spec"], config=json.dumps(payload["config"])))


@unittest.skipIf(AppTest is None, "Streamlit non installé dans ce Python")
class InterfaceTests(unittest.TestCase):
    def setUp(self):
        # Les fichiers de référence sont injectés comme des imports utilisateur.
        files = []
        for name in ("Crimp tensile - cosse_1.TRA", "Force insertion  retention contact.CSV", "Data_260602_155441.txt"):
            file = BytesIO(Path(__file__).with_name(name).read_bytes())
            file.name = name
            files.append(file)
        uploader = patch("streamlit.file_uploader", return_value=files)
        uploader.start()
        self.addCleanup(uploader.stop)

    def test_free_event_marker_lifecycle(self):
        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
        app.checkbox(key="event_enabled").check().run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        self.assertEqual(figure["layout"]["clickmode"], "event+select")
        self.assertEqual(figure["data"][0]["customdata"][0][0], "event")
        app.checkbox(key="event_click").uncheck().run()
        next(w for w in app.number_input if w.label == "Point source de l'évènement").set_value(100).run()
        app.text_input(key="event_title").set_value("Début glissement").run()
        next(w for w in app.button if w.label == "Ajouter ce marqueur").click().run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        annotation = next(a for a in figure["layout"]["annotations"] if "_event_" in a["name"])
        self.assertEqual(annotation["text"], "Début glissement")
        self.assertEqual(annotation["x"], figure["data"][0]["x"][99])
        # Le marqueur reste présent quand le mode d'ajout est fermé.
        app.checkbox(key="event_enabled").uncheck().run()
        self.assertTrue(json.loads(chart_element(app).proto.spec)["layout"]["annotations"])
        next(w for w in app.checkbox if w.label == "Afficher cet évènement").uncheck().run()
        self.assertFalse(json.loads(chart_element(app).proto.spec)["layout"].get("annotations"))
        next(w for w in app.button if w.label == "Supprimer cet évènement").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(any(app.session_state.free_events.values()))

    def test_batch_assignment_copy_and_statistics(self):
        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
        # AppTest uses the underlying identity values, obtainable via each lot widget key.
        identities = [w.key[:-3] for w in app.text_input if w.label == "Lot"]
        next(w for w in app.selectbox if w.label == "Correction de force").select("Valeur saisie").run()
        next(w for w in app.number_input if w.label == "Force à soustraire (N)").set_value(2.0)
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        app.multiselect(key="batch_targets").set_value(identities[:2]).run()
        app.text_input(key="batch_lot_name").set_value("Essai groupé").run()
        next(w for w in app.button if w.label == "Affecter le lot aux courbes cibles").click().run()
        next(w for w in app.button if w.label == "Appliquer les traitements aux courbes cibles").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state[identities[1] + "_treatment_applied"].offset, 2.0)
        app.selectbox(key="batch_filter").select("Essai groupé").run()
        app.checkbox(key="batch_stats").check().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(json.loads(chart_element(app).proto.spec)["data"]), 2)
        summary = next(df.value for df in app.dataframe if "Retenues" in df.value.columns)
        self.assertEqual(summary.iloc[0]["Courbes"], 2)
        self.assertEqual(summary.iloc[0]["Retenues"], 1)  # CSV devient entièrement négatif après -2 N.
        # Plage valable pour le modèle (941 points), impossible pour le CSV (478).
        next(w for w in app.checkbox if w.label == "Limiter à une zone").check().run()
        next(w for w in app.number_input if w.label == "Zone : dernier point").set_value(900)
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        next(w for w in app.button if w.label == "Appliquer les traitements aux courbes cibles").click().run()
        self.assertFalse(app.exception)
        self.assertIn("non appliqué", app.session_state.batch_report)
        self.assertFalse(app.session_state[identities[1] + "_treatment_applied"].crop)

    def test_analysis_and_zones(self):
        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
        next(w for w in app.checkbox if w.label == "Activer l'analyse et les annotations").check().run()
        next(w for w in app.selectbox if w.label == "Extrême de force").select("Maximum positif").run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        marker = next(t for t in figure["data"] if "Maximum positif" in t["name"])
        self.assertAlmostEqual(marker["customdata"][0][1], 65.37660217285)
        next(w for w in app.checkbox if w.label == "Détecter les pics").check().run()
        next(w for w in app.text_input if w.label.startswith("Pics manuels")).set_value("100").run()
        next(w for w in app.checkbox if w.label == "Rechercher une rupture candidate").check().run()
        self.assertTrue(any("Aucune rupture candidate" in w.value for w in app.info))
        next(w for w in app.checkbox if w.label == "Choisir manuellement le point de rupture").check().run()
        next(w for w in app.number_input if w.label == "Point source de rupture").set_value(100).run()
        next(w for w in app.checkbox if w.label == "Confirmer l'évènement comme rupture").check().run()
        next(w for w in app.number_input if w.label == "Nombre de zones").set_value(2).run()
        next(w for w in app.text_input if w.label == "Évènement physique").set_value("Insertion").run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        zones = [a for a in figure["layout"]["annotations"] if "_zone_" in a["name"]]
        self.assertEqual(len(zones), 2)
        self.assertEqual(zones[0]["text"], "Insertion")
        maximum_label = next(a for a in figure["layout"]["annotations"] if "Maximum positif" in a["name"])
        self.assertTrue(maximum_label["showarrow"])
        self.assertAlmostEqual(maximum_label["y"], 65.37660217285)
        config = json.loads(chart_element(app).proto.config)
        self.assertTrue(config["edits"]["annotationTail"])
        self.assertFalse(config["edits"]["annotationPosition"])
        revision = figure["layout"]["editrevision"]
        next(w for w in app.checkbox if w.label == "Déplacer les étiquettes à la souris").uncheck().run()
        self.assertFalse(json.loads(chart_element(app).proto.config)["edits"]["annotationTail"])
        self.assertEqual(json.loads(chart_element(app).proto.spec)["layout"]["editrevision"], revision)
        next(w for w in app.button if w.label == "Réinitialiser la position des étiquettes").click().run()
        self.assertNotEqual(json.loads(chart_element(app).proto.spec)["layout"]["editrevision"], revision)
        self.assertTrue(any("Pic manuel" in t["name"] for t in figure["data"]))
        self.assertTrue(any("Rupture confirmée" in t["name"] for t in figure["data"]))
        # Une nouvelle correction de force doit invalider la confirmation physique.
        next(w for w in app.selectbox if w.label == "Correction de force").select("Valeur saisie").run()
        next(w for w in app.number_input if w.label == "Force à soustraire (N)").set_value(1.0)
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(next(w for w in app.checkbox if w.label == "Confirmer l'évènement comme rupture").value)

    def test_apply_compare_error_and_reset(self):
        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
        baseline = json.loads(chart_element(app).proto.spec)["data"][0]
        self.assertTrue(next(w for w in app.number_input if w.label == "Force à soustraire (N)").disabled)
        next(w for w in app.selectbox if w.label == "Correction de force").select("Valeur saisie").run()
        self.assertFalse(next(w for w in app.number_input if w.label == "Force à soustraire (N)").disabled)
        next(w for w in app.number_input if w.label == "Force à soustraire (N)").set_value(10.0).run()
        self.assertEqual(json.loads(chart_element(app).proto.spec)["data"][0]["y"], baseline["y"])
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        corrected = json.loads(chart_element(app).proto.spec)["data"][0]["y"]
        self.assertEqual(corrected, [v - 10 for v in baseline["y"]])
        next(w for w in app.number_input if w.label == "Force à soustraire (N)").set_value(2.0)
        next(w for w in app.checkbox if w.label == "Limiter à une zone").check().run()
        next(w for w in app.number_input if w.label == "Zone : premier point").set_value(10)
        next(w for w in app.number_input if w.label == "Zone : dernier point").set_value(20)
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        self.assertFalse(app.exception)
        trace = json.loads(chart_element(app).proto.spec)["data"][0]
        self.assertEqual(trace["customdata"], list(range(10, 21)))
        self.assertAlmostEqual(trace["y"][0], baseline["y"][9] - 2)
        next(w for w in app.checkbox if w.label == "Comparer au signal brut").check().run()
        self.assertEqual(len(json.loads(chart_element(app).proto.spec)["data"]), 4)
        next(w for w in app.checkbox if w.label == "Retirer le début avant précharge").check().run()
        next(w for w in app.number_input if w.label == "Seuil de précharge (N, amplitude positive)").set_value(1000.0)
        next(w for w in app.button if w.label == "Appliquer à cette courbe").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertEqual(len(json.loads(chart_element(app).proto.spec)["data"]), 2)
        next(w for w in app.button if w.label == "Réinitialiser les traitements").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        restored = json.loads(chart_element(app).proto.spec)["data"][0]
        self.assertEqual(restored["x"], baseline["x"])
        self.assertEqual(restored["y"], baseline["y"])

    def test_examples_views_and_export_settings(self):
        app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.exception)
        chart = chart_element(app)
        self.assertEqual(len(app.tabs), 3)
        for tab in app.tabs:
            self.assertTrue(any(w.label == "Correction de force" for w in tab.selectbox))
            self.assertTrue(any(w.label == "Activer l'analyse et les annotations" for w in tab.checkbox))
        figure = json.loads(chart.proto.spec)
        self.assertEqual(len(figure["data"]), 3)
        self.assertEqual([len(t["x"]) for t in figure["data"]], [941, 478, 6797])
        config = json.loads(chart.proto.config)
        self.assertEqual(config["toImageButtonOptions"]["format"], "png")
        self.assertEqual(config["toImageButtonOptions"]["width"], 1600)
        next(w for w in app.selectbox if w.label == "Axes").select("Force / temps").run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        self.assertEqual(len(figure["data"]), 1)
        self.assertEqual(figure["data"][0]["x"][0], 3.839)
        self.assertEqual(max(figure["data"][0]["y"]), 173.65)
        next(w for w in app.selectbox if w.label == "Axes").select("Déplacement / temps").run()
        self.assertFalse(app.exception)
        figure = json.loads(chart_element(app).proto.spec)
        self.assertEqual(min(figure["data"][0]["y"]), -2.067)


if __name__ == "__main__":
    unittest.main()
