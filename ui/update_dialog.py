"""
AnhMin Audio - Update Dialog
Dialog for showing update information and download progress
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from ui.styles import COLORS
from updater import Updater, DownloadWorker


class UpdateDialog(QDialog):
    """Dialog showing update information."""

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_worker = None
        self.downloaded_path = None
        self.is_folder = False
        self.setWindowTitle("Cập nhật mới")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        """Setup UI."""
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel(f"Phiên bản mới: v{self.update_info['version']}")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(header)

        # File size info
        size_mb = self.update_info['size'] / (1024 * 1024)
        size_label = QLabel(f"Kích thước: {size_mb:.1f} MB")
        size_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(size_label)

        # Changelog
        changelog_label = QLabel("Thay đổi:")
        changelog_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(changelog_label)

        self.changelog = QTextEdit()
        self.changelog.setReadOnly(True)
        self.changelog.setPlainText(self.update_info['changelog'])
        self.changelog.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.changelog, 1)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {COLORS['bg_lighter']};
                text-align: center;
                color: {COLORS['text_primary']};
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label (hidden initially)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.on_cancel)
        btn_layout.addWidget(self.cancel_btn)

        self.download_btn = QPushButton("Tải về")
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.download_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.download_btn)

        layout.addLayout(btn_layout)

    def start_download(self):
        """Start downloading update."""
        try:
            print("[DEBUG UpdateDialog] start_download() called")
            self.download_btn.setEnabled(False)
            self.cancel_btn.setText("Đóng")
            self.progress_bar.setVisible(True)
            self.status_label.setVisible(True)
            self.status_label.setText("Đang tải xuống...")

            print(f"[DEBUG UpdateDialog] Creating DownloadWorker with:")
            print(f"  URL: {self.update_info['download_url']}")
            print(f"  File: {self.update_info['file_name']}")

            # Start download worker
            self.download_worker = DownloadWorker(
                self.update_info['download_url'],
                self.update_info['file_name']
            )

            print("[DEBUG UpdateDialog] Connecting signals...")
            self.download_worker.progress.connect(self.on_download_progress)
            self.download_worker.finished.connect(self.on_download_finished)
            self.download_worker.error.connect(self.on_download_error)

            print("[DEBUG UpdateDialog] Starting worker thread...")
            self.download_worker.start()
            print("[DEBUG UpdateDialog] Worker thread started successfully")

        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in start_download():")
            print(traceback.format_exc())

            QMessageBox.critical(
                self,
                "Lỗi nghiêm trọng",
                f"Không thể bắt đầu tải xuống:\n{str(e)}\n\nVui lòng kiểm tra console để xem chi tiết."
            )

            # Re-enable button
            self.download_btn.setEnabled(True)
            self.cancel_btn.setText("Hủy")
            self.progress_bar.setVisible(False)
            self.status_label.setVisible(False)

    def on_download_progress(self, downloaded: int, total: int):
        """Update progress bar."""
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)

            # Update status
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(f"Đang tải: {downloaded_mb:.1f} / {total_mb:.1f} MB")

    def on_download_finished(self, path: str, is_folder: bool):
        """Handle download completion."""
        print(f"[DEBUG UpdateDialog] on_download_finished called")
        print(f"  Path: {path}")
        print(f"  Is folder: {is_folder}")

        try:
            self.downloaded_path = path
            self.is_folder = is_folder
            self.status_label.setText("Tải xuống hoàn tất!")
            self.progress_bar.setValue(100)

            # Show confirmation
            reply = QMessageBox.question(
                self,
                "Cài đặt cập nhật",
                "Đã tải xong! Nhấn OK để cài đặt và khởi động lại ứng dụng.\n\n"
                "Lưu ý: Ứng dụng sẽ yêu cầu quyền Administrator để thay thế file.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Ok:
                print("[DEBUG UpdateDialog] User clicked OK, installing update...")
                self.install_update()
            else:
                print("[DEBUG UpdateDialog] User cancelled installation")

        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in on_download_finished:")
            print(traceback.format_exc())

    def on_download_error(self, error_msg: str):
        """Handle download error."""
        print(f"[DEBUG UpdateDialog] on_download_error called: {error_msg}")

        try:
            self.status_label.setText(f"Lỗi: {error_msg}")
            self.download_btn.setEnabled(True)
            self.download_btn.setText("Thử lại")

            QMessageBox.warning(
                self,
                "Lỗi tải xuống",
                f"Không thể tải xuống cập nhật:\n{error_msg}\n\n"
                "Vui lòng kiểm tra kết nối internet và thử lại."
            )
        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in on_download_error:")
            print(traceback.format_exc())

    def install_update(self):
        """Install the downloaded update."""
        print("[DEBUG UpdateDialog] install_update() called")

        if not self.downloaded_path:
            print("[DEBUG UpdateDialog] No downloaded_path, returning")
            return

        try:
            print(f"[DEBUG UpdateDialog] Calling Updater.request_admin_and_install()")
            print(f"  Path: {self.downloaded_path}")
            print(f"  Is folder: {self.is_folder}")

            # Request admin and install
            success = Updater.request_admin_and_install(self.downloaded_path, self.is_folder)

            print(f"[DEBUG UpdateDialog] Updater returned: {success}")

            if success:
                print("[DEBUG UpdateDialog] Installation successful, quitting app...")
                # Close all dialogs and quit app
                self.accept()
                from PyQt6.QtWidgets import QApplication
                QApplication.instance().quit()
            else:
                print("[DEBUG UpdateDialog] Installation failed (success=False)")
                QMessageBox.warning(
                    self,
                    "Lỗi cài đặt",
                    "Không thể cài đặt cập nhật. Vui lòng cài đặt thủ công."
                )

        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in install_update():")
            print(traceback.format_exc())

            QMessageBox.critical(
                self,
                "Lỗi",
                f"Lỗi khi cài đặt: {str(e)}"
            )

    def on_cancel(self):
        """Handle cancel button."""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait()

        self.reject()
