# Construction Windows : .venv/Scripts/python.exe -m PyInstaller App_traction.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH)
datas, binaries, hiddenimports = collect_all('streamlit')
pdata, pbins, pimports = collect_all('plotly')
datas += pdata
binaries += pbins
hiddenimports += pimports
for package in ('streamlit', 'plotly', 'pandas', 'numpy'):
    datas += copy_metadata(package)
modules = ['readers', 'processing', 'analysis', 'batches', 'treatment_ui',
           'analysis_ui', 'batch_ui', 'events_ui', 'chart_ui', 'curve_summary']
# Les sources sont nécessaires à l'introspection des composants Streamlit v2.
datas += [(str(root / (name + '.py')), '.') for name in ['app'] + modules]
hiddenimports += modules + ['streamlit.web.bootstrap']
a = Analysis([str(root / 'launcher.py')], pathex=[str(root)],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='App_traction',
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=True)
