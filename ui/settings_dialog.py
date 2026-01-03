"""
AnhMin Audio - Settings Dialog
API keys management with status and usage tracking
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QComboBox, QMessageBox, QScrollArea,
    QWidget, QSpinBox, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from api import claude_client
from ui.styles import COLORS
from config import FALLBACK_MODELS, DEFAULT_MODEL


class TestKeyWorker(QThread):
    """Worker thread for testing API key."""
    finished = pyqtSignal(dict)
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
    
    def run(self):
        result = claude_client.test_api_key(self.api_key)
        self.finished.emit(result)


class APIKeyItemWidget(QFrame):
    """Widget for a single API key item."""
    
    def __init__(self, key_id: int, name: str, api_key: str, priority: int,
                 is_active: bool, error_count: int, last_used: str,
                 current_key_id: int, on_delete, on_update, on_test, on_reset):
        super().__init__()
        self.key_id = key_id
        self.api_key = api_key
        self.on_delete = on_delete
        self.on_update = on_update
        self.on_test = on_test
        self.on_reset = on_reset
        self.is_current = (key_id == current_key_id)
        self.setup_ui(name, api_key, priority, is_active, error_count, last_used)
    
    def setup_ui(self, name: str, api_key: str, priority: int, 
                 is_active: bool, error_count: int, last_used: str):
        # Highlight if current key
        if self.is_current:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_light']};
                    border-radius: 10px;
                    border: 2px solid {COLORS['accent']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_light']};
                    border-radius: 10px;
                }}
            """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # Header row
        header = QHBoxLayout()
        
        # Name input
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Tên API key")
        self.name_input.setMaximumWidth(180)
        self.name_input.textChanged.connect(self.save_changes)
        header.addWidget(self.name_input)
        
        # Status badge
        if self.is_current:
            badge = QLabel("⭐ Đang sử dụng")
            badge.setStyleSheet(f"""
                color: {COLORS['accent']};
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
                background-color: {COLORS['accent_light']};
                border-radius: 4px;
            """)
            header.addWidget(badge)
        elif error_count >= 3:
            badge = QLabel("❌ Lỗi")
            badge.setStyleSheet(f"""
                color: {COLORS['error']};
                font-size: 11px;
                padding: 2px 8px;
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            """)
            header.addWidget(badge)
        elif is_active:
            badge = QLabel("⏸️ Dự phòng")
            badge.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                font-size: 11px;
                padding: 2px 8px;
                background-color: {COLORS['bg_lighter']};
                border-radius: 4px;
            """)
            header.addWidget(badge)
        
        header.addStretch()
        
        # Priority
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        header.addWidget(priority_label)
        
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 10)
        self.priority_spin.setValue(priority)
        self.priority_spin.setMaximumWidth(50)
        self.priority_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 6px;
                color: {COLORS['text_primary']};
                font-weight: 600;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {COLORS['bg_lighter']};
                border: none;
                width: 12px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        self.priority_spin.valueChanged.connect(self.save_changes)
        header.addWidget(self.priority_spin)
        
        layout.addLayout(header)
        
        # API key input row
        key_row = QHBoxLayout()
        
        self.key_input = QLineEdit(api_key)
        self.key_input.setPlaceholderText("sk-ant-api03-...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.textChanged.connect(self.save_changes)
        self.key_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
        """)
        key_row.addWidget(self.key_input, 1)
        
        layout.addLayout(key_row)
        
        # Info and actions row
        info_row = QHBoxLayout()
        
        # Error count
        error_label = QLabel(f"Lỗi: {error_count}/3")
        if error_count >= 3:
            error_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 11px;")
        else:
            error_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info_row.addWidget(error_label)
        
        # Last used
        if last_used:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
                last_used_str = dt.strftime("%H:%M %d/%m")
            except:
                last_used_str = "N/A"
        else:
            last_used_str = "Chưa sử dụng"
        
        used_label = QLabel(f"Dùng: {last_used_str}")
        used_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info_row.addWidget(used_label)
        
        info_row.addStretch()
        
        # Action buttons
        test_btn = QPushButton("🔍 Kiểm tra")
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        test_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        test_btn.clicked.connect(lambda: self.on_test(self.key_id, self.key_input.text()))
        info_row.addWidget(test_btn)
        
        if error_count > 0:
            reset_btn = QPushButton("🔄 Reset lỗi")
            reset_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_lighter']};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    color: {COLORS['text_primary']};
                }}
                QPushButton:hover {{
                    background-color: {COLORS['border_light']};
                }}
            """)
            reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            reset_btn.clicked.connect(lambda: self.on_reset(self.key_id))
            info_row.addWidget(reset_btn)
        
        show_btn = QPushButton("👁️")
        show_btn.setFixedSize(28, 24)
        show_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 12px;
            }}
        """)
        show_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        show_btn.pressed.connect(lambda: self.key_input.setEchoMode(QLineEdit.EchoMode.Normal))
        show_btn.released.connect(lambda: self.key_input.setEchoMode(QLineEdit.EchoMode.Password))
        info_row.addWidget(show_btn)
        
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
        delete_btn.clicked.connect(lambda: self.on_delete(self.key_id))
        info_row.addWidget(delete_btn)
        
        layout.addLayout(info_row)
    
    def save_changes(self):
        """Save changes to database."""
        self.on_update(
            self.key_id,
            name=self.name_input.text(),
            api_key=self.key_input.text(),
            priority=self.priority_spin.value()
        )


