# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all textual data files and modules
textual_datas = collect_data_files('textual')
textual_hiddenimports = collect_submodules('textual')

# Collect dns_debugger modules
dns_debugger_hiddenimports = collect_submodules('dns_debugger')

a = Analysis(
    ['src/dns_debugger/__main__.py'],
    pathex=[],
    binaries=[],
    datas=textual_datas,
    hiddenimports=[
        'click',
        'httpx',
        'whodap',
        'whois',
        'cryptography',
        'dns_debugger',
        'dns_debugger.app',
        'dns_debugger.adapters',
        'dns_debugger.adapters.dns',
        'dns_debugger.adapters.dns.factory',
        'dns_debugger.domain',
        'dns_debugger.domain.models',
        'dns_debugger.domain.models.dns_record',
    ] + textual_hiddenimports + dns_debugger_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='d',
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
