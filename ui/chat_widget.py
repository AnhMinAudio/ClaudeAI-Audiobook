"""
AnhMin Audio - Chat Widget
Chat interface with streaming support
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTextEdit, QFileDialog, QMenu,
    QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QTextCursor, QKeyEvent

from database import db
from api import claude_client, StreamWorker, file_handler
from api.memory_detector import auto_detect_and_add_memory
from ui.styles import COLORS


class MessageBubble(QFrame):
    """A single message bubble in the chat."""
    
    copy_requested = pyqtSignal(str)
    download_requested = pyqtSignal(str)
    
    def __init__(self, role: str, content: str, attachments: list = None):
        super().__init__()
        self.role = role
        self.content = content
        self.attachments = attachments or []
        self.setup_ui()
    
    def setup_ui(self):
        is_user = self.role == "user"
        
        # Container layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        
        if is_user:
            layout.addStretch()
        
        # Bubble container
        bubble = QFrame()
        bubble.setMaximumWidth(700)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        bubble_layout.setSpacing(8)
        
        if is_user:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['accent']};
                    border-radius: 18px;
                }}
            """)
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_lighter']};
                    border-radius: 18px;
                }}
            """)
        
        # Attachments
        if self.attachments:
            for att in self.attachments:
                att_label = QLabel(f"📎 {att.get('name', 'File')}")
                att_label.setStyleSheet(f"""
                    color: {'white' if is_user else COLORS['text_secondary']};
                    font-size: 11px;
                    padding: 4px 8px;
                    background-color: rgba(0,0,0,0.1);
                    border-radius: 4px;
                """)
                bubble_layout.addWidget(att_label)
        
        # Content
        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setStyleSheet(f"""
            color: {'white' if is_user else COLORS['text_primary']};
            font-size: 14px;
            line-height: 1.5;
        """)
        bubble_layout.addWidget(content_label)
        self.content_label = content_label
        
        # Action buttons for assistant messages
        if not is_user:
            actions = QHBoxLayout()
            actions.setSpacing(8)
            
            copy_btn = QPushButton("📋 Sao chép")
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_muted']};
                    font-size: 11px;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    color: {COLORS['text_primary']};
                }}
            """)
            copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.content))
            actions.addWidget(copy_btn)
            
            download_btn = QPushButton("📥 Tải xuống DOCX")
            download_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_muted']};
                    font-size: 11px;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    color: {COLORS['text_primary']};
                }}
            """)
            download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            download_btn.clicked.connect(lambda: self.download_requested.emit(self.content))
            actions.addWidget(download_btn)
            
            actions.addStretch()
            bubble_layout.addLayout(actions)
        
        layout.addWidget(bubble)
        
        if not is_user:
            layout.addStretch()
    
    def update_content(self, content: str):
        """Update message content (for streaming)."""
        self.content = content
        self.content_label.setText(content)


class ChatInput(QFrame):
    """Chat input area with attachment support."""
    
    message_sent = pyqtSignal(str, list)  # content, attachments
    
    def __init__(self):
        super().__init__()
        self.attachments = []
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Attachments area
        self.attachments_widget = QWidget()
        self.attachments_widget.setStyleSheet(f"padding: 8px; padding-bottom: 0;")
        self.attachments_layout = QHBoxLayout(self.attachments_widget)
        self.attachments_layout.setContentsMargins(8, 8, 8, 4)
        self.attachments_layout.setSpacing(8)
        self.attachments_widget.hide()
        layout.addWidget(self.attachments_widget)
        
        # Input row
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)
        
        # Attach button - rõ ràng hơn
        attach_btn = QPushButton("📎 Tải file")
        attach_btn.setMinimumWidth(80)
        attach_btn.setFixedHeight(36)
        attach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 13px;
                padding: 0 12px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
                border-color: {COLORS['accent']};
            }}
        """)
        attach_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        attach_btn.setToolTip("Đính kèm file (Ctrl+U)")
        attach_btn.clicked.connect(self.attach_file)
        input_layout.addWidget(attach_btn, 0, Qt.AlignmentFlag.AlignTop)
        
        # Text input - 5 dòng mặc định, tự giãn
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Nhập yêu cầu của bạn...")
        self.text_input.setMinimumHeight(100)  # ~5 dòng
        self.text_input.setMaximumHeight(200)  # Tối đa ~10 dòng
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: 14px;
                padding: 0;
                margin: 0;
            }}
        """)
        self.text_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_input.textChanged.connect(self.adjust_height)
        input_layout.addWidget(self.text_input, 1)
        
        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border-radius: 10px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
            }}
        """)
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.setToolTip("Gửi (Ctrl+Enter)")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(input_layout)
        
        # Install event filter for Ctrl+Enter
        self.text_input.installEventFilter(self)
    
    def adjust_height(self):
        """Tự động điều chỉnh chiều cao theo nội dung."""
        doc = self.text_input.document()
        doc_height = doc.size().height()
        new_height = min(max(100, int(doc_height) + 20), 200)
        self.text_input.setMinimumHeight(new_height)
    
    def eventFilter(self, obj, event):
        if obj == self.text_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def attach_file(self):
        """Open file dialog to attach files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn file đính kèm",
            "",
            "Text Files (*.txt);;Word Documents (*.docx);;All Files (*.*)"
        )
        
        for filepath in files:
            content, error = file_handler.read_file(filepath)
            if error:
                continue
            
            from pathlib import Path
            filename = Path(filepath).name
            self.attachments.append({
                'name': filename,
                'path': filepath,
                'content': content
            })
            
            # Add attachment chip
            chip = QFrame()
            chip.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['accent_light']};
                    border-radius: 12px;
                    padding: 4px 8px;
                }}
            """)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 8, 4)
            chip_layout.setSpacing(6)
            
            chip_label = QLabel(f"📄 {filename}")
            chip_label.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px;")
            chip_layout.addWidget(chip_label)
            
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['accent']};
                    font-size: 10px;
                    border: none;
                }}
            """)
            remove_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            remove_btn.clicked.connect(lambda checked, c=chip, f=filepath: self.remove_attachment(c, f))
            chip_layout.addWidget(remove_btn)
            
            self.attachments_layout.addWidget(chip)
        
        if self.attachments:
            self.attachments_widget.show()
    
    def remove_attachment(self, chip, filepath):
        """Remove an attachment."""
        chip.deleteLater()
        self.attachments = [a for a in self.attachments if a['path'] != filepath]
        if not self.attachments:
            self.attachments_widget.hide()
    
    def send_message(self):
        """Send the message."""
        text = self.text_input.toPlainText().strip()
        if not text and not self.attachments:
            return
        
        attachments = self.attachments.copy()
        self.message_sent.emit(text, attachments)
        
        # Clear input
        self.text_input.clear()
        self.attachments.clear()
        
        # Clear attachment chips
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.attachments_widget.hide()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable input."""
        self.text_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
    
    def set_text(self, text: str):
        """Set input text."""
        self.text_input.setPlainText(text)


