"""
AnhMin Audio - Sidebar Widget
Project list and navigation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QDialog, QMessageBox,
    QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor

from database import db
from ui.styles import COLORS


class ProjectItemWidget(QFrame):
    """Widget for a single project item in sidebar."""
    
    clicked = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    rename_requested = pyqtSignal(int)
    
    def __init__(self, project_id: int, name: str, is_active: bool = False):
        super().__init__()
        self.project_id = project_id
        self.name = name
        self.is_active = is_active
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        
        # Folder icon
        icon_label = QLabel("📁")
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(icon_label)
        
        # Project name
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet(f"color: {COLORS['accent'] if self.is_active else COLORS['text_primary']};")
        layout.addWidget(self.name_label, 1)
        
        # Style
        self.update_style()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def update_style(self):
        if self.is_active:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['accent_light']};
                    border: 1px solid rgba(249, 115, 22, 0.3);
                    border-radius: 8px;
                }}
            """)
            self.name_label.setStyleSheet(f"color: {COLORS['accent']};")
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    background-color: {COLORS['bg_lighter']};
                }}
            """)
            self.name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
    
    def set_active(self, active: bool):
        self.is_active = active
        self.update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project_id)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
            }}
        """)
        
        rename_action = menu.addAction("✏️ Đổi tên")
        delete_action = menu.addAction("🗑️ Xóa")
        
        action = menu.exec(event.globalPos())
        if action == rename_action:
            self.rename_requested.emit(self.project_id)
        elif action == delete_action:
            self.delete_requested.emit(self.project_id)


