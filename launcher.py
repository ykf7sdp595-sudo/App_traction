"""Point d'entrée du programme Windows autonome."""
import argparse
import multiprocessing
from pathlib import Path
import socket
import threading
import time
from urllib.request import urlopen
import webbrowser


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
    print('Gardez cette fenêtre ouverte. Pour arrêter : Ctrl+C ou fermez cette fenêtre.', flush=True)
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
    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    bootstrap.run(str(Path(__file__).resolve().with_name('app.py')), False, [], options)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
