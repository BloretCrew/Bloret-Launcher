# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir（非 onefile）规格：产物为 dist/Bloret-Launcher/ 目录。
# UI 已迁到 PySide6 + RinUI/QML；不再依赖 qfluentwidgets / sip。

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)


def _opt_data(src: str, dest: str):
    p = root / src
    return [(src, dest)] if p.exists() else []


datas = [
    ('bloret.ico', '.'),
    ('Bloret.png', '.'),
    ('Bloret-Fluent.png', '.'),
    ('config.json', '.'),
    ('ui', 'ui'),
    ('RinUI', 'RinUI'),
    ('qml', 'qml'),
    ('icon', 'icon'),
    ('lang', 'lang'),
    ('modules', 'modules'),
    ('JavaWrapper.jar', '.'),
]
datas += _opt_data('LICENSE', '.')
datas += _opt_data('servers.dat', '.')
datas += _opt_data('easytier', 'easytier')

hiddenimports = [
    'toml',
    'darkdetect',
    'send2trash',
    'psutil',
    'dulwich',
    'qrcode',
    'PIL',
]
# Windows-only；在非 Windows 上 PyInstaller 会忽略缺失模块时仍可能告警，故按平台加入
import sys

if sys.platform == 'win32':
    hiddenimports += ['win11toast', 'winsdk']

a = Analysis(
    ['Bloret-Launcher.py'],
    pathex=['.'],
    binaries=[],
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
    [],
    exclude_binaries=True,
    name='Bloret-Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['bloret.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Bloret-Launcher',
)
