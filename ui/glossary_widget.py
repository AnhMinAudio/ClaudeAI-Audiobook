"""
AnhMin Audio - Glossary Widget
Manage terminology for consistent translation
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit, QComboBox,
    QDialog, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from ui.styles import COLORS


class TermEditorDialog(QDialog):
    """Dialog for adding/editing a glossary term."""
    
    def __init__(self, term: dict = None, categories: list = None, parent=None):
        super().__init__(parent)
        self.term = term
        self.categories = categories or []
        self.setWindowTitle("Chỉnh sửa thuật ngữ" if term else "Thêm thuật ngữ")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Category
        cat_row = QHBoxLayout()
        cat_label = QLabel("Danh mục:")
        cat_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        cat_row.addWidget(cat_label)
        
        self.cat_combo = QComboBox()
        for cat in self.categories:
            self.cat_combo.addItem(f"{cat['icon']} {cat['name']}", cat['id'])
        
        if self.term and self.term.get('category_id'):
            for i in range(self.cat_combo.count()):
                if self.cat_combo.itemData(i) == self.term['category_id']:
                    self.cat_combo.setCurrentIndex(i)
                    break
        
        self.cat_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        cat_row.addWidget(self.cat_combo, 1)
        layout.addLayout(cat_row)
        
        # Original / Variants
        orig_label = QLabel("Thuật ngữ gốc / Các cách viết khác:")
        orig_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(orig_label)
        
        orig_hint = QLabel("(Có thể nhập tiếng Trung, Việt, Anh, Pinyin... - phân cách bằng dấu phẩy)")
        orig_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(orig_hint)
        
        self.original_input = QLineEdit()
        self.original_input.setPlaceholderText("Ví dụ: 斗帝, Dou Di, Đấu Đế, đấu đế")
        self.original_input.setText(self.term.get('original', '') if self.term else '')
        self.original_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        layout.addWidget(self.original_input)
        
        # Standard
        std_label = QLabel("✅ Cách viết chuẩn (sẽ dùng trong audiobook):")
        std_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(std_label)
        
        self.standard_input = QLineEdit()
        self.standard_input.setPlaceholderText("Ví dụ: Đấu đế")
        self.standard_input.setText(self.term.get('standard', '') if self.term else '')
        self.standard_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 12px;
                color: {COLORS['text_primary']};
                font-weight: 600;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        layout.addWidget(self.standard_input)
        
        # Notes
        notes_label = QLabel("Ghi chú (tùy chọn):")
        notes_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Giải thích cho Claude hiểu ngữ cảnh...")
        self.notes_input.setText(self.term.get('notes', '') if self.term else '')
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
            }}
        """)
        layout.addWidget(self.notes_input)
        
        layout.addStretch()
        
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
        """Validate and save."""
        standard = self.standard_input.text().strip()
        
        if not standard:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập cách viết chuẩn")
            return
        
        if not self.cat_combo.currentData():
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn danh mục")
            return
        
        self.result_data = {
            'category_id': self.cat_combo.currentData(),
            'original': self.original_input.text().strip(),
            'standard': standard,
            'notes': self.notes_input.toPlainText().strip()
        }
        
        self.accept()


