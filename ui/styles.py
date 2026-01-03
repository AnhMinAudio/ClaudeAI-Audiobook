"""
AnhMin Audio - UI Styles
Modern dark theme stylesheet for PyQt6
"""

# Color Palette
COLORS = {
    'bg_darkest': '#0f0f17',
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#1f2937',
    'bg_lighter': '#374151',
    
    'accent': '#f97316',  # Orange
    'accent_hover': '#ea580c',
    'accent_light': 'rgba(249, 115, 22, 0.2)',
    
    'text_primary': '#f3f4f6',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280',
    
    'border': '#374151',
    'border_light': '#4b5563',
    
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'danger': '#ef4444',  # Alias for error
    
    'user_message': '#f97316',
    'assistant_message': '#374151',
}

# Main Application Stylesheet
MAIN_STYLESHEET = f"""
/* ============= Global ============= */
QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLORS['bg_darkest']};
}}

/* ============= Scroll Bars ============= */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['bg_lighter']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['bg_lighter']};
    border-radius: 5px;
    min-width: 30px;
}}

/* ============= Buttons ============= */
QPushButton {{
    background-color: {COLORS['bg_lighter']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS['border_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_light']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}

QPushButton#primaryButton {{
    background-color: {COLORS['accent']};
    color: white;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#dangerButton {{
    background-color: {COLORS['error']};
    color: white;
}}

QPushButton#dangerButton:hover {{
    background-color: #dc2626;
}}

/* ============= Line Edit & Text Edit ============= */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 12px;
    selection-background-color: {COLORS['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent']};
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}

/* ============= Labels ============= */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

QLabel#subtitle {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}

QLabel#mutedText {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}

/* ============= List Widget ============= */
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    background-color: transparent;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 4px;
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['accent_light']};
    border: 1px solid rgba(249, 115, 22, 0.3);
}}

/* ============= Tab Widget ============= */
QTabWidget::pane {{
    border: none;
    background-color: {COLORS['bg_dark']};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 12px 20px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}

QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom-color: {COLORS['accent']};
}}

/* ============= Combo Box ============= */
QComboBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox:focus {{
    border-color: {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['accent']};
    outline: none;
}}

/* ============= Splitter ============= */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ============= Menu ============= */
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

/* ============= Tool Tip ============= */
QToolTip {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
}}

/* ============= Dialog ============= */
QDialog {{
    background-color: {COLORS['bg_dark']};
}}

/* ============= Group Box ============= */
QGroupBox {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {COLORS['text_primary']};
}}

/* ============= Check Box ============= */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['bg_light']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['border_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

/* ============= Progress Bar ============= */
QProgressBar {{
    background-color: {COLORS['bg_light']};
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 6px;
}}

/* ============= Spin Box ============= */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 10px;
}}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS['bg_lighter']};
    border: none;
    width: 20px;
}}

/* ============= Message Box ============= */
QMessageBox {{
    background-color: {COLORS['bg_dark']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}
"""

# Sidebar specific styles
SIDEBAR_STYLE = f"""
QWidget#sidebar {{
    background-color: {COLORS['bg_darkest']};
    border-right: 1px solid {COLORS['border']};
}}

QLabel#appTitle {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['accent']};
}}

QLabel#appSubtitle {{
    font-size: 11px;
    color: {COLORS['text_muted']};
}}

QPushButton#newProjectBtn {{
    background-color: {COLORS['accent']};
    color: white;
    font-weight: 600;
    padding: 10px 16px;
}}

QPushButton#newProjectBtn:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#projectItem {{
    background-color: transparent;
    text-align: left;
    padding: 10px 12px;
    border-radius: 8px;
}}

QPushButton#projectItem:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QPushButton#projectItemActive {{
    background-color: {COLORS['accent_light']};
    border: 1px solid rgba(249, 115, 22, 0.3);
    text-align: left;
    padding: 10px 12px;
    border-radius: 8px;
    color: {COLORS['accent']};
}}
"""

# Chat area styles
CHAT_STYLE = f"""
QWidget#chatArea {{
    background-color: {COLORS['bg_dark']};
}}

QWidget#userMessage {{
    background-color: {COLORS['user_message']};
    border-radius: 16px;
    padding: 12px 16px;
}}

QWidget#assistantMessage {{
    background-color: {COLORS['assistant_message']};
    border-radius: 16px;
    padding: 12px 16px;
}}

QWidget#inputArea {{
    background-color: {COLORS['bg_light']};
    border-radius: 12px;
}}

QPushButton#sendBtn {{
    background-color: {COLORS['accent']};
    border-radius: 8px;
    padding: 8px;
}}

QPushButton#sendBtn:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton#attachBtn {{
    background-color: transparent;
    border-radius: 8px;
    padding: 8px;
}}

QPushButton#attachBtn:hover {{
    background-color: {COLORS['bg_lighter']};
}}
"""

# Memory card styles
MEMORY_CARD_STYLE = f"""
QFrame#memoryCard {{
    background-color: {COLORS['bg_light']};
    border-radius: 12px;
    padding: 12px;
}}

QFrame#memoryCard:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QLabel#memoryKey {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 11px;
}}

QLabel#memoryValue {{
    color: {COLORS['text_primary']};
    font-size: 13px;
}}
"""

# File item styles  
FILE_ITEM_STYLE = f"""
QFrame#fileItem {{
    background-color: {COLORS['bg_light']};
    border-radius: 10px;
    padding: 10px;
}}

QFrame#fileItem:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QLabel#fileName {{
    font-weight: 500;
    color: {COLORS['text_primary']};
}}

QLabel#fileSize {{
    color: {COLORS['text_muted']};
    font-size: 11px;
}}

QPushButton#fileDeleteBtn {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    padding: 4px 8px;
}}

QPushButton#fileDeleteBtn:hover {{
    color: {COLORS['error']};
}}
"""

# Template button styles
TEMPLATE_BTN_STYLE = f"""
QPushButton#templateBtn {{
    background-color: {COLORS['bg_light']};
    border-radius: 10px;
    padding: 12px;
    text-align: left;
}}

QPushButton#templateBtn:hover {{
    background-color: {COLORS['bg_lighter']};
}}
"""

# Upload area styles
UPLOAD_AREA_STYLE = f"""
QFrame#uploadArea {{
    background-color: rgba(31, 41, 55, 0.5);
    border: 2px dashed {COLORS['border']};
    border-radius: 12px;
}}

QFrame#uploadArea:hover {{
    border-color: {COLORS['accent']};
}}
"""

def get_message_style(is_user: bool) -> str:
    """Get style for a chat message bubble."""
    bg_color = COLORS['user_message'] if is_user else COLORS['assistant_message']
    return f"""
        background-color: {bg_color};
        border-radius: 16px;
        padding: 12px 16px;
    """