class NewProjectDialog(QDialog):
    """Dialog for creating a new project."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tạo dự án mới")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Tên dự án")
        title.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ví dụ: Đấu Phá Thương Khung")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Tạo dự án")
        create_btn.setObjectName("primaryButton")
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
        
        # Enter to submit
        self.name_input.returnPressed.connect(self.accept)
    
    def get_name(self) -> str:
        return self.name_input.text().strip()


class SidebarWidget(QWidget):
    """Sidebar widget with project list."""

    project_selected = pyqtSignal(int)
    settings_clicked = pyqtSignal()
    update_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.project_widgets = {}
        self.current_project_id = None
        self.setup_ui()
        self.load_projects()
    
    def setup_ui(self):
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {COLORS['bg_darkest']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet(f"border-bottom: 1px solid {COLORS['border']};")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("🎙️ AnhMin Audio")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['accent']};
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Claude AI Project Manager")
        subtitle.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # New project button
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(12, 12, 12, 12)
        
        new_btn = QPushButton("➕ Dự án mới")
        new_btn.setObjectName("primaryButton")
        new_btn.setMinimumHeight(40)
        new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        new_btn.clicked.connect(self.create_new_project)
        btn_layout.addWidget(new_btn)
        
        layout.addWidget(btn_container)
        
        # Project list label
        list_label = QLabel("Dự án của bạn")
        list_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            text-transform: uppercase;
            padding: 8px 16px;
        """)
        layout.addWidget(list_label)
        
        # Project list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.project_list = QWidget()
        self.project_list.setStyleSheet("background: transparent;")
        self.project_list_layout = QVBoxLayout(self.project_list)
        self.project_list_layout.setContentsMargins(8, 0, 8, 8)
        self.project_list_layout.setSpacing(4)
        self.project_list_layout.addStretch()
        
        scroll.setWidget(self.project_list)
        layout.addWidget(scroll, 1)
        
        # Settings button
        settings_container = QWidget()
        settings_container.setStyleSheet(f"border-top: 1px solid {COLORS['border']};")
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setSpacing(8)
        
        # API Status display
        self.api_status_frame = QFrame()
        self.api_status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        api_status_layout = QVBoxLayout(self.api_status_frame)
        api_status_layout.setContentsMargins(10, 8, 10, 8)
        api_status_layout.setSpacing(4)
        
        # Status row
        status_row = QHBoxLayout()
        self.api_status_icon = QLabel("⚪")
        self.api_status_icon.setStyleSheet("font-size: 12px;")
        status_row.addWidget(self.api_status_icon)
        
        self.api_status_text = QLabel("API: Chưa cấu hình")
        self.api_status_text.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
        status_row.addWidget(self.api_status_text)
        status_row.addStretch()
        
        api_status_layout.addLayout(status_row)
        
        # Usage row
        self.api_usage_label = QLabel("📊 Hôm nay: -- tokens")
        self.api_usage_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        api_status_layout.addWidget(self.api_usage_label)
        
        settings_layout.addWidget(self.api_status_frame)
        
        settings_btn = QPushButton("⚙️ Cài đặt API")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self.settings_clicked.emit)
        settings_layout.addWidget(settings_btn)

        # Update button with notification badge
        update_btn_container = QFrame()
        update_btn_container.setFixedHeight(40)

        # Use absolute positioning for badge overlay
        self.update_btn = QPushButton("🔄 Cập nhật", update_btn_container)
        self.update_btn.setGeometry(0, 0, 200, 40)
        self.update_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_btn.clicked.connect(self.update_clicked.emit)

        # Red dot notification badge - positioned absolutely on top
        self.update_badge = QLabel("●", update_btn_container)
        self.update_badge.setGeometry(160, 0, 20, 20)  # Top-right corner
        self.update_badge.setStyleSheet(f"""
            QLabel {{
                color: #EF4444;
                font-size: 18px;
                background: transparent;
            }}
        """)
        self.update_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_badge.setVisible(False)
        self.update_badge.raise_()  # Ensure badge is on top

        settings_layout.addWidget(update_btn_container)

        layout.addWidget(settings_container)
        
        # Start status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_api_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        self.update_api_status()
    
    def update_api_status(self):
        """Update API status display."""
        status = db.get_api_status()
        usage = db.get_usage_today()
        
        # Update status icon and text
        if status['status'] == 'ok':
            self.api_status_icon.setText("🟢")
            self.api_status_text.setText(f"API: {status['current_key_name'] or 'Hoạt động'}")
        elif status['status'] == 'warning':
            self.api_status_icon.setText("🟡")
            self.api_status_text.setText("API: Có lỗi")
        elif status['status'] == 'none':
            self.api_status_icon.setText("⚪")
            self.api_status_text.setText("API: Chưa cấu hình")
        else:
            self.api_status_icon.setText("🔴")
            self.api_status_text.setText("API: Lỗi")
        
        # Update usage
        total_tokens = usage['input_tokens'] + usage['output_tokens']
        if total_tokens > 0:
            self.api_usage_label.setText(f"📊 Hôm nay: {self.format_tokens(total_tokens)}")
        else:
            self.api_usage_label.setText("📊 Hôm nay: 0 tokens")
    
    def format_tokens(self, tokens: int) -> str:
        """Format token count."""
        if tokens >= 1000000:
            return f"{tokens/1000000:.1f}M"
        elif tokens >= 1000:
            return f"{tokens/1000:.1f}K"
        return str(tokens)
    
    def load_projects(self):
        """Load projects from database."""
        # Clear existing
        for widget in self.project_widgets.values():
            widget.deleteLater()
        self.project_widgets.clear()
        
        # Remove stretch
        while self.project_list_layout.count() > 0:
            item = self.project_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load from database
        projects = db.get_all_projects()
        for project in projects:
            self.add_project_widget(project)
        
        self.project_list_layout.addStretch()
    
    def add_project_widget(self, project: dict):
        """Add a project widget to the list."""
        widget = ProjectItemWidget(
            project['id'],
            project['name'],
            bool(project['is_active'])
        )
        widget.clicked.connect(self.on_project_clicked)
        widget.delete_requested.connect(self.delete_project)
        widget.rename_requested.connect(self.rename_project)
        
        # Insert before stretch
        count = self.project_list_layout.count()
        self.project_list_layout.insertWidget(count - 1, widget)
        self.project_widgets[project['id']] = widget
        
        if project['is_active']:
            self.current_project_id = project['id']
    
    def create_new_project(self):
        """Show dialog to create new project."""
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            if name:
                from config import DEFAULT_INSTRUCTIONS
                project_id = db.create_project(name, DEFAULT_INSTRUCTIONS)
                db.set_active_project(project_id)
                self.load_projects()
                self.project_selected.emit(project_id)
    
    def on_project_clicked(self, project_id: int):
        """Handle project selection."""
        if self.current_project_id and self.current_project_id in self.project_widgets:
            self.project_widgets[self.current_project_id].set_active(False)
        
        self.current_project_id = project_id
        if project_id in self.project_widgets:
            self.project_widgets[project_id].set_active(True)
        
        db.set_active_project(project_id)
        self.project_selected.emit(project_id)
    
    def delete_project(self, project_id: int):
        """Delete a project."""
        project = db.get_project(project_id)
        if not project:
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa dự án '{project['name']}'?\n"
            "Tất cả dữ liệu liên quan sẽ bị xóa vĩnh viễn.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_project(project_id)
            self.load_projects()
            
            # Select first project if current was deleted
            if self.current_project_id == project_id:
                projects = db.get_all_projects()
                if projects:
                    self.on_project_clicked(projects[0]['id'])
    
    def rename_project(self, project_id: int):
        """Rename a project."""
        project = db.get_project(project_id)
        if not project:
            return

        dialog = NewProjectDialog(self)
        dialog.setWindowTitle("Đổi tên dự án")
        dialog.name_input.setText(project['name'])

        if dialog.exec():
            new_name = dialog.get_name()
            if new_name:
                db.update_project(project_id, name=new_name)
                self.load_projects()

    def show_update_badge(self, show: bool = True):
        """Show or hide the update notification badge."""
        self.update_badge.setVisible(show)
