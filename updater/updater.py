"""
AnhMin Audio - Updater
Download and install updates with admin privileges
"""

import os
import sys
import subprocess
import tempfile
import time
import requests
import zipfile
import shutil
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

# CRITICAL FIX: Redirect stdout/stderr to null when running as frozen windowed app
# This prevents crashes from print() and sys.stdout.flush() calls
if getattr(sys, 'frozen', False) and sys.stdout is None:
    if os.name == 'nt':  # Windows
        sys.stdout = open('nul', 'w')
        sys.stderr = open('nul', 'w')
    else:  # Unix-like
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')


class DownloadWorker(QThread):
    """Worker thread for downloading update file."""

    progress = pyqtSignal(int, int)  # (downloaded_bytes, total_bytes)
    finished = pyqtSignal(str, bool)  # (path, is_folder)
    error = pyqtSignal(str)  # error_message
    log_message = pyqtSignal(str)  # log_message for UI display

    def __init__(self, download_url: str, file_name: str):
        super().__init__()
        self.download_url = download_url
        self.file_name = file_name
        self.is_cancelled = False

    def cancel(self):
        """Cancel the download."""
        self.is_cancelled = True

    def run(self):
        """Download the update file and extract if .zip."""
        import traceback
        try:
            print(f"[DEBUG] run() method started")
            sys.stdout.flush()
            self._do_download()
            print(f"[DEBUG] _do_download() completed successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"\n[FATAL ERROR] Exception caught in run():")
            print(f"Exception type: {type(e)}")
            print(f"Exception message: {str(e)}")
            print(traceback.format_exc())
            sys.stdout.flush()
            try:
                self.error.emit(f"Lỗi nghiêm trọng: {str(e)}")
            except Exception as emit_err:
                print(f"[FATAL ERROR] Failed to emit error: {emit_err}")
                sys.stdout.flush()

    def _do_download(self):
        """Internal download implementation."""
        file_path = None
        try:
            # Create temp file
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, self.file_name)

            print(f"[DEBUG] Download URL: {self.download_url}")
            print(f"[DEBUG] File name: {self.file_name}")
            print(f"[DEBUG] Target path: {file_path}")

            self.log_message.emit("🔗 Bắt đầu tải xuống...")

            # Handle Google Drive - use gdown with progress simulation
            if 'drive.google.com' in self.download_url:
                try:
                    import gdown
                    import threading

                    self.log_message.emit("📦 Đang kết nối tới Google Drive...")

                    # Try to estimate file size from Google Drive metadata
                    # Extract file ID for size check
                    import re
                    file_id = None
                    id_match = re.search(r'[?&]id=([^&]+)', self.download_url)
                    if id_match:
                        file_id = id_match.group(1)
                        print(f"[DEBUG] Google Drive File ID: {file_id}")

                    # Use percentage-based progress (0-100) to avoid integer overflow with large files
                    # File size ~2.5 GB would overflow int32 (2^31 - 1 = 2.14 GB max)
                    self.log_message.emit(f"📊 Kích thước ước tính: ~2500 MB")

                    self.log_message.emit("⬇️ Đang tải xuống từ Google Drive...")

                    # Emit initial progress (0%)
                    self.progress.emit(0, 100)

                    # Smooth progress simulation (5% → 85% during download)
                    self._stop_progress_simulation = False

                    def simulate_progress():
                        """Simulate smooth progress during gdown download."""
                        current = 5   # Start at 5%
                        target = 85   # Stop at 85% (leave 15% for extraction)
                        step = 1
                        delay = 1.5  # seconds

                        # Initial progress
                        self.progress.emit(current, 100)

                        while current < target and not self._stop_progress_simulation:
                            time.sleep(delay)

                            if self._stop_progress_simulation or self.is_cancelled:
                                break

                            current += step
                            self.progress.emit(current, 100)

                            # Slow down as approaching target
                            if current > 70:
                                delay = 2.0
                                step = 0.5
                            elif current > 60:
                                delay = 1.8

                        print(f"[DEBUG] Progress simulation stopped at {current}%")

                    # Start simulation thread
                    print(f"[DEBUG] Starting progress simulation thread...")
                    progress_thread = threading.Thread(target=simulate_progress, daemon=True)
                    progress_thread.start()

                    # Download with gdown (blocking call)
                    print(f"[DEBUG] Starting gdown.download()...")
                    gdown.download(self.download_url, file_path, quiet=True, fuzzy=True)

                    # Stop simulation
                    self._stop_progress_simulation = True
                    progress_thread.join(timeout=2.0)
                    print(f"[DEBUG] gdown download completed")

                    # Check if download was successful
                    if not os.path.exists(file_path):
                        raise Exception("Download failed - file not created")

                    # Get actual file size
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)
                    print(f"[DEBUG] Downloaded file size: {file_size_mb:.2f} MB")

                    self.log_message.emit(f"✅ Tải xuống hoàn tất! ({file_size_mb:.1f} MB)")

                    # Emit progress to 87% (download complete, preparing extraction)
                    self.progress.emit(87, 100)

                except Exception as e:
                    import traceback
                    print(f"[DEBUG] Exception in Google Drive download:")
                    print(traceback.format_exc())
                    self.error.emit(f"Lỗi tải từ Google Drive: {str(e)}")
                    return

            else:
                # Regular download with requests (for small files < 2GB)
                self.log_message.emit("🌐 Đang kết nối tới server...")

                response = requests.get(self.download_url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                total_size_mb = total_size / (1024 * 1024)
                self.log_message.emit(f"⬇️ Đang tải xuống ({total_size_mb:.1f} MB)...")

                downloaded = 0
                last_percentage = 0

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.is_cancelled:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            return

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Emit percentage (0-100) to avoid overflow with large files
                            if total_size > 0:
                                percentage = int((downloaded / total_size) * 100)
                                # Only emit when percentage changes (reduce signal spam)
                                if percentage != last_percentage:
                                    self.progress.emit(percentage, 100)
                                    last_percentage = percentage

                self.log_message.emit(f"✅ Tải xuống hoàn tất! ({total_size_mb:.1f} MB)")
                # Ensure 100% is emitted
                self.progress.emit(100, 100)

            print(f"[DEBUG] Exited if-else block for download method")
            sys.stdout.flush()

            print(f"[DEBUG] About to check ZIP...")
            sys.stdout.flush()

            # Check if .zip and extract
            print(f"[DEBUG] About to call endswith()...")
            sys.stdout.flush()

            is_zip = self.file_name.endswith('.zip')
            print(f"[DEBUG] is_zip = {is_zip}")
            sys.stdout.flush()

            print(f"[DEBUG] About to print is_zip check result...")
            sys.stdout.flush()

            print(f"[DEBUG] Checking if file is ZIP: {is_zip}")
            if self.file_name.endswith('.zip'):
                # Extract to temp folder
                extract_dir = os.path.join(temp_dir, 'AnhMinAudio_Update')
                print(f"[DEBUG] Extract directory: {extract_dir}")

                self.log_message.emit("📦 Đang giải nén file ZIP...")
                # Emit 88% progress (extraction starting)
                self.progress.emit(88, 100)

                # Clean up old extract folder if exists
                if os.path.exists(extract_dir):
                    print(f"[DEBUG] Removing old extract folder...")
                    shutil.rmtree(extract_dir)

                # Extract zip
                print(f"[DEBUG] Extracting ZIP file...")
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        num_files = len(zip_ref.namelist())
                        print(f"[DEBUG] ZIP contains {num_files} files")
                        self.log_message.emit(f"📂 Giải nén {num_files} files...")
                        # Emit 92% progress (extraction in progress)
                        self.progress.emit(92, 100)
                        zip_ref.extractall(extract_dir)
                    print(f"[DEBUG] Extraction completed successfully")
                    self.log_message.emit("✅ Giải nén hoàn tất!")
                    # Emit 96% progress (extraction done)
                    self.progress.emit(96, 100)
                except Exception as e:
                    import traceback
                    print(f"[DEBUG] ZIP extraction failed:")
                    print(traceback.format_exc())
                    self.error.emit(f"Lỗi giải nén file ZIP: {str(e)}")
                    return

                # Delete zip file
                print(f"[DEBUG] Deleting ZIP file...")
                self.log_message.emit("🗑️ Xóa file ZIP...")
                os.remove(file_path)

                # Find the extracted app folder (should contain .exe)
                # Assuming structure: AnhMinAudio_Update/AnhMinAudio/AnhMinAudio.exe
                print(f"[DEBUG] Searching for .exe file in extracted folder...")
                self.log_message.emit("🔍 Tìm file thực thi...")
                app_folder = None
                for root, dirs, files in os.walk(extract_dir):
                    exe_files = [f for f in files if f.endswith('.exe')]
                    if exe_files:
                        app_folder = root
                        print(f"[DEBUG] Found .exe in: {root}")
                        print(f"[DEBUG] EXE files: {exe_files}")
                        break

                if not app_folder:
                    print(f"[DEBUG] No .exe found in extracted folder")
                    self.error.emit("Không tìm thấy file .exe trong file .zip")
                    return

                self.log_message.emit("✨ Chuẩn bị cài đặt...")
                # Emit 100% progress (all done)
                self.progress.emit(100, 100)
                print(f"[DEBUG] Emitting finished signal with folder: {app_folder}")
                self.finished.emit(app_folder, True)  # is_folder = True
            else:
                # Single .exe file
                self.log_message.emit("✨ Chuẩn bị cài đặt...")
                # Emit 100% progress (all done)
                self.progress.emit(100, 100)
                print(f"[DEBUG] Emitting finished signal with file: {file_path}")
                self.finished.emit(file_path, False)  # is_folder = False

        except Exception as e:
            import traceback
            print(f"[DEBUG] OUTER EXCEPTION CAUGHT:")
            print(traceback.format_exc())
            sys.stdout.flush()
            self.error.emit(str(e))


class Updater:
    """Handle update installation with admin privileges."""

    @staticmethod
    def is_admin() -> bool:
        """Check if running with admin privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    @staticmethod
    def request_admin_and_install(update_path: str, is_folder: bool = False):
        """
        Request admin privileges and install update.

        Args:
            update_path: Path to downloaded .exe file or extracted folder
            is_folder: True if update_path is a folder, False if single .exe
        """
        print(f"[DEBUG Updater] request_admin_and_install() called")
        print(f"  update_path: {update_path}")
        print(f"  is_folder: {is_folder}")
        print(f"  Path exists: {os.path.exists(update_path)}")

        if not os.path.exists(update_path):
            print(f"[ERROR Updater] Update path not found!")
            raise FileNotFoundError(f"Update path not found: {update_path}")

        # Get current app directory
        is_frozen = getattr(sys, 'frozen', False)
        print(f"[DEBUG Updater] sys.frozen = {is_frozen}")

        if is_frozen:
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            print(f"[DEBUG Updater] Running from frozen exe")
        else:
            # Running from source - for testing
            current_exe = os.path.join(os.getcwd(), 'AnhMinAudio.exe')
            current_dir = os.getcwd()
            print(f"[DEBUG Updater] Running from source (testing mode)")

        print(f"[DEBUG Updater] current_exe: {current_exe}")
        print(f"[DEBUG Updater] current_dir: {current_dir}")

        # Create batch script to replace exe/folder after app closes
        batch_script = os.path.join(tempfile.gettempdir(), 'update_anhmin.bat')
        print(f"[DEBUG Updater] Creating batch script: {batch_script}")

        with open(batch_script, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('chcp 65001 >nul\n')  # UTF-8 encoding
            f.write('timeout /t 2 /nobreak >nul\n')  # Wait for app to close

            if is_folder:
                print(f"[DEBUG Updater] Creating folder replacement script")
                # Replace entire folder
                # Delete old files (except database in %APPDATA%)
                f.write(f'echo Removing old files...\n')
                f.write(f'del /q "{current_dir}\\*.exe"\n')
                f.write(f'del /q "{current_dir}\\*.dll"\n')
                f.write(f'if exist "{current_dir}\\_internal" rmdir /s /q "{current_dir}\\_internal"\n')

                # Copy new files
                f.write(f'echo Copying new files...\n')
                f.write(f'xcopy /E /I /Y "{update_path}\\*" "{current_dir}\\"\n')

                # Clean up temp folder
                f.write(f'rmdir /s /q "{os.path.dirname(update_path)}"\n')
            else:
                print(f"[DEBUG Updater] Creating single file replacement script")
                # Replace single .exe file
                f.write(f'copy /y "{update_path}" "{current_exe}"\n')
                f.write(f'del "{update_path}"\n')

            # Restart app
            f.write(f'start "" "{current_exe}"\n')
            # Delete batch file itself
            f.write(f'del "%~f0"\n')

        print(f"[DEBUG Updater] Batch script created successfully")
        print(f"[DEBUG Updater] Requesting UAC elevation...")

        try:
            # Run batch script with admin privileges
            import ctypes

            print(f"[DEBUG Updater] Calling ShellExecuteW...")
            print(f"  Command: cmd.exe /c \"{batch_script}\"")

            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Request admin
                "cmd.exe",
                f'/c "{batch_script}"',
                None,
                0  # Hidden window
            )

            print(f"[DEBUG Updater] ShellExecuteW returned: {result}")
            print(f"[DEBUG Updater] UAC request completed, returning True")
            return True

        except Exception as e:
            import traceback
            print(f"[ERROR Updater] Exception in ShellExecuteW:")
            print(traceback.format_exc())
            print(f"[ERROR Updater] Error running update script: {e}")
            return False
