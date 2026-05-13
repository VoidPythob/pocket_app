# -*- mode: python ; coding: utf-8 -*-
import os

BASE_DIR = os.getcwd()
MAIN_FILE = os.path.join(BASE_DIR, "src", "pocket_app", "main.py")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")


def collect_resources(src_dir, dst_dir):
    datas = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(root, src_dir)
            if rel_path == ".":
                target = dst_dir
            else:
                target = os.path.join(dst_dir, rel_path)
            datas.append((src_path, target))
    return datas


a = Analysis(  # type: ignore
    [MAIN_FILE],
    pathex=[BASE_DIR],
    binaries=[],
    datas=collect_resources(RESOURCES_DIR, "resources"),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)  # type: ignore

exe = EXE(  # type: ignore
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pocket-app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="x86_64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(  # type: ignore
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pocket-app-win32",
)
