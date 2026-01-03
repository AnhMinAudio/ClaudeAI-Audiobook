"""
AnhMin Audio - Main Window
Main application window combining all components
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QSplitter, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QShortcut

from database import db
from api import claude_client
from ui.styles import MAIN_STYLESHEET, COLORS
from ui.sidebar import SidebarWidget
from ui.chat_widget import ChatWidget
from ui.instructions_widget import InstructionsWidget
from ui.files_widget import FilesWidget
from ui.memory_widget import MemoryWidget
from ui.batch_widget import BatchWidget
from ui.glossary_widget import GlossaryWidget
from ui.video_to_text_widget import VideoToTextWidget
from ui.link_to_text_widget import LinkToTextWidget
from ui.settings_dialog import SettingsDialog
from ui.update_dialog import UpdateDialog
from updater import UpdateChecker
from config import APP_NAME, APP_VERSION, DEFAULT_MODEL, GITHUB_OWNER, GITHUB_REPO


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_project_id = None
        self.update_info = None  # Store update info
        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.init_data()
        self.load_initial_project()
        self.check_for_updates_background()
    
    def setup_window(self):
        """Setup window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 850)
        
        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
    
    def setup_ui(self):
        """Setup the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.project_selected.connect(self.on_project_selected)
        self.sidebar.settings_clicked.connect(self.show_settings)
        self.sidebar.update_clicked.connect(self.check_for_updates_manual)
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Tab header with project name
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['bg_dark']}; border-bottom: 1px solid {COLORS['border']};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        
        self.project_name_label = QLabel("Chọn hoặc tạo dự án mới")
        self.project_name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(self.project_name_label)
        
        header_layout.addStretch()
        
        # New chat button
        new_chat_btn = QPushButton("💬 Chat mới")
        new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        new_chat_btn.clicked.connect(self.new_chat)
        header_layout.addWidget(new_chat_btn)
        
        content_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS['bg_dark']};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                padding: 14px 24px;
                border-bottom: 2px solid transparent;
                font-weight: 500;
                font-size: 13px;
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_primary']};
            }}
            QTabBar::tab:selected {{
                color: {COLORS['accent']};
                border-bottom-color: {COLORS['accent']};
            }}
        """)
        
        # Chat tab
        self.chat_widget = ChatWidget()
        self.tabs.addTab(self.chat_widget, "💬 Chat")
        
        # Instructions tab
        self.instructions_widget = InstructionsWidget()
        self.instructions_widget.instructions_saved.connect(self.on_instructions_saved)
        self.tabs.addTab(self.instructions_widget, "📝 Instruction")
        
        # Files tab
        self.files_widget = FilesWidget()
        self.tabs.addTab(self.files_widget, "📁 Files")
        
        # Memory tab
        self.memory_widget = MemoryWidget()
        self.tabs.addTab(self.memory_widget, "🧠 Memory")
        
        # Batch tab
        self.batch_widget = BatchWidget()
        self.tabs.addTab(self.batch_widget, "📦 Batch")
        
        # Glossary tab
        self.glossary_widget = GlossaryWidget()
        self.tabs.addTab(self.glossary_widget, "📚 Thuật ngữ")
        
        # Video to Text tab
        self.video_to_text_widget = VideoToTextWidget()
        self.tabs.addTab(self.video_to_text_widget, "🎬 Video to Text")
        
        # Link to Text tab
        self.link_to_text_widget = LinkToTextWidget()
        self.tabs.addTab(self.link_to_text_widget, "🔗 Link to Text")
        
        content_layout.addWidget(self.tabs)
        
        main_layout.addWidget(content, 1)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+N: New project
        QShortcut(QKeySequence("Ctrl+N"), self, self.sidebar.create_new_project)
        
        # Ctrl+Enter: Send message (handled in chat widget)
        
        # Ctrl+U: Upload file
        QShortcut(QKeySequence("Ctrl+U"), self, self.upload_file_shortcut)
        
        # Ctrl+1,2,3,4,5,6,7,8: Switch tabs
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.tabs.setCurrentIndex(2))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.tabs.setCurrentIndex(3))
        QShortcut(QKeySequence("Ctrl+5"), self, lambda: self.tabs.setCurrentIndex(4))
        QShortcut(QKeySequence("Ctrl+6"), self, lambda: self.tabs.setCurrentIndex(5))
        QShortcut(QKeySequence("Ctrl+7"), self, lambda: self.tabs.setCurrentIndex(6))
        QShortcut(QKeySequence("Ctrl+8"), self, lambda: self.tabs.setCurrentIndex(7))
    
    def init_data(self):
        """Initialize default data."""
        # Initialize templates
        db.init_default_templates()
        
        # Set default model
        saved_model = db.get_setting('default_model', DEFAULT_MODEL)
        claude_client.set_model(saved_model)
        
        # Load extended thinking settings
        thinking_enabled = db.get_setting('extended_thinking', 'true') == 'true'
        thinking_budget = int(db.get_setting('thinking_budget', '10000'))
        claude_client.set_extended_thinking(thinking_enabled, thinking_budget)
        
        # Fetch available models from API (in background)
        self.fetch_models_async()
    
    def fetch_models_async(self):
        """Fetch models from API without blocking UI."""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class ModelFetcher(QThread):
            finished = pyqtSignal(list)
            
            def run(self):
                models = claude_client.fetch_available_models()
                self.finished.emit(models)
        
        self.model_fetcher = ModelFetcher()
        self.model_fetcher.finished.connect(self.on_models_fetched)
        self.model_fetcher.start()
    
    def on_models_fetched(self, models):
        """Handle models fetched from API."""
        if models:
            print(f"Loaded {len(models)} models from API")
        else:
            print("Using fallback models list")
    
    def load_initial_project(self):
        """Load the last active project or create one."""
        projects = db.get_all_projects()
        
        if not projects:
            # Create a default project
            from config import DEFAULT_INSTRUCTIONS
            project_id = db.create_project("Dự án mẫu", DEFAULT_INSTRUCTIONS)
            db.set_active_project(project_id)
            self.sidebar.load_projects()
            self.on_project_selected(project_id)
        else:
            # Find active project
            active = next((p for p in projects if p['is_active']), projects[0])
            self.on_project_selected(active['id'])
    
    def on_project_selected(self, project_id: int):
        """Handle project selection."""
        self.current_project_id = project_id
        project = db.get_project(project_id)
        
        if project:
            self.project_name_label.setText(f"📁 {project['name']}")
            
            # Update all widgets
            self.chat_widget.set_project(project_id)
            self.instructions_widget.set_project(project_id)
            self.files_widget.set_project(project_id)
            self.memory_widget.set_project(project_id)
            self.batch_widget.set_project(project_id)
            self.glossary_widget.set_project(project_id)
            self.video_to_text_widget.set_project(project_id)
            self.link_to_text_widget.set_project(project_id)
    
    def on_instructions_saved(self):
        """Handle instructions saved."""
        # Could refresh chat or show notification
        pass
    
    def new_chat(self):
        """Start a new chat session."""
        if self.current_project_id:
            self.chat_widget.new_chat()
            self.tabs.setCurrentIndex(0)
    
    def upload_file_shortcut(self):
        """Handle upload file shortcut."""
        if self.tabs.currentIndex() == 0:
            # In chat tab, trigger attachment
            self.chat_widget.chat_input.attach_file()
        elif self.tabs.currentIndex() == 2:
            # In files tab, trigger upload
            from PyQt6.QtWidgets import QFileDialog
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Chọn file",
                "",
                "Text Files (*.txt);;Word Documents (*.docx);;All Files (*.*)"
            )
            if files:
                self.files_widget.add_files(files)
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def check_for_updates_background(self):
        """Check for updates in background thread."""
        from PyQt6.QtCore import QThread, pyqtSignal

        class UpdateCheckWorker(QThread):
            finished = pyqtSignal(object)  # update_info or None

            def run(self):
                checker = UpdateChecker(GITHUB_OWNER, GITHUB_REPO, APP_VERSION)
                update_info = checker.check_for_updates()
                self.finished.emit(update_info)

        self.update_check_worker = UpdateCheckWorker()
        self.update_check_worker.finished.connect(self.on_update_check_finished)
        self.update_check_worker.start()

    def on_update_check_finished(self, update_info):
        """Handle update check completion."""
        if update_info:
            self.update_info = update_info
            self.sidebar.show_update_badge(True)
            print(f"Update available: v{update_info['version']}")
        else:
            self.sidebar.show_update_badge(False)

    def check_for_updates_manual(self):
        """Manually check for updates (when user clicks button)."""
        if self.update_info:
            # Show update dialog with cached info
            self.show_update_dialog()
        else:
            # Check again
            from PyQt6.QtCore import QThread, pyqtSignal

            class UpdateCheckWorker(QThread):
                finished = pyqtSignal(object)

                def run(self):
                    checker = UpdateChecker(GITHUB_OWNER, GITHUB_REPO, APP_VERSION)
                    update_info = checker.check_for_updates()
                    self.finished.emit(update_info)

            self.manual_check_worker = UpdateCheckWorker()
            self.manual_check_worker.finished.connect(self.on_manual_check_finished)
            self.manual_check_worker.start()

    def on_manual_check_finished(self, update_info):
        """Handle manual update check completion."""
        if update_info:
            self.update_info = update_info
            self.sidebar.show_update_badge(True)
            self.show_update_dialog()
        else:
            QMessageBox.information(
                self,
                "Không có cập nhật",
                f"Bạn đang sử dụng phiên bản mới nhất (v{APP_VERSION})."
            )

    def show_update_dialog(self):
        """Show update dialog."""
        if not self.update_info:
            return

        dialog = UpdateDialog(self.update_info, self)
        dialog.exec()

        # Clear badge if user dismissed dialog
        self.sidebar.show_update_badge(False)

    def closeEvent(self, event):
        """Handle window close."""
        # Could save state, cleanup, etc.
        event.accept()
