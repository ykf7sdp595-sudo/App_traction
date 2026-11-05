"""Contrôle local Edge sans fenêtre : composant Plotly, légende et PNG.

Utilise websockets déjà installé par Streamlit. Ne touche pas au navigateur
utilisateur : profil temporaire et serveur de test propres à ce script.
"""
import base64
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from websockets.sync.client import connect

ROOT = Path(__file__).parent
FIXTURE = '''
import sys, runpy
from pathlib import Path
from io import BytesIO
from hashlib import sha256
from unittest.mock import patch
import streamlit as st
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
files=[]
for name in ("Crimp tensile - cosse_1.TRA", "Force insertion  retention contact.CSV", "Data_260602_155441.txt"):
    content=(root/name).read_bytes()
    file=BytesIO(content); file.name=name; files.append(file)
if "free_events" not in st.session_state:
    identity=sha256(files[0].name.encode()+b"\\0"+files[0].getvalue()).hexdigest()
    st.session_state.free_events={identity:[dict(id="validation", title="Contact", point=100, color="#c62828", visible=True)]}
with patch("streamlit.file_uploader", return_value=files):
    runpy.run_path(str(root/"app.py"), run_name="__main__")
'''


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    edge = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe"
    app_port, debug_port = port(), port()
    with tempfile.TemporaryDirectory(prefix="traction_browser_") as temporary:
        temp = Path(temporary)
        fixture = temp / "fixture.py"
        fixture.write_text(FIXTURE, encoding="utf-8")
        processes = []
        with (ROOT / "browser_validation.log").open("w", encoding="utf-8") as log:
            try:
                processes.append(subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(fixture),
                    "--server.headless", "true", "--server.address", "127.0.0.1", "--server.port", str(app_port),
                    "--browser.gatherUsageStats", "false", "--", str(ROOT)], stdout=log, stderr=log,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
                processes.append(subprocess.Popen([str(edge), "--headless=new", "--no-first-run",
                    "--remote-debugging-port=" + str(debug_port), "--user-data-dir=" + str(temp / "profile"),
                    "about:blank"], stdout=log, stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)))
                deadline = time.monotonic() + 30
                while True:
                    try:
                        with urlopen(f"http://127.0.0.1:{debug_port}/json", timeout=1) as response:
                            target = next(p for p in json.load(response) if p["type"] == "page")
                        with urlopen(f"http://127.0.0.1:{app_port}/_stcore/health", timeout=1):
                            break
                    except (OSError, StopIteration):
                        if time.monotonic() > deadline:
                            raise RuntimeError("Démarrage trop long ; consulter browser_validation.log")
                        time.sleep(0.3)
                with connect(target["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
                    serial = 0
                    def command(method, params=None):
                        nonlocal serial
                        serial += 1
                        ws.send(json.dumps(dict(id=serial, method=method, params=params or {})))
                        while True:
                            message = json.loads(ws.recv(timeout=30))
                            if message.get("id") == serial:
                                if "error" in message:
                                    raise RuntimeError(message["error"])
                                return message.get("result", {})
                    def evaluate(expression):
                        result = command("Runtime.evaluate", dict(expression=expression, returnByValue=True, awaitPromise=True))
                        if "exceptionDetails" in result:
                            raise RuntimeError(result["exceptionDetails"])
                        return result.get("result", {}).get("value")
                    def wait_for(expression):
                        deadline = time.monotonic() + 45
                        while not evaluate(expression):
                            if time.monotonic() > deadline:
                                raise RuntimeError("Condition non satisfaite : " + expression)
                            time.sleep(0.3)
                    command("Page.navigate", dict(url=f"http://127.0.0.1:{app_port}"))
                    plot = "document.querySelector('.traction-plot')"
                    wait_for(f"!!{plot}?.data?.length")
                    assert evaluate(f"{plot}.data.length") == 4
                    evaluate(f"{plot}.emit('plotly_legendclick', {{curveNumber:0}})")
                    wait_for(f"{plot}?.data?.[0]?.visible === 'legendonly'")
                    assert evaluate(f"{plot}.data[3].visible") is False
                    assert evaluate(f"{plot}.layout.annotations[0].visible") is False
                    evaluate(f"{plot}.emit('plotly_legendclick', {{curveNumber:0}})")
                    wait_for(f"{plot}?.data?.[0]?.visible !== 'legendonly' && {plot}?.data?.[3]?.visible !== false")
                    # Vérifier le clic de placement après remplacement du rendu natif.
                    evaluate("Array.from(document.querySelectorAll('label')).find(e => e.textContent.includes('Placer un évènement sur une courbe')).querySelector('input').click()")
                    wait_for(f"{plot}?.data?.[0]?.customdata?.[0]?.[0] === 'event'")
                    evaluate(f"{plot}.emit('plotly_click', {{points:[{{customdata:{plot}.data[0].customdata[199]}}]}})")
                    selector = json.dumps("Point source de l'évènement")
                    wait_for("Array.from(document.querySelectorAll('input')).some(e => e.getAttribute('aria-label') === " + selector + " && e.value === '200')")
                    wait_for(f"{plot}?.data?.length === 5 && {plot}?.layout?.annotations?.length === 2")
                    assert evaluate("document.querySelector('.traction-feedback').textContent.includes('200')")
                    # Le même clic ne doit pas produire un second marqueur.
                    evaluate(f"{plot}.emit('plotly_click', {{points:[{{customdata:{plot}.data[0].customdata[199]}}]}})")
                    wait_for("document.querySelector('.traction-feedback').textContent.includes('déjà')")
                    assert evaluate(f"{plot}.data.length") == 5
                    evaluate("Array.from(document.querySelectorAll('button')).find(e => e.textContent.includes('Annuler le dernier marqueur')).click()")
                    wait_for(f"{plot}?.data?.length === 4 && {plot}?.layout?.annotations?.length === 1")
                    assert evaluate("document.querySelector('.traction-feedback').textContent.includes('annulé')")
                    evaluate(f"window.Plotly.relayout({plot}, {{'annotations[0].ax':90, 'annotations[0].ay':-80}}).then(() => true)")
                    uri = evaluate(f"window.Plotly.toImage({plot}, {{format:'png', width:1600, height:900}})")
                    png = base64.b64decode(uri.split(",", 1)[1])
                    assert struct.unpack(">II", png[16:24]) == (1600, 900)
                    (ROOT / "validation_chart.png").write_bytes(png)
                    print("PASS : graphique réel, légende, placement immédiat au point 200, confirmation, anti-doublon, annulation, déplacement d'étiquette, PNG 1600x900.")
            finally:
                for process in reversed(processes):
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
