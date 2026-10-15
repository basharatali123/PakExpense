"""
Automated PyInstaller Build Script for PakExpense Tracker.
Compiles the Python app + SQLite engine into a standalone Windows Executable (.exe).
"""
import os
import sys
import subprocess
import shutil

def build():
    print("=" * 60)
    print("Building PakExpenseTracker Windows Executable (.exe)...")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    # Clean previous build artifacts
    for d in [dist_dir, build_dir]:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            shutil.rmtree(d, ignore_errors=True)

    # PyInstaller arguments
    # --noconsole: Prevents the black command prompt window from showing
    # --collect-all customtkinter: Bundles customtkinter themes, fonts, and assets
    # --add-data: Bundles sample data
    # --onefile: Packages everything into a single standalone .exe file
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PakExpenseTracker",
        "--onefile",
        "--windowed",
        "--collect-all=customtkinter",
        f"--add-data={os.path.join(base_dir, 'sample_data')};sample_data",
        "--hidden-import=sqlite3",
        "--hidden-import=csv",
        "--hidden-import=xml.etree.ElementTree",
        os.path.join(base_dir, "app.py")
    ]

    print("Running PyInstaller command:")
    print(" ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "PakExpenseTracker.exe")
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Executable created at: {exe_path}")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Size: {size_mb:.2f} MB")
        print("=" * 60)
    else:
        print(f"\nBuild failed with exit code: {result.returncode}")

if __name__ == "__main__":
    build()
