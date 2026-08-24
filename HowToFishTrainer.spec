# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_trainer.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'doctest', 'pydoc', 'pygments', 'setuptools', 'pythonnet', 'clr_loader', 'dnfile', 'multiprocessing', 'asyncio', 'concurrent', 'xml', 'xmlrpc', 'html', 'http', 'email', 'urllib', 'ftplib', 'poplib', 'imaplib', 'smtplib'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='HowToFishTrainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