class SettingsDialog(QDialog):
    """Settings dialog for API keys management."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt API")
        self.setModal(True)
        self.setMinimumSize(700, 800)
        self.key_widgets = {}
        self.test_worker = None
        self.setup_ui()
        self.load_api_keys()
        self.refresh_usage_stats()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("⚙️ Cài đặt API")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(title)
        
        # ============== Overview Section ==============
        overview_frame = QFrame()
        overview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        overview_layout = QHBoxLayout(overview_frame)
        overview_layout.setContentsMargins(20, 16, 20, 16)
        overview_layout.setSpacing(24)
        
        # Keys stat
        self.stat_keys = self.create_stat_widget("🔑 Keys", "0")
        overview_layout.addWidget(self.stat_keys)
        
        # Current key
        self.stat_current = self.create_stat_widget("🟢 Đang dùng", "--")
        overview_layout.addWidget(self.stat_current)
        
        # Errors
        self.stat_errors = self.create_stat_widget("⚠️ Lỗi", "0")
        overview_layout.addWidget(self.stat_errors)
        
        # Today usage
        self.stat_today = self.create_stat_widget("📊 Hôm nay", "0")
        overview_layout.addWidget(self.stat_today)
        
        layout.addWidget(overview_frame)
        
        # ============== Model & Thinking Section ==============
        settings_row = QHBoxLayout()
        settings_row.setSpacing(12)
        
        # Model selection
        model_frame = QFrame()
        model_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        model_layout = QHBoxLayout(model_frame)
        model_layout.setContentsMargins(16, 12, 16, 12)
        
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        model_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.load_models()
        
        current_model = db.get_setting('default_model', DEFAULT_MODEL)
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == current_model:
                self.model_combo.setCurrentIndex(i)
                break
        
        self.model_combo.currentIndexChanged.connect(self.save_model)
        model_layout.addWidget(self.model_combo, 1)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("Làm mới danh sách models")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_lighter']};
                border-radius: 6px;
            }}
        """)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_btn)
        
        settings_row.addWidget(model_frame, 1)
        
        # Thinking settings
        thinking_frame = QFrame()
        thinking_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        thinking_layout = QHBoxLayout(thinking_frame)
        thinking_layout.setContentsMargins(16, 12, 16, 12)
        
        self.thinking_checkbox = QCheckBox("🧠 Extended Thinking")
        self.thinking_checkbox.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        thinking_enabled = db.get_setting('extended_thinking', 'true') == 'true'
        self.thinking_checkbox.setChecked(thinking_enabled)
        self.thinking_checkbox.stateChanged.connect(self.save_thinking_setting)
        thinking_layout.addWidget(self.thinking_checkbox)
        
        self.budget_spin = QSpinBox()
        self.budget_spin.setRange(1000, 50000)
        self.budget_spin.setSingleStep(1000)
        self.budget_spin.setValue(int(db.get_setting('thinking_budget', '10000')))
        self.budget_spin.setSuffix(" tokens")
        self.budget_spin.setMaximumWidth(110)
        self.budget_spin.valueChanged.connect(self.save_thinking_setting)
        thinking_layout.addWidget(self.budget_spin)
        
        settings_row.addWidget(thinking_frame, 1)
        
        layout.addLayout(settings_row)

        # ============== Truyện Phương Đông Login Section ==============
        tpd_label = QLabel("🔐 Truyện Phương Đông Login")
        tpd_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            margin-top: 8px;
        """)
        layout.addWidget(tpd_label)

        tpd_frame = QFrame()
        tpd_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        tpd_layout = QGridLayout(tpd_frame)
        tpd_layout.setContentsMargins(16, 16, 16, 16)
        tpd_layout.setSpacing(12)

        # Username field
        username_label = QLabel("Username:")
        username_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        tpd_layout.addWidget(username_label, 0, 0)

        self.tpd_username_input = QLineEdit()
        self.tpd_username_input.setPlaceholderText("Nhập username...")
        self.tpd_username_input.setText(db.get_setting('truyenphuongdong_username', ''))
        self.tpd_username_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
        """)
        self.tpd_username_input.textChanged.connect(self.save_tpd_credentials)
        tpd_layout.addWidget(self.tpd_username_input, 0, 1)

        # Password field
        password_label = QLabel("Password:")
        password_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        tpd_layout.addWidget(password_label, 1, 0)

        password_row = QHBoxLayout()
        password_row.setSpacing(8)

        self.tpd_password_input = QLineEdit()
        self.tpd_password_input.setPlaceholderText("Nhập password...")
        self.tpd_password_input.setText(db.get_setting('truyenphuongdong_password', ''))
        self.tpd_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tpd_password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
        """)
        self.tpd_password_input.textChanged.connect(self.save_tpd_credentials)
        password_row.addWidget(self.tpd_password_input, 1)

        # Show password button
        show_pwd_btn = QPushButton("👁️")
        show_pwd_btn.setFixedSize(32, 32)
        show_pwd_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_lighter']};
                border-radius: 6px;
            }}
        """)
        show_pwd_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        show_pwd_btn.pressed.connect(lambda: self.tpd_password_input.setEchoMode(QLineEdit.EchoMode.Normal))
        show_pwd_btn.released.connect(lambda: self.tpd_password_input.setEchoMode(QLineEdit.EchoMode.Password))
        password_row.addWidget(show_pwd_btn)

        tpd_layout.addLayout(password_row, 1, 1)

        # Info text
        tpd_info = QLabel("💡 Lưu tài khoản để tự động đăng nhập khi scrape từ truyenphuongdong.com")
        tpd_info.setWordWrap(True)
        tpd_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        tpd_layout.addWidget(tpd_info, 2, 0, 1, 2)

        layout.addWidget(tpd_frame)

        # ============== API Keys Section ==============
        keys_header = QHBoxLayout()
        
        keys_label = QLabel("🔑 API Keys")
        keys_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
        """)
        keys_header.addWidget(keys_label)
        
        keys_header.addStretch()
        
        add_btn = QPushButton("➕ Thêm API Key")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.clicked.connect(self.add_api_key)
        keys_header.addWidget(add_btn)
        
        layout.addLayout(keys_header)
        
        # Keys list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setMinimumHeight(180)
        
        self.keys_list = QWidget()
        self.keys_list.setStyleSheet("background: transparent;")
        self.keys_layout = QVBoxLayout(self.keys_list)
        self.keys_layout.setContentsMargins(0, 0, 0, 0)
        self.keys_layout.setSpacing(12)
        self.keys_layout.addStretch()
        
        scroll.setWidget(self.keys_list)
        layout.addWidget(scroll, 1)
        
        # ============== Usage Stats Section ==============
        usage_label = QLabel("📈 Thống kê sử dụng")
        usage_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(usage_label)
        
        usage_frame = QFrame()
        usage_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
            }}
        """)
        usage_layout = QHBoxLayout(usage_frame)
        usage_layout.setContentsMargins(16, 16, 16, 16)
        usage_layout.setSpacing(16)
        
        # Today
        self.usage_today = self.create_usage_widget("Hôm nay", "0", "0")
        usage_layout.addWidget(self.usage_today)
        
        # Week
        self.usage_week = self.create_usage_widget("Tuần này", "0", "0")
        usage_layout.addWidget(self.usage_week)
        
        # Month
        self.usage_month = self.create_usage_widget("Tháng này", "0", "0")
        usage_layout.addWidget(self.usage_month)
        
        layout.addWidget(usage_frame)
        
        # ============== Tips Section ==============
        tips = QLabel(
            "💡 Tips: Key có priority cao được ưu tiên • "
            "Lỗi 3 lần sẽ tạm dừng, dùng 'Reset lỗi' để kích hoạt lại • "
            "Khi hết quota tự động chuyển key"
        )
        tips.setWordWrap(True)
        tips.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            padding: 10px;
            background-color: {COLORS['bg_light']};
            border-radius: 6px;
        """)
        layout.addWidget(tips)
        
        # ============== Close Button ==============
        close_btn = QPushButton("Đóng")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
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
    
    def create_stat_widget(self, label: str, value: str) -> QFrame:
        """Create a stat display widget for overview."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        return frame
    
    def create_usage_widget(self, period: str, input_tokens: str, output_tokens: str) -> QFrame:
        """Create a usage display widget."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_dark']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Period label
        period_label = QLabel(period)
        period_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
        """)
        period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(period_label)
        
        # Input tokens
        input_row = QHBoxLayout()
        input_icon = QLabel("📥")
        input_icon.setStyleSheet("font-size: 11px;")
        input_row.addWidget(input_icon)
        
        input_label = QLabel("Input:")
        input_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        input_row.addWidget(input_label)
        
        input_value = QLabel(input_tokens)
        input_value.setObjectName("input_value")
        input_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 600;")
        input_row.addWidget(input_value)
        input_row.addStretch()
        
        layout.addLayout(input_row)
        
        # Output tokens
        output_row = QHBoxLayout()
        output_icon = QLabel("📤")
        output_icon.setStyleSheet("font-size: 11px;")
        output_row.addWidget(output_icon)
        
        output_label = QLabel("Output:")
        output_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        output_row.addWidget(output_label)
        
        output_value = QLabel(output_tokens)
        output_value.setObjectName("output_value")
        output_value.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 600;")
        output_row.addWidget(output_value)
        output_row.addStretch()
        
        layout.addLayout(output_row)
        
        return frame
    
    def format_tokens(self, tokens: int) -> str:
        """Format token count for display."""
        if tokens >= 1000000:
            return f"{tokens/1000000:.2f}M"
        elif tokens >= 1000:
            return f"{tokens/1000:.1f}K"
        return str(tokens)
    
    def refresh_usage_stats(self):
        """Refresh usage statistics."""
        # Today
        today = db.get_usage_today()
        self.usage_today.findChild(QLabel, "input_value").setText(self.format_tokens(today['input_tokens']))
        self.usage_today.findChild(QLabel, "output_value").setText(self.format_tokens(today['output_tokens']))
        
        # Week
        week = db.get_usage_week()
        self.usage_week.findChild(QLabel, "input_value").setText(self.format_tokens(week['input_tokens']))
        self.usage_week.findChild(QLabel, "output_value").setText(self.format_tokens(week['output_tokens']))
        
        # Month
        month = db.get_usage_month()
        self.usage_month.findChild(QLabel, "input_value").setText(self.format_tokens(month['input_tokens']))
        self.usage_month.findChild(QLabel, "output_value").setText(self.format_tokens(month['output_tokens']))
        
        # Overview stats
        status = db.get_api_status()
        self.stat_keys.findChild(QLabel, "value").setText(str(status['total_keys']))
        self.stat_current.findChild(QLabel, "value").setText(status['current_key_name'] or "--")
        self.stat_errors.findChild(QLabel, "value").setText(str(status['total_errors']))
        
        total_today = today['input_tokens'] + today['output_tokens']
        self.stat_today.findChild(QLabel, "value").setText(self.format_tokens(total_today))
    
    def load_api_keys(self):
        """Load API keys from database."""
        # Clear existing
        for widget in self.key_widgets.values():
            widget.deleteLater()
        self.key_widgets.clear()
        
        while self.keys_layout.count() > 1:
            item = self.keys_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get current key ID
        status = db.get_api_status()
        current_key_id = status.get('current_key_id')
        
        # Load from database
        keys = db.get_api_keys()
        for key in keys:
            self.add_key_widget(key, current_key_id)
        
        # Refresh overview
        self.refresh_usage_stats()
    
    def add_key_widget(self, key_data: dict, current_key_id: int = None):
        """Add an API key widget."""
        widget = APIKeyItemWidget(
            key_data['id'],
            key_data['name'],
            key_data['api_key'],
            key_data['priority'],
            bool(key_data['is_active']),
            key_data['error_count'],
            key_data.get('last_used', ''),
            current_key_id or 0,
            self.delete_api_key,
            self.update_api_key,
            self.test_api_key,
            self.reset_api_key_errors
        )
        
        count = self.keys_layout.count()
        self.keys_layout.insertWidget(count - 1, widget)
        self.key_widgets[key_data['id']] = widget
    
    def add_api_key(self):
        """Add a new API key."""
        if len(self.key_widgets) >= 3:
            QMessageBox.warning(self, "Giới hạn", "Chỉ có thể thêm tối đa 3 API keys")
            return
        
        key_id = db.add_api_key(
            f"API Key {len(self.key_widgets) + 1}",
            "",
            priority=len(self.key_widgets)
        )
        
        self.load_api_keys()
    
    def delete_api_key(self, key_id: int):
        """Delete an API key."""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc muốn xóa API key này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_api_key(key_id)
            self.load_api_keys()
    
    def update_api_key(self, key_id: int, **kwargs):
        """Update an API key."""
        db.update_api_key(key_id, **kwargs)
    
    def test_api_key(self, key_id: int, api_key: str):
        """Test an API key."""
        if not api_key or not api_key.startswith('sk-'):
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập API key hợp lệ (bắt đầu bằng sk-)")
            return
        
        self.test_worker = TestKeyWorker(api_key)
        self.test_worker.finished.connect(self.on_test_finished)
        self.test_worker.start()
    
    def on_test_finished(self, result: dict):
        """Handle test result."""
        if result['valid']:
            QMessageBox.information(
                self,
                "✅ Key hợp lệ",
                f"Kết nối: Thành công\n"
                f"Models khả dụng: {result['model_count']}\n"
                f"Thời gian phản hồi: {result['response_time_ms']}ms"
            )
        else:
            QMessageBox.warning(
                self,
                "❌ Key không hợp lệ",
                f"Lỗi: {result['error']}\n\n"
                "Vui lòng kiểm tra lại key hoặc tạo key mới."
            )
    
    def reset_api_key_errors(self, key_id: int):
        """Reset error count for a key."""
        db.reset_api_key_errors(key_id)
        self.load_api_keys()
        QMessageBox.information(self, "Thành công", "Đã reset số lỗi về 0")
    
    def save_model(self):
        """Save selected model."""
        model = self.model_combo.currentData()
        db.set_setting('default_model', model)
        claude_client.set_model(model)
    
    def save_thinking_setting(self):
        """Save extended thinking settings."""
        enabled = self.thinking_checkbox.isChecked()
        budget = self.budget_spin.value()

        db.set_setting('extended_thinking', 'true' if enabled else 'false')
        db.set_setting('thinking_budget', str(budget))

        claude_client.set_extended_thinking(enabled, budget)

    def save_tpd_credentials(self):
        """Save truyenphuongdong.com credentials to database."""
        username = self.tpd_username_input.text()
        password = self.tpd_password_input.text()

        db.set_setting('truyenphuongdong_username', username)
        db.set_setting('truyenphuongdong_password', password)

    def load_models(self):
        """Load models from API or fallback."""
        self.model_combo.clear()
        
        if claude_client.available_models:
            models = claude_client.available_models
        else:
            models = FALLBACK_MODELS
        
        for name, model_id in models:
            self.model_combo.addItem(name, model_id)
    
    def refresh_models(self):
        """Refresh models list from API."""
        current_model = self.model_combo.currentData()
        
        models = claude_client.fetch_available_models()
        
        if models:
            self.model_combo.clear()
            for name, model_id in models:
                self.model_combo.addItem(name, model_id)
            
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == current_model:
                    self.model_combo.setCurrentIndex(i)
                    break
            
            QMessageBox.information(self, "Thành công", f"Đã cập nhật {len(models)} models!")
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể lấy danh sách models.\nVui lòng kiểm tra API key và kết nối mạng.")