class TemplateButton(QPushButton):
    """A template quick action button."""
    
    def __init__(self, name: str, description: str, prompt: str):
        super().__init__()
        self.prompt = prompt
        self.setup_ui(name, description)
    
    def setup_ui(self, name: str, description: str):
        self.setText(f"{name}\n{description}")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_light']};
                border-radius: 10px;
                padding: 12px;
                text-align: left;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_lighter']};
            }}
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(60)


class ChatWidget(QWidget):
    """Main chat widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.session_id = None
        self.stream_worker = None
        self.current_assistant_bubble = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Messages scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_dark']};
            }}
        """)
        
        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 16, 0, 16)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        scroll.setWidget(self.messages_widget)
        self.scroll_area = scroll
        layout.addWidget(scroll, 1)
        
        # Templates area (shown when no messages)
        self.templates_widget = QWidget()
        self.templates_widget.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        templates_layout = QVBoxLayout(self.templates_widget)
        templates_layout.setContentsMargins(40, 40, 40, 40)
        templates_layout.setSpacing(16)
        
        welcome = QLabel("👋 Xin chào! Bạn muốn làm gì hôm nay?")
        welcome.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        templates_layout.addWidget(welcome)
        
        templates_layout.addSpacing(20)
        
        # Template buttons grid
        templates_grid = QHBoxLayout()
        templates_grid.setSpacing(12)
        
        templates = db.get_templates(self.project_id)
        for tmpl in templates[:4]:
            # Build description from template content (first line or empty)
            content = tmpl.get('content', '')
            description = content.split('\n')[0][:50] + '...' if content else ''
            btn = TemplateButton(
                tmpl['name'],
                description,
                tmpl['content']
            )
            btn.clicked.connect(lambda checked, p=tmpl['content']: self.use_template(p))
            templates_grid.addWidget(btn)
        
        templates_layout.addLayout(templates_grid)
        templates_layout.addStretch()
        
        layout.addWidget(self.templates_widget)
        
        # Input area - full width
        input_container = QWidget()
        input_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_dark']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        
        self.chat_input = ChatInput()
        self.chat_input.message_sent.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        
        hint = QLabel("Nhấn Ctrl+Enter để gửi • Ctrl+U để đính kèm file")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.addWidget(hint)
        
        layout.addWidget(input_container)
    
    def set_project(self, project_id: int):
        """Set the current project and load chat history."""
        self.project_id = project_id
        self.clear_messages()
        
        # Get or create chat session
        sessions = db.get_chat_sessions(project_id)
        if sessions:
            self.session_id = sessions[0]['id']
            self.load_messages()
        else:
            self.session_id = db.create_chat_session(project_id)
        
        self.update_visibility()
    
    def load_messages(self):
        """Load messages from database."""
        if not self.session_id:
            return
        
        messages = db.get_messages(self.session_id)
        for msg in messages:
            self.add_message_bubble(msg['role'], msg['content'], msg['attachments'])
        
        self.update_visibility()
        self.scroll_to_bottom()
    
    def clear_messages(self):
        """Clear all message bubbles."""
        while self.messages_layout.count() > 1:  # Keep stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_message_bubble(self, role: str, content: str, attachments: list = None):
        """Add a message bubble to the chat."""
        bubble = MessageBubble(role, content, attachments)
        bubble.copy_requested.connect(self.copy_to_clipboard)
        bubble.download_requested.connect(self.download_as_docx)
        
        # Insert before stretch
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        
        return bubble
    
    def update_visibility(self):
        """Update visibility of templates vs messages."""
        has_messages = self.messages_layout.count() > 1
        self.scroll_area.setVisible(has_messages)
        self.templates_widget.setVisible(not has_messages)
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat."""
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    def use_template(self, prompt: str):
        """Use a template prompt."""
        self.chat_input.set_text(prompt)
        self.chat_input.text_input.setFocus()
    
    def send_message(self, content: str, attachments: list):
        """Send a message to Claude."""
        if not self.project_id or not self.session_id:
            return
        
        # Add user message
        att_info = [{'name': a['name'], 'type': 'text'} for a in attachments]
        db.add_message(self.session_id, 'user', content, att_info)
        self.add_message_bubble('user', content, att_info)
        self.update_visibility()
        self.scroll_to_bottom()
        
        # Disable input during generation
        self.chat_input.set_enabled(False)
        
        # Build messages for API
        all_messages = db.get_messages(self.session_id)
        api_messages = []
        
        for msg in all_messages:
            msg_content = msg['content']
            if msg['attachments']:
                # Add attachment content
                for att in attachments:
                    if att.get('content'):
                        msg_content = f"[File: {att['name']}]\n{att['content']}\n\n{msg_content}"
            
            api_messages.append({
                'role': msg['role'],
                'content': msg_content
            })
        
        # Get project info for system prompt
        project = db.get_project(self.project_id)
        memory = db.get_memory(self.project_id)
        system_prompt = claude_client.build_system_prompt(
            project.get('instructions', ''),
            memory
        )

        # Apply project-specific model and thinking settings
        project_model = project.get('model')
        if project_model:
            claude_client.set_model(project_model)

        extended_thinking = bool(project.get('extended_thinking', 1))
        claude_client.set_extended_thinking(extended_thinking, claude_client.thinking_budget)

        # Create streaming response
        self.current_assistant_bubble = self.add_message_bubble('assistant', '▌')
        self.scroll_to_bottom()

        # Start streaming worker
        self.stream_worker = StreamWorker(claude_client, api_messages, system_prompt)
        self.stream_worker.chunk_received.connect(self.on_stream_chunk)
        self.stream_worker.stream_finished.connect(self.on_stream_finished)
        self.stream_worker.error_occurred.connect(self.on_stream_error)
        self.stream_worker.start()
    
    def on_stream_chunk(self, chunk: str):
        """Handle streaming chunk."""
        if self.current_assistant_bubble:
            current = self.current_assistant_bubble.content.replace('▌', '')
            self.current_assistant_bubble.update_content(current + chunk + '▌')
            self.scroll_to_bottom()
    
    def on_stream_finished(self, full_response: str):
        """Handle stream completion."""
        if self.current_assistant_bubble:
            self.current_assistant_bubble.update_content(full_response)

        # Save to database
        db.add_message(self.session_id, 'assistant', full_response)

        # Auto-detect and add memory from response
        if self.project_id:
            auto_detect_and_add_memory(full_response, self.project_id)

        self.chat_input.set_enabled(True)
        self.current_assistant_bubble = None
        self.stream_worker = None
    
    def on_stream_error(self, error: str):
        """Handle streaming error."""
        if self.current_assistant_bubble:
            self.current_assistant_bubble.update_content(f"❌ Lỗi: {error}")
        
        self.chat_input.set_enabled(True)
        self.current_assistant_bubble = None
        self.stream_worker = None
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    
    def download_as_docx(self, content: str):
        """Download content as DOCX file."""
        project = db.get_project(self.project_id) if self.project_id else {}
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu file DOCX",
            f"{project.get('name', 'output')}.docx",
            "Word Document (*.docx)"
        )
        
        if filepath:
            result, error = file_handler.export_to_docx(
                content,
                project_name=project.get('name', ''),
                output_path=filepath
            )
            if error:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Lỗi", error)
    
    def new_chat(self):
        """Start a new chat session."""
        if self.project_id:
            self.session_id = db.create_chat_session(self.project_id)
            self.clear_messages()
            self.update_visibility()
