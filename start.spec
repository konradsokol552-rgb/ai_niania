# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = []
binaries = []
hiddenimports = []

# Zbieramy wszystko dla webview
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# DODANE: Zbieramy metadane i zależności dla Streamlita, żeby nie wyrzucał błędu PackageNotFoundError
st_datas, st_binaries, st_hiddenimports = collect_all('streamlit')
datas += st_datas
binaries += st_binaries
hiddenimports += st_hiddenimports

# Dodatkowe metadane wersji Streamlita
datas += copy_metadata('streamlit')


a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='start',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Zmień na True, gdybyś chciał widzieć okno konsoli z logami w celach debugowania
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)