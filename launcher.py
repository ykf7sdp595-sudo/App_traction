"""Point d'entrée du programme Windows autonome."""
import argparse
import multiprocessing
from pathlib import Path
import signal
import socket
import threading
import time
from urllib.request import urlopen
import webbrowser


def stop_when_tabs_closed(grace_seconds=15):
    """Arrêter le serveur après fermeture du dernier onglet connecté."""
    from streamlit.runtime.runtime import Runtime, RuntimeState

    connected_once = False
    disconnected_at = None
    while True:
        if Runtime.exists():
            state = Runtime.instance().state
            if state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
                return
            if state == RuntimeState.ONE_OR_MORE_SESSIONS_CONNECTED:
                connected_once = True
                disconnected_at = None
            elif connected_once and state == RuntimeState.NO_SESSIONS_CONNECTED:
                now = time.monotonic()
                if disconnected_at is None:
                    disconnected_at = now
                elif now - disconnected_at >= grace_seconds:
                    print('Dernier onglet fermé : arrêt de l’application.', flush=True)
                    signal.raise_signal(signal.SIGINT)
                    return
        time.sleep(1)


def open_when_ready(url):
    for _ in range(120):
        try:
            with urlopen(url + '/_stcore/health', timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            pass
        time.sleep(0.5)
    print('Ouverture automatique impossible : ouvrez l’adresse ci-dessus.')


def main():
    parser = argparse.ArgumentParser(description='Courbes de traction')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', args.port))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    print(f'App traction : {url}', flush=True)
    print('L’application s’arrête après la fermeture du dernier onglet.', flush=True)
    from streamlit.web import bootstrap
    options = {
        'server.address': '127.0.0.1',
        'server.port': port,
        'server.headless': True,
        'server.fileWatcherType': 'none',
        'server.runOnSave': False,
        'browser.gatherUsageStats': False,
        'global.developmentMode': False,
    }
    bootstrap.load_config_options(flag_options=options)
    threading.Thread(target=stop_when_tabs_closed, daemon=True).start()
    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    bootstrap.run(str(Path(__file__).resolve().with_name('app.py')), False, [], options)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()

