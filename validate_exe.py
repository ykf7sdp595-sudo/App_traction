"""Vérifie le binaire copié seul, avec PATH sans Python, dans Edge headless."""
import base64
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
from urllib.request import urlopen

from websockets.sync.client import connect
from validate_browser import port

ROOT = Path(__file__).resolve().parent


def main():
    edge = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe'
    app_port, debug_port = port(), port()
    with tempfile.TemporaryDirectory(prefix='traction_exe_') as temporary:
        temp = Path(temporary)
        executable = temp / 'App_traction.exe'
        shutil.copy2(ROOT / 'dist/App_traction.exe', executable)
        env = os.environ.copy()
        env['PATH'] = os.environ['SystemRoot'] + '\\System32'
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        processes = []
        with (ROOT / 'exe_validation.log').open('w', encoding='utf-8') as log:
            try:
                processes.append(subprocess.Popen([str(executable), '--no-browser', '--port', str(app_port)],
                    cwd=temp, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW))
                processes.append(subprocess.Popen([str(edge), '--headless=new', '--no-first-run',
                    '--remote-debugging-port=' + str(debug_port), '--user-data-dir=' + str(temp / 'profile'),
                    'about:blank'], stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW))
                deadline = time.monotonic() + 120
                while True:
                    try:
                        with urlopen(f'http://127.0.0.1:{debug_port}/json', timeout=1) as response:
                            target = next(p for p in json.load(response) if p['type'] == 'page')
                        with urlopen(f'http://127.0.0.1:{app_port}/_stcore/health', timeout=1):
                            break
                    except (OSError, StopIteration):
                        if processes[0].poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError('Échec du démarrage : consulter exe_validation.log')
                        time.sleep(0.3)
                with connect(target['webSocketDebuggerUrl'], max_size=20_000_000) as ws:
                    serial = 0

                    def command(method, params=None):
                        nonlocal serial
                        serial += 1
                        ws.send(json.dumps(dict(id=serial, method=method, params=params or {})))
                        while True:
                            message = json.loads(ws.recv(timeout=30))
                            if message.get('id') == serial:
                                if 'error' in message:
                                    raise RuntimeError(message['error'])
                                return message.get('result', {})

                    def evaluate(expression):
                        result = command('Runtime.evaluate', dict(expression=expression, returnByValue=True, awaitPromise=True))
                        if 'exceptionDetails' in result:
                            raise RuntimeError(result['exceptionDetails'])
                        return result.get('result', {}).get('value')

                    def wait_for(expression):
                        deadline = time.monotonic() + 60
                        while not evaluate(expression):
                            if time.monotonic() > deadline:
                                raise RuntimeError('Condition non satisfaite : ' + expression + '\n' + str(evaluate('document.body.innerText')))
                            time.sleep(0.3)

                    command('Page.navigate', dict(url=f'http://127.0.0.1:{app_port}'))
                    wait_for("!!document.querySelector('input[type=file]')")
                    document = command('DOM.getDocument')
                    node = command('DOM.querySelector', dict(nodeId=document['root']['nodeId'], selector='input[type=file]'))
                    files = ['Crimp tensile - cosse_1.TRA', 'Force insertion  retention contact.CSV', 'Data_260602_155441.txt']
                    command('DOM.setFileInputFiles', dict(nodeId=node['nodeId'], files=[str(ROOT / name) for name in files]))
                    plot = "document.querySelector('.traction-plot')"
                    wait_for(f'{plot}?.data?.length === 3')
                    assert sorted(evaluate(f'{plot}.data.map(t => t.x.length)')) == [478, 941, 6797]
                    assert not evaluate("!!document.querySelector('[data-testid=stException]')")
                    evaluate(f"{plot}.emit('plotly_legendclick', {{curveNumber:0}})")
                    wait_for(f"{plot}?.data?.[0]?.visible === 'legendonly'")
                    evaluate(f"{plot}.emit('plotly_legendclick', {{curveNumber:0}})")
                    wait_for(f"{plot}?.data?.[0]?.visible !== 'legendonly'")
                    uri = evaluate(f"window.Plotly.toImage({plot}, {{format:'png', width:1600, height:900}})")
                    png = base64.b64decode(uri.split(',', 1)[1])
                    assert struct.unpack('>II', png[16:24]) == (1600, 900)
                    print('PASS : EXE copié seul, PATH sans Python, import TRA/CSV/TXT, 3 courbes, légende interactive, export PNG 1600x900.')
            finally:
                for process in reversed(processes):
                    if process.poll() is None:
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=log, stderr=log, check=False)
                        process.wait(timeout=15)


if __name__ == '__main__':
    main()
