# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller import log as logging

logger = logging.getLogger(__name__)
logger.info("Optimizing imports and dependencies for Jira Worklog Importer")

block_cipher = None

# Main analysis configuration
a = Analysis(
    ['main.py'],
    binaries=[],
    datas=[
        # Application data files
        # ('autolog/*', 'autolog'),
    ],
    hiddenimports=[
        'jira',
        'keyring.backends',
        'keyring.backends.Windows',
        'keyring.backends.macOS',
        'keyring.backends.SecretService',
        'customtkinter',
        'aiohttp',
        'PIL'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'unittest', 'pytest', 'test', 'tests',
        'black', 'isort', 'flake8', 'autoflake', 'ruff'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create the pyz archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
    exclude_imports=[
        'PIL'
    ]
)

# Single executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='AutoLog',
    version="version.txt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)