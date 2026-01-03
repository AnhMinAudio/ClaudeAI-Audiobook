"""
AnhMin Audio - Configuration
"""

import os
import sys
from pathlib import Path

# App Info
APP_NAME = "AnhMin Audio"
APP_VERSION = "1.0.0"
APP_AUTHOR = "PhamDung"

# GitHub Update Configuration
# TODO: Replace with your actual GitHub username and repo name after creating repository
GITHUB_OWNER = "AnhMinAudio"  # Change this to your GitHub username
GITHUB_REPO = "ClaudeAI-Audiobook"  # Change this to your repository name
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Paths
if getattr(sys, 'frozen', False):
    # Running as compiled
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent

DATA_DIR = Path.home() / ".anhmin_audio"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "database.db"
PROJECTS_DIR = DATA_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# Claude API Settings
DEFAULT_MODEL = "claude-opus-4-5-20250514"

# Fallback models (used when API fetch fails)
FALLBACK_MODELS = [
    ("Claude Opus 4.5", "claude-opus-4-5-20250514"),
    ("Claude Opus 4", "claude-opus-4-20250514"),
    ("Claude Sonnet 4.5", "claude-sonnet-4-5-20250929"),
    ("Claude Sonnet 4", "claude-sonnet-4-20250514"),
    ("Claude Haiku 4.5", "claude-haiku-4-5-20251001"),
]

MAX_TOKENS = 8192
TEMPERATURE = 0.7

# UI Settings
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700

# Template prompts
DEFAULT_TEMPLATES = [
    {
        "name": "📖 Viết lại chương",
        "description": "Chuyển đổi văn phong sang kể chuyện",
        "prompt": """Hãy viết lại nội dung chương sau theo phong cách kể chuyện audiobook tiếng Việt:
- Giữ nguyên cốt truyện và các chi tiết quan trọng
- Chuyển sang văn phong kể chuyện tự nhiên, hấp dẫn
- Sử dụng từ ngữ phù hợp với văn hóa Việt Nam
- Thêm các câu chuyển đoạn mượt mà
- Tạo suspense và cliffhanger khi phù hợp

Nội dung chương gốc:
{content}"""
    },
    {
        "name": "✍️ Tạo mô tả video",
        "description": "Viết title và description YouTube",
        "prompt": """Dựa trên nội dung tập audiobook sau, hãy viết:
1. TIÊU ĐỀ VIDEO (hấp dẫn, có keyword, dưới 100 ký tự)
2. MÔ TẢ VIDEO (300-500 từ, có timestamp, hashtag)

Nội dung tập:
{content}"""
    },
    {
        "name": "🎬 Đoạn mở đầu",
        "description": "Viết intro hấp dẫn cho tập mới",
        "prompt": """Viết đoạn mở đầu hấp dẫn cho tập audiobook mới với:
- Lời chào khán giả
- Tóm tắt ngắn tập trước
- Giới thiệu nội dung tập này
- Tạo sự hứng thú cho người nghe

Thông tin tập:
- Tên series: {series_name}
- Số tập: {episode_number}
- Nội dung chính: {content}"""
    },
    {
        "name": "📝 Tóm tắt nội dung", 
        "description": "Tóm tắt chương để review",
        "prompt": """Tóm tắt nội dung chương sau thành 3-5 điểm chính:
- Các sự kiện quan trọng
- Nhân vật xuất hiện
- Diễn biến cốt truyện
- Các chi tiết cần nhớ cho các tập sau

Nội dung:
{content}"""
    },
    {
        "name": "🔄 Chỉnh sửa văn phong",
        "description": "Điều chỉnh giọng văn theo yêu cầu",
        "prompt": """Chỉnh sửa đoạn văn sau theo yêu cầu:
- Giữ nguyên ý nghĩa
- Làm cho câu văn mượt mà hơn
- Sửa lỗi ngữ pháp nếu có
- Đảm bảo phù hợp với phong cách kể chuyện

Đoạn văn cần chỉnh sửa:
{content}"""
    }
]

# Default Instructions Template
DEFAULT_INSTRUCTIONS = """Bạn là trợ lý chuyên sản xuất audiobook tiên hiệp tiếng Việt cho kênh AnhMin Audio.

PHONG CÁCH VIẾT:
- Viết theo phong cách kể chuyện tự nhiên, hấp dẫn
- Sử dụng từ ngữ phù hợp với văn hóa Việt Nam
- Tạo sự hấp dẫn, có twist và cliffhanger
- Giữ giọng văn nhất quán với các tập trước

QUY TẮC:
- Giữ nguyên tên nhân vật đã được Việt hóa
- Không bỏ sót chi tiết quan trọng của cốt truyện
- Thêm các câu chuyển đoạn mượt mà
- Đoạn văn không quá dài, phù hợp để đọc thành tiếng
"""
