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
        ('autolog/*', 'autolog'),
        
        # Collect CustomTkinter resources
        *collect_data_files('customtkinter', include_py_files=True),
        
        # Collect JIRA dependencies
        *collect_data_files('jira'),

        # Collect AioHTTP dependencies
        *collect_data_files('aiohttp'),

        # Collect Keyring dependencies
        *collect_data_files('keyring'),
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
        'unittest', 'pytest', 'test', 'tests',                   # Testing frameworks
        'black', 'isort', 'flake8', 'autoflake', 'ruff'          # Testing frameworks
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

# Additional optimizations for Windows
if sys.platform == 'win32':
    exe = exe.to_win32pe(exe)
    logger.info("Applying Windows PE optimizations")