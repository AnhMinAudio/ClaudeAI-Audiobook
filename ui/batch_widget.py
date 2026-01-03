"""
AnhMin Audio - Batch Widget
Batch processing with Anthropic Batch API
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QCursor, QColor

from database import db
from api import claude_client, file_handler
from ui.styles import COLORS


class BatchWorker(QThread):
    """Worker thread for batch operations."""
    
    batch_created = pyqtSignal(dict)
    status_updated = pyqtSignal(dict)
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == 'create':
                result = claude_client.create_batch(self.kwargs['requests'])
                self.batch_created.emit(result)
            
            elif self.operation == 'status':
                result = claude_client.get_batch_status(self.kwargs['batch_id'])
                self.status_updated.emit(result)
            
            elif self.operation == 'results':
                results = claude_client.get_batch_results(self.kwargs['batch_id'])
                self.results_ready.emit(results)
                
        except Exception as e:
            self.error_occurred.emit(str(e))


class FileListItem(QFrame):
    """Widget for a single file in batch list."""
    
    remove_requested = pyqtSignal(str)
    
    def __init__(self, filepath: str, filename: str, file_size: int):
        super().__init__()
        self.filepath = filepath
        self.setup_ui(filename, file_size)
    
    def setup_ui(self, filename: str, file_size: int):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel("📄")
        icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon)
        
        # File info
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name_label = QLabel(filename)
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        info.addWidget(name_label)
        
        size_label = QLabel(file_handler.format_file_size(file_size))
        size_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info.addWidget(size_label)
        
        layout.addLayout(info, 1)
        
        # Remove button
        remove_btn = QPushButton("🗑️ Xóa")
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(239, 68, 68, 0.1);
                color: {COLORS['error']};
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: rgba(239, 68, 68, 0.2);
            }}
        """)
        remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.filepath))
        layout.addWidget(remove_btn)


