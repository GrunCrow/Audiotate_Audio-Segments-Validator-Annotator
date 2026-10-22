# Generic one-file build; for branded filenames use app_windows.spec or app_linux.spec.
import sys
import os
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], ["tkinter.filedialog"]
for package in (
    "gradio", "gradio_client", "librosa", "soundfile", "matplotlib",
    "scipy", "numba", "llvmlite", "pandas",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [os.path.join(SPECPATH, "app.py")], pathex=[SPECPATH], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [], name="Audiotate",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=True, disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
    icon=os.path.join(SPECPATH, "assets", "audiotate.ico") if sys.platform == "win32" else None,
)
