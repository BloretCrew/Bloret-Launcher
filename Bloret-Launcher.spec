# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir（非 onefile）规格：产物为 dist/Bloret-Launcher/ 目录。

a = Analysis(
    ['Bloret-Launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
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
    ],
    hiddenimports=[
        'sip',
        'qfluentwidgets',
        'win11toast',
        'toml',
        'winsdk',
    ],
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
