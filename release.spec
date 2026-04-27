# -*- mode: python ; coding: utf-8 -*-
# for release purposes only, sync changes in deep properties and use spec as is for onefile - Vish

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules("mediapipe")
hiddenimports += collect_submodules("onnxruntime")
hiddenimports += collect_submodules("eventlet")
hiddenimports += collect_submodules("engineio")
hiddenimports += collect_submodules("socketio")
hiddenimports += collect_submodules("OpenSSL")
# Critical for eventlet runtime
hiddenimports += [
    "eventlet.green.ssl",
    "eventlet.green.socket",
    "eventlet.green.thread",
    "eventlet.hubs.epolls",
    "eventlet.hubs.selects",
]
hiddenimports += [
    "sklearn",
    "sklearn.tree",
    "sklearn.ensemble",
    "sklearn.base",
    "sklearn.utils",
    "sklearn.preprocessing",
]


datas = []
datas += collect_data_files("mediapipe")
datas += collect_data_files("sklearn")
datas += [("isl_alphabet_model.pkl", ".")]
datas += [("dynamic_sign_model.onnx", ".")]
datas += [("templates", "templates")]
datas += [("static", "static")]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "mediapipe.model_maker",
        "matplotlib.tests",
        "numpy.tests",
        "IPython",
        "notebook",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SignBridge",
    console=False,          # GUI release
    icon="logo.ico",
    upx=False,
    strip=False,
    onefile=True,
)
