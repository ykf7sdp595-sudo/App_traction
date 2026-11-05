"""Démarre un serveur de contrôle isolé, vérifie sa santé puis l'arrête."""

from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen


def main():
    root = Path(__file__).parent
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    log = root / "startup_validation.log"
    with log.open("w", encoding="utf-8") as output:
        child = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(root / "app.py"),
            "--server.address", "127.0.0.1", "--server.port", str(port),
            "--server.headless", "true", "--browser.gatherUsageStats", "false"],
            cwd=root, stdout=output, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError("Arrêt du serveur ; consulter startup_validation.log")
                try:
                    with urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                        if response.status == 200:
                            print(f"PASS : serveur local opérationnel sur le port de test {port}.")
                            return
                except OSError:
                    time.sleep(0.2)
            raise RuntimeError("Le serveur de contrôle n'a pas répondu en 20 secondes.")
        finally:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
