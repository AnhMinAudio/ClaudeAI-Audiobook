"""
AnhMin Audio - Files Widget
Project files management
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QDragEnterEvent, QDropEvent

from database import db
from api import file_handler
from ui.styles import COLORS


class FileItemWidget(QFrame):
    """Widget for a single file item."""
    
    delete_requested = pyqtSignal(int, str)
    
    def __init__(self, file_id: int, filename: str, file_size: int, filepath: str):
        super().__init__()
        self.file_id = file_id
        self.filepath = filepath
        self.setup_ui(filename, file_size)
    
    def setup_ui(self, filename: str, file_size: int):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_lighter']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Icon
        icon_frame = QFrame()
        icon_frame.setFixedSize(40, 40)
        icon_frame.setStyleSheet(f"""
            background-color: {COLORS['accent_light']};
            border-radius: 8px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel("📄")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 18px;")
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_frame)
        
        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(filename)
        name_label.setStyleSheet(f"""
            font-weight: 500;
            color: {COLORS['text_primary']};
            font-size: 13px;
        """)
        info_layout.addWidget(name_label)
        
        size_label = QLabel(file_handler.format_file_size(file_size))
        size_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info_layout.addWidget(size_label)
        
        layout.addLayout(info_layout, 1)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Xóa")
        delete_btn.setStyleSheet(f"""
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
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.file_id, self.filepath))
        layout.addWidget(delete_btn)


class UploadArea(QFrame):
    """Drag and drop upload area."""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(31, 41, 55, 0.5);
                border: 2px dashed {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {COLORS['accent']};
            }}
        """)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        # Icon
        icon = QLabel("☁️")
        icon.setStyleSheet("font-size: 36px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # Text
        text = QLabel("Kéo thả file vào đây")
        text.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {COLORS['text_primary']};
        """)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text)
        
        hint = QLabel("hoặc click để chọn file • Hỗ trợ TXT, DOCX")
        hint.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']};")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['accent_light']};
                    border: 2px dashed {COLORS['accent']};
                    border-radius: 12px;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(31, 41, 55, 0.5);
                border: 2px dashed {COLORS['border']};
                border-radius: 12px;
            }}
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(31, 41, 55, 0.5);
                border: 2px dashed {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        
        files = []
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                files.append(filepath)
        
        if files:
            self.files_dropped.emit(files)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Chọn file",
                "",
                "Text Files (*.txt);;Word Documents (*.docx);;All Files (*.*)"
            )
            if files:
                self.files_dropped.emit(files)
        super().mousePressEvent(event)


class FilesWidget(QWidget):
    """Files management widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.file_widgets = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(20)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("Project Files")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        subtitle = QLabel("Các file này sẽ được Claude tham khảo trong mọi cuộc trò chuyện.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header.addWidget(subtitle)
        
        layout.addLayout(header)
        
        # Upload area
        self.upload_area = UploadArea()
        self.upload_area.files_dropped.connect(self.add_files)
        layout.addWidget(self.upload_area)
        
        # Files list header
        files_header = QHBoxLayout()
        
        self.files_count = QLabel("Files đã upload (0)")
        self.files_count.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {COLORS['text_secondary']};
        """)
        files_header.addWidget(self.files_count)
        
        files_header.addStretch()
        
        layout.addLayout(files_header)
        
        # Files list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.files_list = QWidget()
        self.files_list.setStyleSheet("background: transparent;")
        self.files_layout = QVBoxLayout(self.files_list)
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        self.files_layout.setSpacing(8)
        self.files_layout.addStretch()
        
        scroll.setWidget(self.files_list)
        layout.addWidget(scroll, 1)
    
    def set_project(self, project_id: int):
        """Load project files."""
        self.project_id = project_id
        self.clear_files()
        self.load_files()
    
    def clear_files(self):
        """Clear all file widgets."""
        for widget in self.file_widgets.values():
            widget.deleteLater()
        self.file_widgets.clear()
        
        while self.files_layout.count() > 1:
            item = self.files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def load_files(self):
        """Load files from database."""
        if not self.project_id:
            return
        
        files = db.get_project_files(self.project_id)
        for f in files:
            self.add_file_widget(f)
        
        self.update_count()
    
    def add_file_widget(self, file_data: dict):
        """Add a file widget to the list."""
        widget = FileItemWidget(
            file_data['id'],
            file_data['filename'],
            file_data['file_size'],
            file_data['filepath']
        )
        widget.delete_requested.connect(self.delete_file)
        
        # Insert before stretch
        count = self.files_layout.count()
        self.files_layout.insertWidget(count - 1, widget)
        self.file_widgets[file_data['id']] = widget
    
    def add_files(self, filepaths: list):
        """Add files to the project."""
        if not self.project_id:
            return
        
        for filepath in filepaths:
            # Copy to project directory
            new_path, error = file_handler.copy_to_project(filepath, self.project_id)
            if error:
                QMessageBox.warning(self, "Lỗi", f"Không thể thêm file: {error}")
                continue
            
            from pathlib import Path
            path = Path(filepath)
            file_size = file_handler.get_file_size(filepath)
            file_type = file_handler.get_file_type(filepath)
            
            # Add to database
            file_id = db.add_project_file(
                self.project_id,
                path.name,
                new_path,
                file_size,
                file_type
            )
            
            # Add widget
            self.add_file_widget({
                'id': file_id,
                'filename': path.name,
                'file_size': file_size,
                'filepath': new_path
            })
        
        self.update_count()
    
    def delete_file(self, file_id: int, filepath: str):
        """Delete a file."""
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa file này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete from filesystem
            file_handler.delete_file(filepath)
            
            # Delete from database
            db.delete_project_file(file_id)
            
            # Remove widget
            if file_id in self.file_widgets:
                self.file_widgets[file_id].deleteLater()
                del self.file_widgets[file_id]
            
            self.update_count()
    
    def update_count(self):
        """Update files count label."""
        count = len(self.file_widgets)
        self.files_count.setText(f"Files đã upload ({count})")
