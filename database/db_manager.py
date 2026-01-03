"""
AnhMin Audio - Database Manager
SQLite database for projects, chats, and memory
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import DATABASE_PATH


class DatabaseManager:
    """Manages SQLite database for the application."""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
        self._migrate_database()  # Run migrations for existing databases
        self.init_default_templates()
        self.init_default_categories()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _migrate_database(self):
        """Migrate database schema for existing databases."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if projects table needs migration
            cursor.execute("PRAGMA table_info(projects)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add model column if missing
            if 'model' not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN model TEXT DEFAULT NULL")
                print("Added 'model' column to projects table")

            # Add extended_thinking column if missing
            if 'extended_thinking' not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN extended_thinking INTEGER DEFAULT 1")
                print("Added 'extended_thinking' column to projects table")

    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    instructions TEXT DEFAULT '',
                    model TEXT DEFAULT NULL,
                    extended_thinking INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 0
                )
            """)
            
            # Project files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT DEFAULT 'txt',
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Chat sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    title TEXT DEFAULT 'Cuộc trò chuyện mới',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    attachments TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id, key)
                )
            """)
            
            # API Keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    error_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Usage tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    UNIQUE(date)
                )
            """)
            
            # Templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT '📝',
                    content TEXT NOT NULL,
                    is_global INTEGER DEFAULT 0,
                    is_default INTEGER DEFAULT 0,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Glossary categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS glossary_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT '📂',
                    is_global INTEGER DEFAULT 0,
                    sort_order INTEGER DEFAULT 0
                )
            """)
            
            # Glossary terms table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS glossary_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    original TEXT,
                    standard TEXT NOT NULL,
                    variants TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES glossary_categories(id) ON DELETE CASCADE
                )
            """)
    
    # ============== Projects ==============
    
    def create_project(self, name: str, instructions: str = "") -> int:
        """Create a new project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (name, instructions) VALUES (?, ?)",
                (name, instructions)
            )
            return cursor.lastrowid
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get a project by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM projects WHERE id = ?",
                (project_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        """Update project fields."""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.now().isoformat()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [project_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE projects SET {fields} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all related data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0
    
    def set_active_project(self, project_id: int):
        """Set a project as active (deactivate others)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE projects SET is_active = 0")
            cursor.execute(
                "UPDATE projects SET is_active = 1 WHERE id = ?",
                (project_id,)
            )
    
    # ============== Project Files ==============
    
    def add_project_file(self, project_id: int, filename: str, 
                         filepath: str, file_size: int, file_type: str) -> int:
        """Add a file to a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO project_files 
                   (project_id, filename, filepath, file_size, file_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (project_id, filename, filepath, file_size, file_type)
            )
            return cursor.lastrowid
    
    def get_project_files(self, project_id: int) -> List[Dict]:
        """Get all files for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM project_files WHERE project_id = ? ORDER BY uploaded_at DESC",
                (project_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_project_file(self, file_id: int) -> bool:
        """Delete a project file."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_files WHERE id = ?", (file_id,))
            return cursor.rowcount > 0
    
    # ============== Chat Sessions ==============
    
    def create_chat_session(self, project_id: int, title: str = "Cuộc trò chuyện mới") -> int:
        """Create a new chat session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (project_id, title) VALUES (?, ?)",
                (project_id, title)
            )
            return cursor.lastrowid
    
    def get_chat_sessions(self, project_id: int) -> List[Dict]:
        """Get all chat sessions for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM chat_sessions 
                   WHERE project_id = ? 
                   ORDER BY updated_at DESC""",
                (project_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_chat_session(self, session_id: int, **kwargs) -> bool:
        """Update chat session."""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.now().isoformat()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [session_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE chat_sessions SET {fields} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0
    
    def delete_chat_session(self, session_id: int) -> bool:
        """Delete a chat session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            return cursor.rowcount > 0
    
    # ============== Chat Messages ==============
    
    def add_message(self, session_id: int, role: str, content: str, 
                    attachments: List[str] = None) -> int:
        """Add a message to a chat session."""
        attachments = attachments or []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO chat_messages (session_id, role, content, attachments)
                   VALUES (?, ?, ?, ?)""",
                (session_id, role, content, json.dumps(attachments))
            )
            # Update session's updated_at
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,)
            )
            return cursor.lastrowid
    
    def get_messages(self, session_id: int) -> List[Dict]:
        """Get all messages for a chat session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            )
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg['attachments'] = json.loads(msg['attachments'])
                messages.append(msg)
            return messages
    
    # ============== Memory ==============
    
    def set_memory(self, project_id: int, key: str, value: str, 
                   category: str = "general") -> int:
        """Set or update a memory item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO project_memory (project_id, key, value, category)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(project_id, key) DO UPDATE SET 
                   value = excluded.value,
                   category = excluded.category,
                   updated_at = CURRENT_TIMESTAMP""",
                (project_id, key, value, category)
            )
            return cursor.lastrowid
    
    def get_memory(self, project_id: int) -> List[Dict]:
        """Get all memory items for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM project_memory 
                   WHERE project_id = ? 
                   ORDER BY category, key""",
                (project_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_memory WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0
    
    def clear_memory(self, project_id: int) -> bool:
        """Clear all memory for a project."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM project_memory WHERE project_id = ?",
                (project_id,)
            )
            return cursor.rowcount > 0
    
    # ============== API Keys ==============
    
    def add_api_key(self, name: str, api_key: str, priority: int = 0) -> int:
        """Add an API key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO api_keys (name, api_key, priority)
                   VALUES (?, ?, ?)""",
                (name, api_key, priority)
            )
            return cursor.lastrowid
    
    def get_api_keys(self) -> List[Dict]:
        """Get all API keys."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM api_keys ORDER BY priority DESC, id ASC"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_api_key(self) -> Optional[Dict]:
        """Get the highest priority active API key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM api_keys 
                   WHERE is_active = 1 AND error_count < 3
                   ORDER BY priority DESC, last_used ASC
                   LIMIT 1"""
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_api_key(self, key_id: int, **kwargs) -> bool:
        """Update API key fields."""
        if not kwargs:
            return False
        
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [key_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE api_keys SET {fields} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
            return cursor.rowcount > 0
    
    def mark_api_key_used(self, key_id: int):
        """Mark an API key as recently used."""
        self.update_api_key(key_id, last_used=datetime.now().isoformat())
    
    def increment_api_key_error(self, key_id: int):
        """Increment error count for an API key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET error_count = error_count + 1 WHERE id = ?",
                (key_id,)
            )
    
    def reset_api_key_errors(self, key_id: int):
        """Reset error count for an API key."""
        self.update_api_key(key_id, error_count=0)
    
    # ============== Settings ==============
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO settings (key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (key, value)
            )
    
    # ============== Usage Tracking ==============
    
    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add usage for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO usage_stats (date, input_tokens, output_tokens, request_count)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(date) DO UPDATE SET
                   input_tokens = usage_stats.input_tokens + excluded.input_tokens,
                   output_tokens = usage_stats.output_tokens + excluded.output_tokens,
                   request_count = usage_stats.request_count + 1""",
                (today, input_tokens, output_tokens)
            )
    
    def get_usage_today(self) -> Dict:
        """Get today's usage."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM usage_stats WHERE date = ?",
                (today,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {'input_tokens': 0, 'output_tokens': 0, 'request_count': 0}
    
    def get_usage_week(self) -> Dict:
        """Get this week's usage."""
        from datetime import timedelta
        today = datetime.now()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT SUM(input_tokens) as input_tokens, 
                          SUM(output_tokens) as output_tokens,
                          SUM(request_count) as request_count
                   FROM usage_stats WHERE date >= ?""",
                (week_start,)
            )
            row = cursor.fetchone()
            if row and row['input_tokens']:
                return {
                    'input_tokens': row['input_tokens'] or 0,
                    'output_tokens': row['output_tokens'] or 0,
                    'request_count': row['request_count'] or 0
                }
            return {'input_tokens': 0, 'output_tokens': 0, 'request_count': 0}
    
    def get_usage_month(self) -> Dict:
        """Get this month's usage."""
        month_start = datetime.now().strftime("%Y-%m-01")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT SUM(input_tokens) as input_tokens, 
                          SUM(output_tokens) as output_tokens,
                          SUM(request_count) as request_count
                   FROM usage_stats WHERE date >= ?""",
                (month_start,)
            )
            row = cursor.fetchone()
            if row and row['input_tokens']:
                return {
                    'input_tokens': row['input_tokens'] or 0,
                    'output_tokens': row['output_tokens'] or 0,
                    'request_count': row['request_count'] or 0
                }
            return {'input_tokens': 0, 'output_tokens': 0, 'request_count': 0}
    
    def get_api_status(self) -> Dict:
        """Get overall API status."""
        keys = self.get_api_keys()
        active_keys = [k for k in keys if k['is_active'] and k['error_count'] < 3]
        current_key = self.get_active_api_key()
        total_errors = sum(k['error_count'] for k in keys)
        
        return {
            'total_keys': len(keys),
            'active_keys': len(active_keys),
            'current_key_name': current_key['name'] if current_key else None,
            'current_key_id': current_key['id'] if current_key else None,
            'total_errors': total_errors,
            'status': 'ok' if active_keys else ('warning' if keys else 'none')
        }
    
    # ============== Templates ==============
    
    def get_templates(self, project_id: int = None) -> List[Dict]:
        """Get templates for a project (includes global templates)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute(
                    """SELECT * FROM templates 
                       WHERE project_id = ? OR is_global = 1
                       ORDER BY is_default DESC, sort_order ASC, name ASC""",
                    (project_id,)
                )
            else:
                cursor.execute(
                    """SELECT * FROM templates 
                       WHERE is_global = 1
                       ORDER BY is_default DESC, sort_order ASC, name ASC"""
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get a single template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_template(self, name: str, content: str, project_id: int = None,
                     icon: str = '📝', is_global: bool = False, is_default: bool = False) -> int:
        """Add a new template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO templates (project_id, name, icon, content, is_global, is_default)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, name, icon, content, int(is_global), int(is_default))
            )
            return cursor.lastrowid
    
    def update_template(self, template_id: int, **kwargs):
        """Update a template."""
        allowed = ['name', 'icon', 'content', 'is_global', 'sort_order']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return
        
        updates['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [template_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE templates SET {set_clause} WHERE id = ?", values)
    
    def delete_template(self, template_id: int):
        """Delete a template."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ? AND is_default = 0", (template_id,))
    
    def init_default_templates(self):
        """Initialize default templates if not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM templates WHERE is_default = 1")
            count = cursor.fetchone()[0]
            
            if count == 0:
                defaults = [
                    {
                        'name': 'Mặc định',
                        'icon': '📝',
                        'content': '''Bạn là chuyên gia biên tập audiobook tiểu thuyết tu tiên Việt Nam với hơn 10 năm kinh nghiệm.

## Nhiệm vụ:
Chỉnh sửa văn bản dịch thành văn nói tự nhiên, phù hợp cho audiobook.

## Yêu cầu:
1. Giảm 20-25% độ dài, giữ 75-80% nội dung quan trọng
2. Chuyển văn dịch sang văn nói tự nhiên tiếng Việt
3. Kết hợp câu ngắn, loại bỏ lặp từ
4. Giữ nguyên tên riêng, thuật ngữ tu tiên

## Thuật ngữ:
{{GLOSSARY}}'''
                    },
                    {
                        'name': 'Chương chiến đấu',
                        'icon': '⚔️',
                        'content': '''Bạn là chuyên gia biên tập audiobook tiểu thuyết tu tiên.

## Yêu cầu đặc biệt cho CHƯƠNG CHIẾN ĐẤU:
1. Giữ tiết tấu NHANH - không mô tả dài dòng
2. Chiêu thức: mô tả ngắn gọn, chỉ giữ tên + hiệu ứng chính
3. Cắt bớt: suy nghĩ nội tâm dài trong lúc đánh nhau
4. Giữ nguyên: tên chiêu thức, cảnh giới, vũ khí
5. Tăng cường: động từ mạnh (đánh, chém, phá, xé...)
6. Giảm 25-30% độ dài

## Thuật ngữ:
{{GLOSSARY}}'''
                    },
                    {
                        'name': 'Chương tu luyện',
                        'icon': '🧘',
                        'content': '''Bạn là chuyên gia biên tập audiobook tiểu thuyết tu tiên.

## Yêu cầu đặc biệt cho CHƯƠNG TU LUYỆN:
1. Giữ chi tiết về: cảnh giới, đột phá, công pháp
2. Giải thích rõ ràng các khái niệm tu luyện
3. Có thể giữ mô tả dài hơn về quá trình tu luyện
4. Giữ nguyên: tên công pháp, đan dược, linh thảo
5. Giảm 15-20% độ dài (ít hơn chương chiến đấu)

## Thuật ngữ:
{{GLOSSARY}}'''
                    }
                ]
                
                for i, t in enumerate(defaults):
                    cursor.execute(
                        """INSERT INTO templates (name, icon, content, is_global, is_default, sort_order)
                           VALUES (?, ?, ?, 1, 1, ?)""",
                        (t['name'], t['icon'], t['content'], i)
                    )
    
    # ============== Glossary Categories ==============
    
    def get_glossary_categories(self, project_id: int = None) -> List[Dict]:
        """Get glossary categories for a project (includes global)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute(
                    """SELECT * FROM glossary_categories 
                       WHERE project_id = ? OR is_global = 1
                       ORDER BY sort_order ASC, name ASC""",
                    (project_id,)
                )
            else:
                cursor.execute(
                    """SELECT * FROM glossary_categories 
                       WHERE is_global = 1
                       ORDER BY sort_order ASC, name ASC"""
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_glossary_category(self, name: str, project_id: int = None,
                              icon: str = '📂', is_global: bool = False) -> int:
        """Add a glossary category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO glossary_categories (project_id, name, icon, is_global)
                   VALUES (?, ?, ?, ?)""",
                (project_id, name, icon, int(is_global))
            )
            return cursor.lastrowid
    
    def update_glossary_category(self, category_id: int, **kwargs):
        """Update a glossary category."""
        allowed = ['name', 'icon', 'sort_order']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [category_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE glossary_categories SET {set_clause} WHERE id = ?", values)
    
    def delete_glossary_category(self, category_id: int):
        """Delete a glossary category and its terms."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM glossary_terms WHERE category_id = ?", (category_id,))
            cursor.execute("DELETE FROM glossary_categories WHERE id = ?", (category_id,))
    
    def init_default_categories(self):
        """Initialize default glossary categories if not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM glossary_categories WHERE is_global = 1")
            count = cursor.fetchone()[0]
            
            if count == 0:
                defaults = [
                    ('Cảnh giới', '⚔️'),
                    ('Nhân vật', '👤'),
                    ('Chiêu thức', '💥'),
                    ('Vật phẩm', '💎'),
                    ('Địa danh', '🏔️'),
                    ('Thế lực', '🏛️'),
                ]
                
                for i, (name, icon) in enumerate(defaults):
                    cursor.execute(
                        """INSERT INTO glossary_categories (name, icon, is_global, sort_order)
                           VALUES (?, ?, 1, ?)""",
                        (name, icon, i)
                    )
    
    # ============== Glossary Terms ==============
    
    def get_glossary_terms(self, category_id: int) -> List[Dict]:
        """Get all terms in a category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM glossary_terms 
                   WHERE category_id = ?
                   ORDER BY standard ASC""",
                (category_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_glossary_terms(self, project_id: int = None) -> List[Dict]:
        """Get all terms for a project (includes global)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if project_id:
                cursor.execute(
                    """SELECT t.*, c.name as category_name, c.icon as category_icon
                       FROM glossary_terms t
                       JOIN glossary_categories c ON t.category_id = c.id
                       WHERE c.project_id = ? OR c.is_global = 1
                       ORDER BY c.sort_order, t.standard""",
                    (project_id,)
                )
            else:
                cursor.execute(
                    """SELECT t.*, c.name as category_name, c.icon as category_icon
                       FROM glossary_terms t
                       JOIN glossary_categories c ON t.category_id = c.id
                       WHERE c.is_global = 1
                       ORDER BY c.sort_order, t.standard"""
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def add_glossary_term(self, category_id: int, standard: str,
                          original: str = None, variants: str = None, notes: str = None) -> int:
        """Add a glossary term."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO glossary_terms (category_id, original, standard, variants, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (category_id, original, standard, variants, notes)
            )
            return cursor.lastrowid
    
    def update_glossary_term(self, term_id: int, **kwargs):
        """Update a glossary term."""
        allowed = ['original', 'standard', 'variants', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return
        
        updates['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [term_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE glossary_terms SET {set_clause} WHERE id = ?", values)
    
    def delete_glossary_term(self, term_id: int):
        """Delete a glossary term."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM glossary_terms WHERE id = ?", (term_id,))
    
    def get_glossary_for_prompt(self, project_id: int = None) -> str:
        """Get formatted glossary for prompt insertion."""
        terms = self.get_all_glossary_terms(project_id)
        
        if not terms:
            return "(Chưa có thuật ngữ nào được định nghĩa)"
        
        # Group by category
        categories = {}
        for term in terms:
            cat_name = term['category_name']
            if cat_name not in categories:
                categories[cat_name] = []
            categories[cat_name].append(term)
        
        # Format output
        lines = []
        for cat_name, cat_terms in categories.items():
            lines.append(f"\n### {cat_name}:")
            for term in cat_terms:
                line = f"- {term['standard']}"
                if term['original']:
                    line += f" ({term['original']})"
                if term['notes']:
                    line += f" - {term['notes']}"
                lines.append(line)
        
        return '\n'.join(lines)


# Singleton instance
db = DatabaseManager()
