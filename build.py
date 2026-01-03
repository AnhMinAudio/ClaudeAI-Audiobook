"""
Build script for AnhMin Audio
Dong goi ung dung thanh executable
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    print("=" * 50)
    print("AnhMin Audio - Build Script")
    print("=" * 50)

    # Xac dinh platform
    is_windows = sys.platform.startswith('win')
    is_macos = sys.platform == 'darwin'

    # Duong dan venv
    venv_dir = Path('.venv')
    if is_windows:
        python_exe = venv_dir / 'Scripts' / 'python.exe'
        pip_exe = venv_dir / 'Scripts' / 'pip.exe'
    else:
        python_exe = venv_dir / 'bin' / 'python'
        pip_exe = venv_dir / 'bin' / 'pip'

    # Kiem tra venv
    if not python_exe.exists():
        print("ERROR: Virtual environment not found!")
        print(f"Please create venv first: python -m venv .venv")
        sys.exit(1)

    print(f"Using Python: {python_exe}")
    print(f"Platform: {sys.platform}\n")

    # Clean old build artifacts
    print("Step 1: Cleaning old build artifacts...")
    import shutil
    folders_to_clean = ['build', 'dist']
    files_to_clean = ['AnhMinAudio.spec']

    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"  Removing {folder}/")
            shutil.rmtree(folder)

    for file in files_to_clean:
        if os.path.exists(file):
            print(f"  Removing {file}")
            os.remove(file)

    print("  Clean complete!\n")

    # Kiem tra va cai PyInstaller
    print("Step 2: Checking PyInstaller...")
    try:
        result = subprocess.run(
            [str(pip_exe), 'show', 'pyinstaller'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("PyInstaller not found. Installing...")
            subprocess.run(
                [str(pip_exe), 'install', 'pyinstaller'],
                check=True
            )
            print("PyInstaller installed successfully!")
        else:
            print("PyInstaller already installed.")
    except Exception as e:
        print(f"ERROR: Failed to install PyInstaller: {e}")
        sys.exit(1)

    # Xay dung arguments
    print("\nStep 3: Building arguments...")

    args = [
        str(python_exe),
        '-m', 'PyInstaller',
        'main.py',
        '--name=AnhMinAudio',
        '--windowed',
        '--onedir',
        '--noconfirm',

        # Hidden imports
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=anthropic',
        '--hidden-import=docx',
        '--hidden-import=bs4',
        '--hidden-import=selenium',
        '--hidden-import=sqlite3',
        '--hidden-import=gdown',  # For auto-update from Google Drive
        '--hidden-import=packaging',  # For version comparison in auto-update
        '--hidden-import=requests',  # For downloading updates
        '--hidden-import=urllib3',  # Dependency of requests
        '--hidden-import=certifi',  # SSL certificates for requests
        '--hidden-import=charset_normalizer',  # Dependency of requests
        '--hidden-import=filelock',  # Dependency of gdown
        '--hidden-import=tqdm',  # Dependency of gdown (progress bar)

        # Exclude
        '--exclude-module=matplotlib',
        '--exclude-module=PIL',
        '--exclude-module=tkinter',
    ]

    # Tim va them data files tu packages
    print("\nStep 4: Locating package data files...")
    separator = ';' if is_windows else ':'

    # Add icon if exists (use absolute path for embedding in EXE)
    icon_path = Path('app_icon.ico').resolve()
    if icon_path.exists():
        print(f"  Found app icon: {icon_path}")
        # Use absolute path string for --icon to ensure it's embedded in EXE
        args.append(f'--icon={str(icon_path)}')
        # Also add icon as data file for runtime loading
        args.append(f'--add-data={str(icon_path)}{separator}.')
    else:
        print("  Warning: app_icon.ico not found. Build will proceed without icon.")

    # Tim faster_whisper assets (neu co)
    site_packages = venv_dir / ('Lib/site-packages' if is_windows else 'lib/python*/site-packages')
    if is_windows:
        faster_whisper_path = venv_dir / 'Lib' / 'site-packages' / 'faster_whisper'
    else:
        # Tim thu muc site-packages
        import glob
        sp_dirs = glob.glob(str(venv_dir / 'lib' / 'python*' / 'site-packages'))
        faster_whisper_path = Path(sp_dirs[0]) / 'faster_whisper' if sp_dirs else None

    if faster_whisper_path and faster_whisper_path.exists():
        assets_path = faster_whisper_path / 'assets'
        if assets_path.exists():
            print(f"  Found faster_whisper assets: {assets_path}")
            args.append(f'--add-data={assets_path}{separator}faster_whisper/assets')
        else:
            print("  Warning: faster_whisper/assets not found")
    else:
        print("  Info: faster_whisper not installed (optional)")

    # Add data files (platform-specific)
    if is_windows:
        args.extend([
            '--add-data=README.md;.',
            '--add-data=requirements.txt;.',
        ])
    else:
        args.extend([
            '--add-data=README.md:.',
            '--add-data=requirements.txt:.',
        ])

    # Chay PyInstaller
    print(f"\nStep 5: Running PyInstaller...")
    print(f"Command: {' '.join(args[:4])} ...")
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with exit code {e.returncode}")
        sys.exit(1)

    # Kiem tra ket qua
    if is_windows:
        exe_path = Path('dist') / 'AnhMinAudio' / 'AnhMinAudio.exe'
    else:
        exe_path = Path('dist') / 'AnhMinAudio' / 'AnhMinAudio'

    if exe_path.exists():
        print("\n" + "=" * 50)
        print("BUILD SUCCESS!")
        print("=" * 50)
        print(f"Executable: {exe_path}")

        # Tinh kich thuoc
        size_bytes = sum(f.stat().st_size for f in Path('dist/AnhMinAudio').rglob('*') if f.is_file())
        size_mb = size_bytes / (1024 * 1024)
        print(f"Size: {size_mb:.1f} MB")

        print(f"\nTo run:")
        if is_windows:
            print(f"  dist\\AnhMinAudio\\AnhMinAudio.exe")
        else:
            print(f"  dist/AnhMinAudio/AnhMinAudio")
    else:
        print("\nERROR: Executable not found after build!")
        sys.exit(1)

if __name__ == '__main__':
    main()
