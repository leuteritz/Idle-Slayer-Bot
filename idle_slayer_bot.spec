# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
        'PIL._tkinter_finder',
        'bot.core.bot',
        'bot.core.key_handler',
        'bot.window.manager',
        'bot.window.input',
        'bot.vision.capture',
        'bot.vision.matcher',
        'bot.minigames.chest_hunt',
        'bot.minigames.bonus_stage',
        'bot.memory.reader',
        'bot.memory.scanner',
        'bot.memory.format',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='idle_slayer_bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
