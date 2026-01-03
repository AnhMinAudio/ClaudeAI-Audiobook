"""
AnhMin Audio - Memory Widget
Project memory management
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QMessageBox, QComboBox, QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from ui.styles import COLORS


class MemoryItemWidget(QFrame):
    """Widget for a single memory item (read-only)."""

    def __init__(self, memory_id: int, key: str, value: str, category: str = "general"):
        super().__init__()
        self.memory_id = memory_id
        self.key = key
        self.value = value
        self.category = category
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_lighter']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with key and delete button
        header = QHBoxLayout()
        
        key_label = QLabel(self.key)
        key_label.setStyleSheet(f"""
            background-color: {COLORS['accent_light']};
            color: {COLORS['accent']};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        """)
        header.addWidget(key_label)
        
        if self.category != "general":
            cat_label = QLabel(self.category)
            cat_label.setStyleSheet(f"""
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
            """)
            header.addWidget(cat_label)
        
        header.addStretch()

        layout.addLayout(header)

        # Value
        value_label = QLabel(self.value)
        value_label.setWordWrap(True)
        value_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
        """)
        layout.addWidget(value_label)


class MemoryWidget(QWidget):
    """Memory management widget with auto-update."""

    def __init__(self):
        super().__init__()
        self.project_id = None
        self.memory_widgets = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        header_text = QVBoxLayout()
        header_text.setSpacing(4)
        
        title = QLabel("Project Memory")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header_text.addWidget(title)

        subtitle = QLabel("Memory tự động cập nhật từ các chương được xử lý.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header_text.addWidget(subtitle)

        header.addLayout(header_text)
        header.addStretch()

        # Clear all button
        clear_btn = QPushButton("🗑️ Xóa tất cả Memory")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_secondary']};
                font-size: 12px;
                padding: 6px 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: white;
            }}
        """)
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.clicked.connect(self.clear_all_memory)
        header.addWidget(clear_btn)

        layout.addLayout(header)
        
        # Memory list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.memory_list = QWidget()
        self.memory_list.setStyleSheet("background: transparent;")
        self.memory_layout = QVBoxLayout(self.memory_list)
        self.memory_layout.setContentsMargins(0, 0, 0, 0)
        self.memory_layout.setSpacing(12)
        self.memory_layout.addStretch()
        
        scroll.setWidget(self.memory_list)
        layout.addWidget(scroll, 1)

        # Stats
        self.stats = QFrame()
        self.stats.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(31, 41, 55, 0.3);
                border-radius: 10px;
            }}
        """)
        stats_layout = QHBoxLayout(self.stats)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        
        self.count_label = QLabel("Tổng số memory: 0 items")
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        stats_layout.addWidget(self.count_label)
        
        stats_layout.addStretch()
        
        layout.addWidget(self.stats)
    
    def set_project(self, project_id: int):
        """Load project memory."""
        self.project_id = project_id
        self.clear_widgets()
        self.load_memory()
    
    def clear_widgets(self):
        """Clear all memory widgets."""
        for widget in self.memory_widgets.values():
            widget.deleteLater()
        self.memory_widgets.clear()
        
        while self.memory_layout.count() > 1:
            item = self.memory_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def load_memory(self):
        """Load memory from database."""
        if not self.project_id:
            return
        
        memories = db.get_memory(self.project_id)
        for mem in memories:
            self.add_memory_widget(mem)
        
        self.update_stats()
    
    def add_memory_widget(self, memory_data: dict):
        """Add a memory widget to the list."""
        widget = MemoryItemWidget(
            memory_data['id'],
            memory_data['key'],
            memory_data['value'],
            memory_data.get('category', 'general')
        )

        # Insert before stretch
        count = self.memory_layout.count()
        self.memory_layout.insertWidget(count - 1, widget)
        self.memory_widgets[memory_data['id']] = widget
    
    def clear_all_memory(self):
        """Clear all memory for the project."""
        if not self.project_id:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa Memory",
            "Bạn có chắc muốn xóa tất cả memory?\n\n"
            "Memory sẽ được tự động tạo lại từ các chương tiếp theo sau khi xóa.\n\n"
            "Hành động này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            db.clear_memory(self.project_id)
            self.clear_widgets()
            self.memory_layout.addStretch()
            self.update_stats()

    def update_stats(self):
        """Update memory statistics."""
        count = len(self.memory_widgets)
        self.count_label.setText(f"Tổng số memory: {count} items")
