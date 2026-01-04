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


class ConfirmDialog(QDialog):
    """Dialog for confirmation with clear, readable UI."""

    def __init__(self, title: str, message: str, ok_text: str = "OK", cancel_text: str = "Hủy", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(450, 200)
        self.user_confirmed = False
        self.setup_ui(message, ok_text, cancel_text)

    def setup_ui(self, message: str, ok_text: str, cancel_text: str):
        """Setup UI."""
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Icon and message
        msg_layout = QHBoxLayout()

        # Question icon
        icon_label = QLabel("❓")
        icon_label.setStyleSheet("font-size: 48px;")
        msg_layout.addWidget(icon_label)

        # Message text
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 500;
            padding-left: 12px;
            line-height: 1.5;
        """)
        msg_layout.addWidget(msg_label, 1)

        layout.addLayout(msg_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        # OK button
        ok_btn = QPushButton(ok_text)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        ok_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_btn.clicked.connect(self.on_confirm)
        ok_btn.setDefault(True)  # Enter key triggers this
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def on_confirm(self):
        """User confirmed."""
        self.user_confirmed = True
        self.accept()


class ErrorDialog(QDialog):
    """Dialog for showing error messages in a readable format."""

    def __init__(self, title: str, message: str, details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.setup_ui(message, details)

    def setup_ui(self, message: str, details: str):
        """Setup UI."""
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Icon and message
        msg_layout = QHBoxLayout()

        # Error icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        msg_layout.addWidget(icon_label)

        # Message text
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 14px;
            padding-left: 8px;
        """)
        msg_layout.addWidget(msg_label, 1)

        layout.addLayout(msg_layout)

        # Details (if provided)
        if details:
            details_label = QLabel("Chi tiết lỗi:")
            details_label.setStyleSheet(f"""
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 13px;
                margin-top: 8px;
            """)
            layout.addWidget(details_label)

            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setPlainText(details)
            details_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLORS['bg_light']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 12px;
                    color: {COLORS['text_primary']};
                    font-size: 12px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
            """)
            layout.addWidget(details_text, 1)

        # OK button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        ok_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)


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

        # Log window (hidden initially, shown during download)
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
        """)
        self.log_window.setVisible(False)
        layout.addWidget(self.log_window, 1)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)  # Show percentage text
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

            # Hide changelog, show log window
            self.changelog.setVisible(False)
            self.log_window.setVisible(True)
            self.log_window.clear()

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
            self.download_worker.log_message.connect(self.on_log_message)

            print("[DEBUG UpdateDialog] Starting worker thread...")
            self.download_worker.start()
            print("[DEBUG UpdateDialog] Worker thread started successfully")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR UpdateDialog] Exception in start_download():")
            print(error_details)

            # Show error with custom dialog
            error_dialog = ErrorDialog(
                title="Lỗi nghiêm trọng",
                message="Không thể bắt đầu tải xuống. Vui lòng thử lại.",
                details=error_details,
                parent=self
            )
            error_dialog.exec()

            # Re-enable button
            self.download_btn.setEnabled(True)
            self.cancel_btn.setText("Hủy")
            self.progress_bar.setVisible(False)
            self.status_label.setVisible(False)

    def on_download_progress(self, downloaded: int, total: int):
        """Update progress bar."""
        print(f"[DEBUG] on_download_progress called: {downloaded}/{total}")
        if total > 0:
            percentage = int((downloaded / total) * 100)
            print(f"[DEBUG] Setting progress bar to {percentage}%")
            self.progress_bar.setValue(percentage)

            # Update status label based on progress stage
            if percentage < 87:
                status_text = "Đang tải xuống từ Google Drive..."
            elif percentage < 88:
                status_text = "Hoàn tất tải xuống..."
            elif percentage < 96:
                status_text = "Đang giải nén file..."
            elif percentage < 100:
                status_text = "Hoàn tất giải nén..."
            else:
                status_text = "Chuẩn bị cài đặt..."

            self.status_label.setText(status_text)
            print(f"[DEBUG] Status label: {status_text}")

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

            self.append_log("🎉 Hoàn tất! Sẵn sàng cài đặt.")

            # Show confirmation with custom dialog
            confirm_dialog = ConfirmDialog(
                title="Cài đặt cập nhật",
                message="Đã tải xong! Nhấn OK để cài đặt và khởi động lại ứng dụng.\n\n"
                        "Lưu ý: Ứng dụng sẽ yêu cầu quyền Administrator để thay thế file.",
                ok_text="Cài đặt",
                cancel_text="Hủy",
                parent=self
            )
            confirm_dialog.exec()

            if confirm_dialog.user_confirmed:
                print("[DEBUG UpdateDialog] User clicked OK, installing update...")
                self.append_log("🔧 Bắt đầu cài đặt...")
                self.install_update()
            else:
                print("[DEBUG UpdateDialog] User cancelled installation")
                self.append_log("⏸️ Người dùng hủy cài đặt.")

        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in on_download_finished:")
            print(traceback.format_exc())

    def on_download_error(self, error_msg: str):
        """Handle download error."""
        print(f"[DEBUG UpdateDialog] on_download_error called: {error_msg}")

        try:
            self.status_label.setText("Lỗi tải xuống")
            self.download_btn.setEnabled(True)
            self.download_btn.setText("Thử lại")

            # Add error to log window
            self.append_log(f"❌ Lỗi: {error_msg[:100]}...")

            # Show error in a readable dialog
            error_dialog = ErrorDialog(
                title="Lỗi tải xuống",
                message="Không thể tải xuống cập nhật. Vui lòng kiểm tra kết nối internet và thử lại.",
                details=error_msg,
                parent=self
            )
            error_dialog.exec()
        except Exception as e:
            import traceback
            print(f"[ERROR UpdateDialog] Exception in on_download_error:")
            print(traceback.format_exc())

    def on_log_message(self, message: str):
        """Handle log message from download worker."""
        self.append_log(message)

    def append_log(self, message: str):
        """Append message to log window with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_window.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_window.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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
                # Show error with custom dialog
                error_dialog = ErrorDialog(
                    title="Lỗi cài đặt",
                    message="Không thể cài đặt cập nhật. Vui lòng cài đặt thủ công.",
                    details="Updater.request_admin_and_install() returned False.\n"
                            "Có thể do:\n"
                            "- Không có quyền Administrator\n"
                            "- File đang được sử dụng\n"
                            "- Đường dẫn không hợp lệ",
                    parent=self
                )
                error_dialog.exec()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR UpdateDialog] Exception in install_update():")
            print(error_details)

            # Show error with custom dialog
            error_dialog = ErrorDialog(
                title="Lỗi cài đặt",
                message="Lỗi khi cài đặt cập nhật. Vui lòng thử lại.",
                details=error_details,
                parent=self
            )
            error_dialog.exec()

    def on_cancel(self):
        """Handle cancel button."""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait()

        self.reject()
