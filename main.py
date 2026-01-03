#!/usr/bin/env python3
"""
AnhMin Audio - Claude AI Project Manager
Main entry point

Author: PhamDung
Version: 1.0.0
"""

import sys
import os

# CRITICAL FIX: Redirect stdout/stderr to null when running as frozen windowed app
# This prevents crashes from print() statements throughout the entire app
if getattr(sys, 'frozen', False) and sys.stdout is None:
    if os.name == 'nt':  # Windows
        sys.stdout = open('nul', 'w', encoding='utf-8')
        sys.stderr = open('nul', 'w', encoding='utf-8')
    else:  # Unix-like
        sys.stdout = open('/dev/null', 'w', encoding='utf-8')
        sys.stderr = open('/dev/null', 'w', encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

from ui import MainWindow
from config import APP_NAME


def setup_high_dpi():
    """Setup high DPI scaling."""
    # Enable high DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def setup_app_style(app: QApplication):
    """Setup application-wide styling."""
    # Set application font
    font = QFont("Segoe UI", 10)
    if sys.platform == "darwin":
        font = QFont("SF Pro Display", 11)
    app.setFont(font)
    
    # Set dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(26, 26, 46))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(243, 244, 246))
    palette.setColor(QPalette.ColorRole.Base, QColor(31, 41, 55))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(22, 33, 62))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(31, 41, 55))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(243, 244, 246))
    palette.setColor(QPalette.ColorRole.Text, QColor(243, 244, 246))
    palette.setColor(QPalette.ColorRole.Button, QColor(55, 65, 81))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(243, 244, 246))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(249, 115, 22))
    palette.setColor(QPalette.ColorRole.Link, QColor(249, 115, 22))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(249, 115, 22))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in development mode
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def main():
    """Main entry point."""
    # Setup high DPI before creating QApplication
    setup_high_dpi()

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("AnhMin Audio")

    # Set application icon (works in both dev and built mode)
    icon_path = get_resource_path('app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Setup styling
    setup_app_style(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