class BatchWidget(QWidget):
    """Batch processing widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.files: Dict[str, dict] = {}  # filepath -> {name, size, content}
        self.output_dir: Optional[Path] = None
        self.current_batch_id: Optional[str] = None
        self.status_timer: Optional[QTimer] = None
        self.file_widgets: Dict[str, FileListItem] = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("📦 Batch Processing")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        subtitle = QLabel("Xử lý nhiều file cùng lúc với Batch API - Tiết kiệm 50% chi phí")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header.addWidget(subtitle)
        
        layout.addLayout(header)
        
        # Info box
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(249, 115, 22, 0.1);
                border: 1px solid rgba(249, 115, 22, 0.3);
                border-radius: 8px;
            }}
        """)
        info_layout = QHBoxLayout(info_box)
        info_layout.setContentsMargins(12, 10, 12, 10)
        
        info_icon = QLabel("💡")
        info_layout.addWidget(info_icon)
        
        info_text = QLabel(
            "Batch API xử lý không đồng bộ, thời gian hoàn thành 1-24 giờ. "
            "Sử dụng Hướng dẫn, Files và Memory của project hiện tại."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
        info_layout.addWidget(info_text, 1)
        
        layout.addWidget(info_box)
        
        # Main content - split into left (file list) and right (status)
        content = QHBoxLayout()
        content.setSpacing(16)
        
        # Left panel - File selection
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        
        # Add files button
        btn_row = QHBoxLayout()
        
        add_files_btn = QPushButton("📁 Chọn files")
        add_files_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        add_files_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_files_btn.clicked.connect(self.add_files)
        btn_row.addWidget(add_files_btn)
        
        clear_btn = QPushButton("🗑️ Xóa tất cả")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {COLORS['error']};
            }}
        """)
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(clear_btn)
        
        btn_row.addStretch()
        
        self.file_count_label = QLabel("0 files đã chọn")
        self.file_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        btn_row.addWidget(self.file_count_label)
        
        left_panel.addLayout(btn_row)
        
        # File list
        file_scroll = QScrollArea()
        file_scroll.setWidgetResizable(True)
        file_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        file_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_dark']};
            }}
        """)
        file_scroll.setMinimumHeight(200)
        
        self.file_list = QWidget()
        self.file_list.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self.file_list_layout = QVBoxLayout(self.file_list)
        self.file_list_layout.setContentsMargins(8, 8, 8, 8)
        self.file_list_layout.setSpacing(6)
        self.file_list_layout.addStretch()
        
        file_scroll.setWidget(self.file_list)
        left_panel.addWidget(file_scroll, 1)
        
        # Output directory selection
        output_row = QHBoxLayout()
        
        output_label = QLabel("📂 Thư mục lưu:")
        output_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        output_row.addWidget(output_label)
        
        self.output_path_label = QLabel("Chưa chọn")
        self.output_path_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        output_row.addWidget(self.output_path_label, 1)
        
        choose_dir_btn = QPushButton("Chọn...")
        choose_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        choose_dir_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        choose_dir_btn.clicked.connect(self.choose_output_dir)
        output_row.addWidget(choose_dir_btn)
        
        left_panel.addLayout(output_row)
        
        # Start batch button
        self.start_btn = QPushButton("🚀 Bắt đầu xử lý Batch")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.clicked.connect(self.start_batch)
        self.start_btn.setEnabled(False)
        left_panel.addWidget(self.start_btn)
        
        content.addLayout(left_panel, 1)
        
        # Right panel - Batch status
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        status_title = QLabel("📊 Trạng thái Batch")
        status_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
        """)
        right_panel.addWidget(status_title)
        
        # Status card
        self.status_card = QFrame()
        self.status_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        status_card_layout = QVBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(16, 16, 16, 16)
        status_card_layout.setSpacing(12)
        
        # Batch ID
        self.batch_id_label = QLabel("Batch ID: --")
        self.batch_id_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        status_card_layout.addWidget(self.batch_id_label)
        
        # Status
        self.status_label = QLabel("Chưa có batch nào")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: 600;
        """)
        status_card_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_dark']};
                border: none;
                border-radius: 6px;
                height: 12px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 6px;
            }}
        """)
        self.progress_bar.setValue(0)
        status_card_layout.addWidget(self.progress_bar)
        
        # Stats
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(16)
        
        self.stat_processing = self.create_stat_widget("Đang xử lý", "0")
        stats_grid.addWidget(self.stat_processing)
        
        self.stat_succeeded = self.create_stat_widget("Thành công", "0", COLORS['success'])
        stats_grid.addWidget(self.stat_succeeded)
        
        self.stat_errored = self.create_stat_widget("Lỗi", "0", COLORS['error'])
        stats_grid.addWidget(self.stat_errored)
        
        status_card_layout.addLayout(stats_grid)
        
        # Action buttons
        action_row = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Làm mới")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        self.refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.refresh_btn.clicked.connect(self.refresh_status)
        self.refresh_btn.setEnabled(False)
        action_row.addWidget(self.refresh_btn)
        
        self.download_btn = QPushButton("📥 Tải kết quả")
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.download_btn.clicked.connect(self.download_results)
        self.download_btn.setEnabled(False)
        action_row.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("❌ Hủy")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['error']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                color: {COLORS['error']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
            }}
            QPushButton:disabled {{
                border-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.cancel_batch)
        self.cancel_btn.setEnabled(False)
        action_row.addWidget(self.cancel_btn)
        
        status_card_layout.addLayout(action_row)
        
        right_panel.addWidget(self.status_card)
        
        # Batch history
        history_label = QLabel("📜 Lịch sử Batch")
        history_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            margin-top: 8px;
        """)
        right_panel.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Batch ID", "Trạng thái", "Files", "Thời gian"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_light']};
                border: none;
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent_light']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border: none;
                font-weight: 500;
            }}
        """)
        self.history_table.itemDoubleClicked.connect(self.on_history_item_clicked)
        right_panel.addWidget(self.history_table, 1)
        
        content.addLayout(right_panel, 1)
        
        layout.addLayout(content, 1)
        
        # Load batch history
        self.load_batch_history()
    
    def create_stat_widget(self, label: str, value: str, color: str = None) -> QFrame:
        """Create a stat display widget."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {color or COLORS['text_primary']};
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        return frame
    
    def set_project(self, project_id: int):
        """Set current project."""
        self.project_id = project_id
        self.load_batch_history()
    
    def add_files(self):
        """Add files to batch list."""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn files để xử lý",
            "",
            "Text Files (*.txt);;Word Documents (*.docx);;All Files (*.*)"
        )
        
        for filepath in filepaths:
            if filepath in self.files:
                continue
            
            content, error = file_handler.read_file(filepath)
            if error:
                QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {filepath}\n{error}")
                continue
            
            path = Path(filepath)
            file_size = file_handler.get_file_size(filepath)
            
            self.files[filepath] = {
                'name': path.name,
                'size': file_size,
                'content': content,
                'stem': path.stem
            }
            
            # Add widget
            widget = FileListItem(filepath, path.name, file_size)
            widget.remove_requested.connect(self.remove_file)
            
            count = self.file_list_layout.count()
            self.file_list_layout.insertWidget(count - 1, widget)
            self.file_widgets[filepath] = widget
        
        self.update_file_count()
    
    def remove_file(self, filepath: str):
        """Remove a file from batch list."""
        if filepath in self.files:
            del self.files[filepath]
        
        if filepath in self.file_widgets:
            self.file_widgets[filepath].deleteLater()
            del self.file_widgets[filepath]
        
        self.update_file_count()
    
    def clear_files(self):
        """Clear all files."""
        self.files.clear()
        
        for widget in self.file_widgets.values():
            widget.deleteLater()
        self.file_widgets.clear()
        
        self.update_file_count()
    
    def update_file_count(self):
        """Update file count label and button state."""
        count = len(self.files)
        self.file_count_label.setText(f"{count} files đã chọn")
        self.start_btn.setEnabled(count > 0 and self.output_dir is not None)
    
    def choose_output_dir(self):
        """Choose output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục lưu kết quả",
            str(Path.home() / "Downloads")
        )
        
        if dir_path:
            self.output_dir = Path(dir_path)
            # Truncate display if too long
            display = str(self.output_dir)
            if len(display) > 40:
                display = "..." + display[-37:]
            self.output_path_label.setText(display)
            self.output_path_label.setToolTip(str(self.output_dir))
            self.update_file_count()
    
    def start_batch(self):
        """Start batch processing."""
        if not self.files:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn files để xử lý")
            return
        
        if not self.output_dir:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn thư mục lưu kết quả")
            return
        
        if not self.project_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn project")
            return
        
        # Build system prompt from project
        project = db.get_project(self.project_id)
        memory = db.get_memory(self.project_id)
        system_prompt = claude_client.build_system_prompt(
            project.get('instructions', ''),
            memory
        )
        
        # Build batch requests
        requests = []
        for filepath, file_info in self.files.items():
            request = claude_client.build_batch_request(
                custom_id=file_info['stem'],
                content=file_info['content'],
                system_prompt=system_prompt
            )
            requests.append(request)
        
        # Disable UI
        self.start_btn.setEnabled(False)
        self.start_btn.setText("⏳ Đang gửi...")
        
        # Create batch
        self.worker = BatchWorker('create', requests=requests)
        self.worker.batch_created.connect(self.on_batch_created)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_batch_created(self, batch: dict):
        """Handle batch created."""
        self.current_batch_id = batch['id']
        
        # Save to database
        self.save_batch_to_history(batch)
        
        # Update UI
        self.batch_id_label.setText(f"Batch ID: {batch['id'][:20]}...")
        self.status_label.setText("🔄 Đang xử lý")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 16px; font-weight: 600;")
        
        self.refresh_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.start_btn.setText("🚀 Bắt đầu xử lý Batch")
        
        # Start polling
        self.start_status_polling()
        
        # Reload history
        self.load_batch_history()
        
        QMessageBox.information(
            self, 
            "Batch đã tạo", 
            f"Batch đã được gửi thành công!\n\n"
            f"ID: {batch['id']}\n"
            f"Số files: {len(self.files)}\n\n"
            f"Vui lòng chờ 1-24 giờ để xử lý hoàn tất."
        )
    
    def start_status_polling(self):
        """Start polling for batch status."""
        if self.status_timer:
            self.status_timer.stop()
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(30000)  # Check every 30 seconds
    
    def stop_status_polling(self):
        """Stop polling."""
        if self.status_timer:
            self.status_timer.stop()
            self.status_timer = None
    
    def refresh_status(self):
        """Refresh batch status."""
        if not self.current_batch_id:
            return
        
        self.worker = BatchWorker('status', batch_id=self.current_batch_id)
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_status_updated(self, status: dict):
        """Handle status update."""
        counts = status['request_counts']
        total = counts['processing'] + counts['succeeded'] + counts['errored'] + counts['canceled'] + counts['expired']
        
        # Update progress
        if total > 0:
            progress = int((counts['succeeded'] + counts['errored']) / total * 100)
            self.progress_bar.setValue(progress)
        
        # Update stats
        self.stat_processing.findChild(QLabel, "value").setText(str(counts['processing']))
        self.stat_succeeded.findChild(QLabel, "value").setText(str(counts['succeeded']))
        self.stat_errored.findChild(QLabel, "value").setText(str(counts['errored']))
        
        # Update status label
        if status['status'] == 'in_progress':
            self.status_label.setText("🔄 Đang xử lý")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 16px; font-weight: 600;")
        elif status['status'] == 'ended':
            self.stop_status_polling()
            if counts['succeeded'] > 0:
                self.status_label.setText("✅ Hoàn thành")
                self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px; font-weight: 600;")
                self.download_btn.setEnabled(True)
            else:
                self.status_label.setText("❌ Thất bại")
                self.status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px; font-weight: 600;")
            self.cancel_btn.setEnabled(False)
        
        # Update history
        self.update_batch_in_history(self.current_batch_id, status)
        self.load_batch_history()
    
    def download_results(self):
        """Download batch results."""
        if not self.current_batch_id:
            return
        
        if not self.output_dir:
            self.choose_output_dir()
            if not self.output_dir:
                return
        
        self.download_btn.setEnabled(False)
        self.download_btn.setText("⏳ Đang tải...")
        
        self.worker = BatchWorker('results', batch_id=self.current_batch_id)
        self.worker.results_ready.connect(self.on_results_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_results_ready(self, results: list):
        """Handle results ready."""
        success_count = 0
        error_count = 0
        
        project = db.get_project(self.project_id) if self.project_id else {}
        project_name = project.get('name', '')
        
        for result in results:
            if result['type'] == 'succeeded':
                # Export to DOCX
                output_path = self.output_dir / f"{result['custom_id']}.docx"
                _, error = file_handler.export_to_docx(
                    result['content'],
                    project_name=project_name,
                    output_path=str(output_path)
                )
                
                if error:
                    error_count += 1
                else:
                    success_count += 1
            else:
                error_count += 1
        
        self.download_btn.setText("📥 Tải kết quả")
        self.download_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Hoàn thành",
            f"Đã lưu {success_count} files vào:\n{self.output_dir}\n\n"
            f"Thành công: {success_count}\n"
            f"Lỗi: {error_count}"
        )
    
    def cancel_batch(self):
        """Cancel current batch."""
        if not self.current_batch_id:
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn hủy batch này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                claude_client.cancel_batch(self.current_batch_id)
                self.stop_status_polling()
                self.status_label.setText("❌ Đã hủy")
                self.status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px; font-weight: 600;")
                self.cancel_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
    
    def on_error(self, error: str):
        """Handle error."""
        self.start_btn.setText("🚀 Bắt đầu xử lý Batch")
        self.start_btn.setEnabled(len(self.files) > 0 and self.output_dir is not None)
        self.download_btn.setText("📥 Tải kết quả")
        
        QMessageBox.warning(self, "Lỗi", error)
    
    # ============== Batch History ==============
    
    def save_batch_to_history(self, batch: dict):
        """Save batch to database."""
        if not self.project_id:
            return
        
        history = self.get_batch_history()
        history.append({
            'id': batch['id'],
            'status': batch['status'],
            'file_count': len(self.files),
            'created_at': datetime.now().isoformat(),
            'output_dir': str(self.output_dir)
        })
        
        # Keep only last 20
        history = history[-20:]
        
        db.set_setting(f'batch_history_{self.project_id}', json.dumps(history))
    
    def update_batch_in_history(self, batch_id: str, status: dict):
        """Update batch status in history."""
        if not self.project_id:
            return
        
        history = self.get_batch_history()
        for item in history:
            if item['id'] == batch_id:
                item['status'] = status['status']
                break
        
        db.set_setting(f'batch_history_{self.project_id}', json.dumps(history))
    
    def get_batch_history(self) -> list:
        """Get batch history from database."""
        if not self.project_id:
            return []
        
        history_str = db.get_setting(f'batch_history_{self.project_id}', '[]')
        try:
            return json.loads(history_str)
        except:
            return []
    
    def load_batch_history(self):
        """Load batch history into table."""
        history = self.get_batch_history()
        
        self.history_table.setRowCount(len(history))
        
        for i, item in enumerate(reversed(history)):
            # ID
            id_item = QTableWidgetItem(item['id'][:16] + "...")
            id_item.setData(Qt.ItemDataRole.UserRole, item['id'])
            self.history_table.setItem(i, 0, id_item)
            
            # Status
            status_text = {
                'in_progress': '🔄 Đang xử lý',
                'ended': '✅ Hoàn thành',
                'canceling': '⏳ Đang hủy',
                'canceled': '❌ Đã hủy'
            }.get(item.get('status', ''), item.get('status', ''))
            self.history_table.setItem(i, 1, QTableWidgetItem(status_text))
            
            # File count
            self.history_table.setItem(i, 2, QTableWidgetItem(str(item.get('file_count', 0))))
            
            # Time
            try:
                dt = datetime.fromisoformat(item['created_at'])
                time_str = dt.strftime("%d/%m %H:%M")
            except:
                time_str = "--"
            self.history_table.setItem(i, 3, QTableWidgetItem(time_str))
    
    def on_history_item_clicked(self, item):
        """Handle double click on history item."""
        row = item.row()
        id_item = self.history_table.item(row, 0)
        batch_id = id_item.data(Qt.ItemDataRole.UserRole)
        
        if batch_id:
            self.current_batch_id = batch_id
            self.batch_id_label.setText(f"Batch ID: {batch_id[:20]}...")
            self.refresh_status()
