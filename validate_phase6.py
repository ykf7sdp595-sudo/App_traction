"""Validation reproductible et mesures côté Python, sans navigateur.

Lancer avec le Python du projet. Génère validation_results.json.
Les acquisitions de charge sont des copies en mémoire, pas des essais indépendants.
"""

from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import json
from pathlib import Path
import platform
from time import perf_counter
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).parent
NAMES = ["Crimp tensile - cosse_1.TRA", "Force insertion  retention contact.CSV", "Data_260602_155441.txt"]


def upload(name, content):
    file = BytesIO(content)
    file.name = name
    return file


def check(app):
    if app.exception:
        raise AssertionError([str(e.value) for e in app.exception])


def figure(app):
    return json.loads(app.session_state.chart_payload["spec"])


def main():
    sources = [(name, (ROOT / name).read_bytes()) for name in NAMES]
    hashes = {name: sha256(content).hexdigest() for name, content in sources}
    report = {"python": platform.python_version(), "system": platform.platform(),
              "streamlit": version("streamlit"), "plotly": version("plotly"),
              "source_sha256": hashes, "campaigns": [],
              "limits": "AppTest : temps Python, hors navigateur, zoom, clic réel et export PNG. Copies en mémoire des trois exemples."}
    for size in (15, 30, 60):
        files = [upload(f"{i + 1:02d}_{sources[i % 3][0]}", sources[i % 3][1]) for i in range(size)]
        with patch("streamlit.file_uploader", return_value=files):
            start = perf_counter()
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
            first_seconds = perf_counter() - start
            check(app)
            graph = figure(app)
            assert len(graph["data"]) == size
            expected = (size // 3) * (941 + 478 + 6797)
            assert sum(len(t["x"]) for t in graph["data"]) == expected
            start = perf_counter()
            next(w for w in app.text_input if w.label == "Titre").set_value("Validation campagne").run()
            check(app)
            rerun_seconds = perf_counter() - start
            start = perf_counter()
            app.checkbox(key="batch_stats").check().run()
            check(app)
            summary = next(df.value for df in app.dataframe if "Retenues" in df.value.columns)
            assert summary.iloc[0]["Retenues"] == size
            expected_mean = (65.37660217285 + 0.3055521249771 + 173.65) / 3
            assert abs(summary.iloc[0]["Moyenne (N)"] - expected_mean) < 1e-9
            stats_seconds = perf_counter() - start
            report["campaigns"].append(dict(curves=size, points=expected,
                initial_seconds=round(first_seconds, 3), rerun_seconds=round(rerun_seconds, 3),
                statistics_seconds=round(stats_seconds, 3), plot_json_mb=round(len(json.dumps(graph).encode()) / 1_000_000, 3)))
            print(json.dumps(report["campaigns"][-1]), flush=True)
    with patch("streamlit.file_uploader", return_value=[upload(*sources[0]),
               upload("invalide.csv", b"Allongement;Force standard\n0;NaN"),
               upload("point_unique.TRA", b"Allongement;Force standard\n0;5")]):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        check(app)
        assert len(figure(app)["data"]) == 2 and app.error
        assert figure(app)["data"][1]["mode"] == "markers"
        report["mixed_invalid_and_single_point"] = "PASS"
    assert all(sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    report["sources_unchanged"] = True
    (ROOT / "validation_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Validation terminée : validation_results.json", flush=True)


if __name__ == "__main__":
    main()