class CategoryEditorDialog(QDialog):
    """Dialog for adding/editing a category."""
    
    def __init__(self, category: dict = None, project_id: int = None, parent=None):
        super().__init__(parent)
        self.category = category
        self.project_id = project_id
        self.setWindowTitle("Chỉnh sửa danh mục" if category else "Thêm danh mục")
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_dark']}; }}")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Name row
        name_row = QHBoxLayout()
        
        name_label = QLabel("Tên danh mục:")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        name_row.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ví dụ: Cảnh giới")
        self.name_input.setText(self.category.get('name', '') if self.category else '')
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
        
        layout.addLayout(name_row)
        
        # Icon row
        icon_row = QHBoxLayout()
        
        icon_label = QLabel("Icon:")
        icon_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        icon_row.addWidget(icon_label)
        
        self.icon_input = QLineEdit()
        self.icon_input.setMaximumWidth(60)
        self.icon_input.setText(self.category.get('icon', '📂') if self.category else '📂')
        self.icon_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 18px;
            }}
        """)
        icon_row.addWidget(self.icon_input)
        
        icon_row.addStretch()
        
        layout.addLayout(icon_row)
        
        # Scope row
        scope_row = QHBoxLayout()
        
        scope_label = QLabel("Phạm vi:")
        scope_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        scope_row.addWidget(scope_label)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("🌐 Global (dùng cho tất cả project)", True)
        self.scope_combo.addItem("📁 Project này", False)
        
        if self.category and self.category.get('is_global'):
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
        
        layout.addStretch()
        
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
            }}
        """)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(save_btn)
        
        layout.addLayout(btn_row)
    
    def save(self):
        """Validate and save."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên danh mục")
            return
        
        self.result_data = {
            'name': name,
            'icon': self.icon_input.text() or '📂',
            'is_global': self.scope_combo.currentData()
        }
        
        self.accept()


class GlossaryWidget(QWidget):
    """Glossary management widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.current_category_id = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title = QLabel("📚 Thuật ngữ")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        title_section.addWidget(title)
        
        subtitle = QLabel("Quản lý thuật ngữ để đảm bảo nhất quán trong toàn bộ series")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        title_section.addWidget(subtitle)
        
        header.addLayout(title_section)
        header.addStretch()
        
        # Import/Export buttons
        import_btn = QPushButton("📥 Import")
        import_btn.setStyleSheet(f"""
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
        import_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        import_btn.clicked.connect(self.import_glossary)
        header.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.setStyleSheet(f"""
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
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.clicked.connect(self.export_glossary)
        header.addWidget(export_btn)
        
        layout.addLayout(header)
        
        # Main content - split view
        content = QHBoxLayout()
        content.setSpacing(16)
        
        # Left panel - Categories
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        
        cat_header = QHBoxLayout()
        cat_label = QLabel("📂 Danh mục")
        cat_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        cat_header.addWidget(cat_label)
        
        cat_header.addStretch()
        
        add_cat_btn = QPushButton("➕")
        add_cat_btn.setFixedSize(28, 28)
        add_cat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
        """)
        add_cat_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_cat_btn.setToolTip("Thêm danh mục")
        add_cat_btn.clicked.connect(self.add_category)
        cat_header.addWidget(add_cat_btn)
        
        left_panel.addLayout(cat_header)
        
        # Category list
        self.cat_scroll = QScrollArea()
        self.cat_scroll.setWidgetResizable(True)
        self.cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cat_scroll.setMinimumWidth(200)
        self.cat_scroll.setMaximumWidth(250)
        self.cat_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_light']};
            }}
        """)
        
        self.cat_list = QWidget()
        self.cat_list.setStyleSheet(f"background-color: {COLORS['bg_light']};")
        self.cat_list_layout = QVBoxLayout(self.cat_list)
        self.cat_list_layout.setContentsMargins(8, 8, 8, 8)
        self.cat_list_layout.setSpacing(4)
        self.cat_list_layout.addStretch()
        
        self.cat_scroll.setWidget(self.cat_list)
        left_panel.addWidget(self.cat_scroll, 1)
        
        content.addLayout(left_panel)
        
        # Right panel - Terms
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        terms_header = QHBoxLayout()
        
        self.terms_title = QLabel("Chọn danh mục để xem thuật ngữ")
        self.terms_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        terms_header.addWidget(self.terms_title)
        
        terms_header.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_input.setMaximumWidth(200)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_terms)
        terms_header.addWidget(self.search_input)
        
        self.add_term_btn = QPushButton("➕ Thêm thuật ngữ")
        self.add_term_btn.setStyleSheet(f"""
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
        self.add_term_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_term_btn.clicked.connect(self.add_term)
        self.add_term_btn.setEnabled(False)
        terms_header.addWidget(self.add_term_btn)
        
        right_panel.addLayout(terms_header)
        
        # Terms table
        self.terms_table = QTableWidget()
        self.terms_table.setColumnCount(4)
        self.terms_table.setHorizontalHeaderLabels(["Thuật ngữ gốc", "Cách viết chuẩn", "Ghi chú", "Thao tác"])
        self.terms_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.terms_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.terms_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.terms_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.terms_table.setColumnWidth(3, 120)
        self.terms_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.terms_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.terms_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
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
                padding: 10px;
                border: none;
                font-weight: 500;
            }}
        """)
        right_panel.addWidget(self.terms_table, 1)
        
        content.addLayout(right_panel, 1)
        
        layout.addLayout(content, 1)
        
        # Stats footer
        self.stats_label = QLabel("Tổng: 0 danh mục, 0 thuật ngữ")
        self.stats_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.stats_label)
    
    def set_project(self, project_id: int):
        """Set current project."""
        self.project_id = project_id
        self.load_categories()
        self.update_stats()
    
    def load_categories(self):
        """Load categories list."""
        # Clear existing
        while self.cat_list_layout.count() > 1:
            item = self.cat_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        categories = db.get_glossary_categories(self.project_id)
        
        for cat in categories:
            self.add_category_item(cat)
        
        # Select first if available
        if categories:
            self.select_category(categories[0]['id'])
    
    def add_category_item(self, category: dict):
        """Add category to list."""
        btn = QPushButton(f"{category['icon']} {category['name']}")
        btn.setProperty('category_id', category['id'])
        btn.setCheckable(True)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 12px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_lighter']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent_light']};
                color: {COLORS['accent']};
            }}
        """)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda: self.select_category(category['id']))
        
        # Context menu for edit/delete
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos: self.show_category_menu(category, btn.mapToGlobal(pos)))
        
        count = self.cat_list_layout.count()
        self.cat_list_layout.insertWidget(count - 1, btn)
    
    def show_category_menu(self, category: dict, pos):
        """Show context menu for category."""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['bg_lighter']};
            }}
        """)
        
        edit_action = menu.addAction("✏️ Sửa")
        delete_action = menu.addAction("🗑️ Xóa")
        
        action = menu.exec(pos)
        
        if action == edit_action:
            self.edit_category(category)
        elif action == delete_action:
            self.delete_category(category['id'])
    
    def select_category(self, category_id: int):
        """Select a category and load its terms."""
        self.current_category_id = category_id
        self.add_term_btn.setEnabled(True)
        
        # Update button states
        for i in range(self.cat_list_layout.count() - 1):
            btn = self.cat_list_layout.itemAt(i).widget()
            if btn:
                btn.setChecked(btn.property('category_id') == category_id)
        
        # Load terms
        self.load_terms()
    
    def load_terms(self):
        """Load terms for current category."""
        if not self.current_category_id:
            return
        
        categories = db.get_glossary_categories(self.project_id)
        cat_name = "Thuật ngữ"
        for cat in categories:
            if cat['id'] == self.current_category_id:
                cat_name = f"{cat['icon']} {cat['name']}"
                break
        
        self.terms_title.setText(cat_name)
        
        terms = db.get_glossary_terms(self.current_category_id)
        
        self.terms_table.setRowCount(len(terms))
        
        for i, term in enumerate(terms):
            # Original
            orig_item = QTableWidgetItem(term.get('original', ''))
            orig_item.setData(Qt.ItemDataRole.UserRole, term['id'])
            self.terms_table.setItem(i, 0, orig_item)
            
            # Standard
            std_item = QTableWidgetItem(term['standard'])
            std_item.setData(Qt.ItemDataRole.FontRole, True)
            self.terms_table.setItem(i, 1, std_item)
            
            # Notes
            notes_item = QTableWidgetItem(term.get('notes', '') or '')
            self.terms_table.setItem(i, 2, notes_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 0, 4, 0)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️ Sửa")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_lighter']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['border_light']};
                }}
            """)
            edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_btn.clicked.connect(lambda _, t=term: self.edit_term(t))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️ Xóa")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(239, 68, 68, 0.1);
                    color: {COLORS['error']};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: rgba(239, 68, 68, 0.2);
                }}
            """)
            delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_btn.clicked.connect(lambda _, tid=term['id']: self.delete_term(tid))
            actions_layout.addWidget(delete_btn)
            
            self.terms_table.setCellWidget(i, 3, actions_widget)
        
        self.update_stats()
    
    def filter_terms(self, text: str):
        """Filter terms by search text."""
        text = text.lower()
        for i in range(self.terms_table.rowCount()):
            match = False
            for j in range(3):  # Check first 3 columns
                item = self.terms_table.item(i, j)
                if item and text in item.text().lower():
                    match = True
                    break
            self.terms_table.setRowHidden(i, not match)
    
    def add_category(self):
        """Add new category."""
        dialog = CategoryEditorDialog(project_id=self.project_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.add_glossary_category(
                name=data['name'],
                project_id=self.project_id if not data['is_global'] else None,
                icon=data['icon'],
                is_global=data['is_global']
            )
            self.load_categories()
    
    def edit_category(self, category: dict):
        """Edit category."""
        dialog = CategoryEditorDialog(category, self.project_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.update_glossary_category(
                category['id'],
                name=data['name'],
                icon=data['icon']
            )
            self.load_categories()
    
    def delete_category(self, category_id: int):
        """Delete category."""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Xóa danh mục sẽ xóa tất cả thuật ngữ trong đó. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_glossary_category(category_id)
            if self.current_category_id == category_id:
                self.current_category_id = None
                self.terms_table.setRowCount(0)
                self.terms_title.setText("Chọn danh mục để xem thuật ngữ")
                self.add_term_btn.setEnabled(False)
            self.load_categories()
    
    def add_term(self):
        """Add new term."""
        if not self.current_category_id:
            return
        
        categories = db.get_glossary_categories(self.project_id)
        dialog = TermEditorDialog(categories=categories, parent=self)
        
        # Pre-select current category
        for i in range(dialog.cat_combo.count()):
            if dialog.cat_combo.itemData(i) == self.current_category_id:
                dialog.cat_combo.setCurrentIndex(i)
                break
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.add_glossary_term(
                category_id=data['category_id'],
                standard=data['standard'],
                original=data['original'],
                notes=data['notes']
            )
            self.load_terms()
    
    def edit_term(self, term: dict):
        """Edit term."""
        categories = db.get_glossary_categories(self.project_id)
        dialog = TermEditorDialog(term, categories, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            db.update_glossary_term(
                term['id'],
                original=data['original'],
                standard=data['standard'],
                notes=data['notes']
            )
            self.load_terms()
    
    def delete_term(self, term_id: int):
        """Delete term."""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn xóa thuật ngữ này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_glossary_term(term_id)
            self.load_terms()
    
    def update_stats(self):
        """Update statistics."""
        categories = db.get_glossary_categories(self.project_id)
        terms = db.get_all_glossary_terms(self.project_id)
        
        self.stats_label.setText(f"Tổng: {len(categories)} danh mục, {len(terms)} thuật ngữ")
    
    def import_glossary(self):
        """Import glossary from JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Glossary",
            "",
            "JSON Files (*.json)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import categories and terms
            imported_cats = 0
            imported_terms = 0
            
            for cat_data in data.get('categories', []):
                cat_id = db.add_glossary_category(
                    name=cat_data['name'],
                    icon=cat_data.get('icon', '📂'),
                    project_id=self.project_id,
                    is_global=False
                )
                imported_cats += 1
                
                for term_data in cat_data.get('terms', []):
                    db.add_glossary_term(
                        category_id=cat_id,
                        original=term_data.get('original', ''),
                        standard=term_data['standard'],
                        notes=term_data.get('notes', '')
                    )
                    imported_terms += 1
            
            self.load_categories()
            
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã import {imported_cats} danh mục và {imported_terms} thuật ngữ"
            )
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể import: {str(e)}")
    
    def export_glossary(self):
        """Export glossary to JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Glossary",
            "glossary.json",
            "JSON Files (*.json)"
        )
        
        if not filepath:
            return
        
        try:
            categories = db.get_glossary_categories(self.project_id)
            
            data = {
                'project': '',
                'version': '1.0',
                'categories': []
            }
            
            if self.project_id:
                project = db.get_project(self.project_id)
                data['project'] = project.get('name', '') if project else ''
            
            for cat in categories:
                terms = db.get_glossary_terms(cat['id'])
                cat_data = {
                    'name': cat['name'],
                    'icon': cat['icon'],
                    'terms': []
                }
                
                for term in terms:
                    cat_data['terms'].append({
                        'original': term.get('original', ''),
                        'standard': term['standard'],
                        'notes': term.get('notes', '')
                    })
                
                data['categories'].append(cat_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Thành công", f"Đã export glossary")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể export: {str(e)}")
