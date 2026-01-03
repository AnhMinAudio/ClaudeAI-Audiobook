"""
AnhMin Audio - Instructions Widget
Project instructions editor with template support
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QComboBox, QMessageBox, QDialog,
    QScrollArea, QLineEdit, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from api import claude_client
from ui.styles import COLORS
from config import DEFAULT_MODEL


class TemplateEditorDialog(QDialog):
    """Dialog for editing a template."""
    
    def __init__(self, template: dict = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Chỉnh sửa Template" if template else "Tạo Template mới")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Name row
        name_row = QHBoxLayout()
        
        name_label = QLabel("Tên:")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 60px;")
        name_row.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tên template...")
        self.name_input.setText(self.template.get('name', '') if self.template else '')
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        name_row.addWidget(self.name_input, 1)
        
        # Icon
        icon_label = QLabel("Icon:")
        icon_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 16px;")
        name_row.addWidget(icon_label)
        
        self.icon_input = QLineEdit()
        self.icon_input.setMaximumWidth(50)
        self.icon_input.setText(self.template.get('icon', '📝') if self.template else '📝')
        self.icon_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                text-align: center;
            }}
        """)
        name_row.addWidget(self.icon_input)
        
        layout.addLayout(name_row)
        
        # Scope row
        scope_row = QHBoxLayout()
        
        scope_label = QLabel("Phạm vi:")
        scope_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 60px;")
        scope_row.addWidget(scope_label)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("🌐 Global (dùng cho tất cả project)", True)
        self.scope_combo.addItem("📁 Project này", False)
        
        if self.template and self.template.get('is_global'):
            self.scope_combo.setCurrentIndex(0)
        else:
            self.scope_combo.setCurrentIndex(1)
        
        self.scope_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        scope_row.addWidget(self.scope_combo, 1)
        
        layout.addLayout(scope_row)
        
        # Content
        content_label = QLabel("Nội dung template:")
        content_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(content_label)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Nhập nội dung template...\n\nDùng {{GLOSSARY}} để tự động chèn thuật ngữ")
        self.content_input.setText(self.template.get('content', '') if self.template else '')
        self.content_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.content_input, 1)
        
        # Tips
        tips = QLabel("💡 Biến có sẵn: {{GLOSSARY}} - chèn thuật ngữ, {{PROJECT}} - tên project")
        tips.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(tips)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setStyleSheet(f"""
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
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Lưu")
        save_btn.setStyleSheet(f"""
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
        """)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(save_btn)
        
        layout.addLayout(btn_row)
    
    def save(self):
        """Save template."""
        name = self.name_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên template")
            return
        
        if not content:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập nội dung template")
            return
        
        self.result_data = {
            'name': name,
            'icon': self.icon_input.text() or '📝',
            'content': content,
            'is_global': self.scope_combo.currentData()
        }
        
        self.accept()


class TemplateManagerDialog(QDialog):
    """Dialog for managing templates."""
    
    def __init__(self, project_id: int = None, parent=None):
        super().__init__(parent)
        self.project_id = project_id
        self.setWindowTitle("Quản lý Template")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setup_ui()
        self.load_templates()
    
    def setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📋 Quản lý Template")
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("➕ Tạo mới")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.clicked.connect(self.add_template)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Template list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setStyleSheet(f"""
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
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def load_templates(self):
        """Load templates list."""
        # Clear existing
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        templates = db.get_templates(self.project_id)
        
        for tmpl in templates:
            self.add_template_item(tmpl)
    
    def add_template_item(self, template: dict):
        """Add a template item to the list."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        
        # Icon and name
        icon = QLabel(template.get('icon', '📝'))
        icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon)
        
        name = QLabel(template['name'])
        name.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        layout.addWidget(name)
        
        # Scope badge
        if template.get('is_global'):
            scope = QLabel("🌐 Global")
            scope.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        else:
            scope = QLabel("📁 Project")
            scope.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(scope)
        
        layout.addStretch()
        
        # Default badge
        if template.get('is_default'):
            default = QLabel("Mặc định")
            default.setStyleSheet(f"""
                color: {COLORS['accent']};
                background-color: {COLORS['accent_light']};
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 10px;
            """)
            layout.addWidget(default)
        
        # Edit button
        edit_btn = QPushButton("✏️ Sửa")
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(lambda: self.edit_template(template))
        layout.addWidget(edit_btn)
        
        # Delete button (only for non-default)
        if not template.get('is_default'):
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
            delete_btn.clicked.connect(lambda: self.delete_template(template['id']))
            layout.addWidget(delete_btn)
        
        count = self.list_layout.count()
        self.list_layout.insertWidget(count - 1, frame)
    
    def add_template(self):
        """Add new template."""
        dialog = TemplateEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.add_template(
                name=data['name'],
                content=data['content'],
                project_id=self.project_id if not data['is_global'] else None,
                icon=data['icon'],
                is_global=data['is_global']
            )
            self.load_templates()
    
    def edit_template(self, template: dict):
        """Edit existing template."""
        dialog = TemplateEditorDialog(template, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.update_template(
                template['id'],
                name=data['name'],
                content=data['content'],
                icon=data['icon'],
                is_global=data['is_global']
            )
            self.load_templates()
    
    def delete_template(self, template_id: int):
        """Delete a template."""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn xóa template này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_template(template_id)
            self.load_templates()


class InstructionsWidget(QWidget):
    """Instructions editor widget with template support."""
    
    instructions_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.current_template_id = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(16)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title = QLabel("📝 Hướng dẫn")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        subtitle = QLabel("Hướng dẫn này sẽ được áp dụng cho tất cả các cuộc trò chuyện trong dự án.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header.addWidget(subtitle)

        layout.addLayout(header)

        # Project Settings (Model & Thinking)
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(16, 12, 16, 12)
        settings_layout.setSpacing(12)

        # Settings header
        settings_header = QLabel("⚙️ Cài đặt Project")
        settings_header.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 14px;")
        settings_layout.addWidget(settings_header)

        # Model selection row
        model_row = QHBoxLayout()

        model_label = QLabel("🤖 Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; min-width: 100px;")
        model_row.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
            QComboBox:hover {{
                border-color: {COLORS['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        model_row.addWidget(self.model_combo, 1)

        # Refresh models button
        refresh_btn = QPushButton("🔄 Cập nhật")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh_models)
        model_row.addWidget(refresh_btn)

        settings_layout.addLayout(model_row)

        # Extended Thinking row
        thinking_row = QHBoxLayout()

        thinking_label = QLabel("🧠 Extended Thinking:")
        thinking_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; min-width: 100px;")
        thinking_row.addWidget(thinking_label)

        self.thinking_checkbox = QCheckBox("Bật chế độ suy nghĩ nâng cao (khuyến nghị cho Opus/Sonnet 4+)")
        self.thinking_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {COLORS['border']};
                background-color: {COLORS['bg_dark']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
        """)
        self.thinking_checkbox.stateChanged.connect(self.on_thinking_changed)
        thinking_row.addWidget(self.thinking_checkbox, 1)

        settings_layout.addLayout(thinking_row)

        # Info note
        info_note = QLabel("💡 Các cài đặt này chỉ áp dụng cho project hiện tại")
        info_note.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        settings_layout.addWidget(info_note)

        layout.addWidget(settings_frame)

        # Template selector
        template_frame = QFrame()
        template_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        template_layout = QHBoxLayout(template_frame)
        template_layout.setContentsMargins(16, 12, 16, 12)
        
        template_label = QLabel("📋 Template:")
        template_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        template_layout.addWidget(template_label)
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(250)
        self.template_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
            QComboBox:hover {{
                border-color: {COLORS['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
        """)
        self.template_combo.currentIndexChanged.connect(self.on_template_selected)
        template_layout.addWidget(self.template_combo, 1)
        
        apply_btn = QPushButton("Áp dụng")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        apply_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        apply_btn.clicked.connect(self.apply_template)
        template_layout.addWidget(apply_btn)
        
        manage_btn = QPushButton("⚙️ Quản lý")
        manage_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        manage_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        manage_btn.clicked.connect(self.open_template_manager)
        template_layout.addWidget(manage_btn)
        
        layout.addWidget(template_frame)
        
        # Text editor (read-only)
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)  # Read-only mode
        self.editor.setPlaceholderText("📋 Chọn template ở trên và nhấn 'Áp dụng' để hiển thị hướng dẫn\n\n💡 Để chỉnh sửa nội dung, vào 'Quản lý' → sửa template → áp dụng lại")
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.6;
                color: {COLORS['text_primary']};
            }}
            QTextEdit[readOnly="true"] {{
                background-color: {COLORS['bg_lighter']};
                border-style: dashed;
            }}
        """)
        self.editor.setMinimumHeight(300)
        self.editor.mousePressEvent = self.on_editor_clicked
        layout.addWidget(self.editor, 1)
        
        # Footer with info
        footer = QHBoxLayout()

        self.char_count = QLabel("0 ký tự")
        self.char_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        footer.addWidget(self.char_count)

        footer.addStretch()

        # Info about variables
        var_info = QLabel("💡 {{GLOSSARY}} sẽ tự động chèn thuật ngữ khi gửi")
        var_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        footer.addWidget(var_info)

        footer.addStretch()

        # Read-only notice
        readonly_notice = QLabel("📖 Chế độ xem • Sửa qua Template")
        readonly_notice.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            background-color: {COLORS['bg_lighter']};
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 11px;
        """)
        footer.addWidget(readonly_notice)

        layout.addLayout(footer)
    
    def set_project(self, project_id: int):
        """Load project instructions."""
        self.project_id = project_id
        self.load_templates()
        self.load_models()

        project = db.get_project(project_id)
        if project:
            instructions = project.get('instructions', '')
            self.editor.setPlainText(instructions)
            self.update_char_count()

            # Load project-specific model
            project_model = project.get('model')
            if project_model:
                # Find and select the model
                index = self.model_combo.findData(project_model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                else:
                    # Model not in list, add it
                    self.model_combo.addItem(f"🔹 {project_model}", project_model)
                    self.model_combo.setCurrentIndex(self.model_combo.count() - 1)
            else:
                # Use default (first model in list)
                self.model_combo.setCurrentIndex(0)

            # Load project-specific thinking setting
            extended_thinking = project.get('extended_thinking', 1)
            self.thinking_checkbox.setChecked(bool(extended_thinking))
    
    def load_templates(self):
        """Load templates into combo box."""
        self.template_combo.clear()
        self.template_combo.addItem("-- Chọn template --", None)
        
        templates = db.get_templates(self.project_id)
        
        for tmpl in templates:
            icon = tmpl.get('icon', '📝')
            name = tmpl['name']
            scope = " (Global)" if tmpl.get('is_global') else ""
            self.template_combo.addItem(f"{icon} {name}{scope}", tmpl['id'])
    
    def on_template_selected(self, index: int):
        """Handle template selection."""
        template_id = self.template_combo.currentData()
        self.current_template_id = template_id
    
    def apply_template(self):
        """Apply selected template to editor and save to database."""
        if not self.current_template_id:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn template")
            return

        template = db.get_template(self.current_template_id)
        if template:
            content = template['content']

            # Replace variables
            if '{{GLOSSARY}}' in content:
                glossary = db.get_glossary_for_prompt(self.project_id)
                content = content.replace('{{GLOSSARY}}', glossary)

            if '{{PROJECT}}' in content:
                project = db.get_project(self.project_id)
                project_name = project.get('name', '') if project else ''
                content = content.replace('{{PROJECT}}', project_name)

            # Confirm if editor has content
            if self.editor.toPlainText().strip():
                reply = QMessageBox.question(
                    self,
                    "Xác nhận",
                    "Nội dung hiện tại sẽ bị thay thế. Tiếp tục?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Apply to editor and save to database
            self.editor.setPlainText(content)
            self.update_char_count()

            # Save to database immediately
            if self.project_id:
                db.update_project(self.project_id, instructions=content)
                self.instructions_saved.emit()
                QMessageBox.information(self, "Thành công", "Đã áp dụng template và lưu hướng dẫn!")
    
    def open_template_manager(self):
        """Open template manager dialog."""
        dialog = TemplateManagerDialog(self.project_id, parent=self)
        dialog.exec()
        self.load_templates()

    def on_editor_clicked(self, event):
        """Handle click on read-only editor."""
        QMessageBox.information(
            self,
            "Chế độ chỉ xem",
            "Khung này chỉ hiển thị nội dung từ template.\n\n"
            "Để chỉnh sửa:\n"
            "1. Nhấn nút '⚙️ Quản lý' để mở Template Manager\n"
            "2. Sửa template mong muốn\n"
            "3. Quay lại và nhấn 'Áp dụng' để cập nhật"
        )

    def update_char_count(self):
        """Update character count."""
        text = self.editor.toPlainText()
        self.char_count.setText(f"{len(text)} ký tự")

    def load_models(self):
        """Load available models into combo box."""
        self.model_combo.blockSignals(True)  # Prevent triggering on_model_changed
        self.model_combo.clear()

        # Get available models from claude_client
        models = claude_client.available_models
        if not models:
            # Try to fetch if not already loaded
            models = claude_client.fetch_available_models()

        # Use fallback if still empty
        if not models:
            from config import FALLBACK_MODELS
            models = FALLBACK_MODELS  # Already in correct format

        # Add models to combo
        for display_name, model_id in models:
            self.model_combo.addItem(display_name, model_id)

        self.model_combo.blockSignals(False)

    def refresh_models(self):
        """Refresh models from API."""
        # Check if API key exists
        from database import db
        api_key = db.get_active_api_key()

        if not api_key:
            QMessageBox.warning(
                self,
                "Thiếu API Key",
                "Vui lòng thêm API key trong Settings trước khi cập nhật models.\n\n"
                "Hiện đang sử dụng danh sách models mặc định."
            )
            return

        models = claude_client.fetch_available_models()
        if models:
            self.load_models()
            QMessageBox.information(self, "Thành công", f"Đã cập nhật {len(models)} models từ API")
        else:
            QMessageBox.warning(
                self,
                "Lỗi kết nối",
                "Không thể tải danh sách models từ API.\n\n"
                "Vui lòng kiểm tra:\n"
                "• API key có hợp lệ không\n"
                "• Kết nối internet\n\n"
                "Hiện đang sử dụng danh sách models mặc định."
            )

    def on_model_changed(self, index: int):
        """Handle model selection change."""
        if not self.project_id:
            return

        model_id = self.model_combo.currentData()
        if model_id:
            # Save to database
            db.update_project(self.project_id, model=model_id)
            print(f"Project {self.project_id}: Model changed to {model_id}")

    def on_thinking_changed(self, state: int):
        """Handle thinking checkbox change."""
        if not self.project_id:
            return

        # Save to database (1 for checked, 0 for unchecked)
        extended_thinking = 1 if state == Qt.CheckState.Checked.value else 0
        db.update_project(self.project_id, extended_thinking=extended_thinking)
        print(f"Project {self.project_id}: Extended thinking = {extended_thinking}")
