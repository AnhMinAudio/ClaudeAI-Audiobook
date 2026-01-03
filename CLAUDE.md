# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnhMin Audio is a PyQt6 desktop application for managing audiobook production projects with Claude AI integration. The application is specifically designed for Vietnamese audiobook production, particularly cultivation novels (tiên hiệp).

**Tech Stack:**
- PyQt6 for GUI
- Anthropic API for Claude AI integration
- SQLite for data persistence
- python-docx for document handling
- BeautifulSoup/Selenium for web scraping
- Optional: undetected-chromedriver for anti-bot bypass
- Optional: faster-whisper/mlx-whisper for video transcription

## Development Setup

### Installation

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

### Data Storage

Application data is stored in:
- **Windows:** `C:\Users\<username>\.anhmin_audio\`
- **macOS:** `/Users/<username>/.anhmin_audio/`

Contains:
- `database.db` - SQLite database
- `projects/` - Project file storage

## Architecture

### Module Structure

```
api/
├── claude_client.py   # Claude API client with auto-rotation & streaming
├── file_handler.py    # File upload/processing (TXT, DOCX)
└── memory_detector.py # Auto memory detection from content

database/
└── db_manager.py      # SQLite operations (projects, chats, memory, API keys)

ui/
├── main_window.py     # Main window with tab management
├── sidebar.py         # Project list and navigation
├── chat_widget.py     # Chat interface with streaming
├── instructions_widget.py  # Project instructions editor
├── files_widget.py    # File management
├── memory_widget.py   # Project memory (characters, places, etc.)
├── batch_widget.py    # Batch API processing
├── glossary_widget.py # Terminology management
├── video_to_text_widget.py  # Video transcription
├── link_to_text_widget.py   # Web content extraction
├── settings_dialog.py # API key and settings management
├── update_dialog.py   # Update download and installation UI
└── styles.py          # Application styling

updater/
├── __init__.py        # Package exports
├── update_checker.py  # GitHub Releases API integration
└── updater.py         # Download and install with UAC elevation

config.py              # Application configuration
main.py                # Entry point
build.py               # PyInstaller build script
```

### Key Components

#### Claude API Client ([api/claude_client.py](api/claude_client.py))

- **Auto-rotation**: Automatically switches API keys when hitting rate limits or errors
- **Extended thinking**: Supports extended thinking mode for compatible models (Opus 4/4.5, Sonnet 4/4.5)
- **Streaming**: Real-time streaming responses with `StreamWorker` thread
- **Batch API**: Create and manage batch requests for bulk processing
- **Model selection**: Fetches available models from Anthropic API

Key methods:
- `stream_message()` - Stream responses
- `send_message()` - Non-streaming responses
- `create_batch()` / `get_batch_results()` - Batch processing
- `test_api_key()` - Validate API keys

#### Database Manager ([database/db_manager.py](database/db_manager.py))

Singleton instance (`db`) manages all SQLite operations using context managers for safe transactions.

**Tables:**
- `projects` - Project metadata and instructions
- `project_files` - Uploaded files (TXT, DOCX)
- `chat_sessions` - Chat conversation sessions
- `chat_messages` - Individual messages with attachments
- `project_memory` - Key-value memory system
- `api_keys` - API key management with priority and error tracking
- `settings` - Application settings
- `usage_stats` - Token usage tracking
- `templates` - Prompt templates (global and project-specific)
- `glossary_categories` - Terminology categories
- `glossary_terms` - Standardized terminology

#### Main Window ([ui/main_window.py](ui/main_window.py))

Orchestrates all UI components:
- Tab-based interface for different features
- Keyboard shortcuts (Ctrl+1-8 for tabs, Ctrl+N for new project, Ctrl+Enter for send)
- Project switching updates all child widgets via `set_project(project_id)`

#### Settings Dialog ([ui/settings_dialog.py](ui/settings_dialog.py))

Manages application configuration:
- **Model Selection**: Choose default Claude model
- **Extended Thinking**: Enable/disable and set thinking budget
- **Truyện Phương Đông Login**: Store credentials for auto-login
  - Username/email input field
  - Password input field with show/hide toggle
  - Auto-saves to `settings` table on text change
- **API Keys Management**: Add, edit, delete, and test API keys
- **Usage Statistics**: Token usage tracking and display

Credentials are stored using:
```python
db.set_setting('truyenphuongdong_username', username)
db.set_setting('truyenphuongdong_password', password)
```

### Important Patterns

#### Singleton Pattern

Both `claude_client` and `db` are singleton instances:

```python
from api import claude_client
from database import db
```

#### Signal-Slot Communication

PyQt6 signals connect UI components:

```python
# Example from main_window.py
self.sidebar.project_selected.connect(self.on_project_selected)
self.instructions_widget.instructions_saved.connect(self.on_instructions_saved)
```

#### Project Context

All widgets are project-aware and update when a new project is selected:

```python
def set_project(self, project_id: int):
    self.current_project_id = project_id
    # Load project-specific data
```

#### API Key Rotation

The Claude client automatically rotates through available API keys on rate limit or auth errors. Keys with error_count >= 3 are skipped. Priority determines rotation order.

## Configuration

### Models ([config.py](config.py))

Default model: `claude-opus-4-5-20250514`

Extended thinking is enabled by default for supported models. When enabled:
- Temperature is forced to 1.0
- Thinking budget defaults to 10,000 tokens
- Thinking blocks are filtered from streaming output (user only sees final response)

### Templates

Templates support `{{GLOSSARY}}` placeholder which is replaced with formatted glossary terms using `db.get_glossary_for_prompt(project_id)`.

### Styling

Dark theme defined in [ui/styles.py](ui/styles.py) with centralized color palette in `COLORS` dictionary.

## Important Behaviors

### API Key Management

- Keys are stored in SQLite with priority ordering
- `get_active_api_key()` returns highest priority key with error_count < 3
- On error, `increment_api_key_error()` is called; key is disabled after 3 errors
- On success, `reset_api_key_errors()` resets the counter
- `mark_api_key_used()` updates last_used timestamp

### Message Attachments

Chat messages support file attachments. When building messages for the API:
- Attachments are formatted as content blocks: `[File: {name}]\n{content}`
- The user's message text follows the attachment blocks

### Database Transactions

Always use the context manager pattern:

```python
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Perform operations
    # Auto-commits on success, rolls back on exception
```

### Extended Thinking

When extended thinking is enabled and model supports it:
1. Streaming emits "[🧠 Đang suy nghĩ...]\n" when thinking block starts
2. Thinking content is not streamed to user
3. Only text blocks are streamed to output

## Common Tasks

### Adding a New Tab/Widget

1. Create widget class in `ui/` extending appropriate PyQt6 base class
2. Implement `set_project(project_id)` method
3. Add to `main_window.py`:
   - Import the widget
   - Create instance in `setup_ui()`
   - Add to tabs with `self.tabs.addTab()`
   - Call `set_project()` in `on_project_selected()`

### Adding Database Tables

1. Add CREATE TABLE statement in `db_manager.py` `init_database()`
2. Add CRUD methods following existing pattern
3. Use proper FOREIGN KEY constraints with ON DELETE CASCADE
4. Use context manager for all database operations

### Working with Glossary in Prompts

Templates can include `{{GLOSSARY}}` placeholder. Before sending to API:

```python
glossary_text = db.get_glossary_for_prompt(project_id)
prompt = template['content'].replace('{{GLOSSARY}}', glossary_text)
```

Format returned:
```
### Category Name:
- Standard Term (Original Term) - Notes
- Another Term - Notes
```

## Platform-Specific Notes

### Video Transcription

Video to Text feature requires platform-specific setup:

**Windows (NVIDIA GPU):**
```bash
pip install faster-whisper yt-dlp
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
winget install ffmpeg
```

**macOS (Apple Silicon):**
```bash
pip install mlx-whisper yt-dlp
brew install ffmpeg
```

**macOS (Intel) / Linux:**
```bash
pip install faster-whisper yt-dlp
# Install ffmpeg via system package manager
```

#### Timestamp & SRT Export

**Location:** [ui/video_to_text_widget.py](ui/video_to_text_widget.py)

The Video to Text widget supports timestamp handling and SRT subtitle export:

**Checkbox: "Giữ timestamp"**
- Default: **unchecked** (timestamps removed from raw text)
- When **checked**: Timestamps kept in format `[MM:SS]` and SRT export button appears
- Logic: `keep_timestamps` parameter passed to WhisperWorker

**SRT Export:**
- Only available when "Giữ timestamp" is checked
- Stores segments data with start/end times: `self.segments_data`
- Format: Standard SubRip (.srt) with `HH:MM:SS,mmm` timestamps
- Implementation: `save_srt_file()` at lines 1556-1596

```python
# SRT format output:
1
00:00:00,000 --> 00:00:05,500
First subtitle text

2
00:00:05,500 --> 00:00:10,250
Second subtitle text
```

**Data Flow:**
1. WhisperWorker emits: `finished.emit(text, segments_data)`
2. Main widget stores: `self.segments_data = segments_data`
3. SRT button enabled if checkbox checked AND segments exist
4. Export uses `format_srt_time()` for proper timestamp format

#### Smooth Progress Bar

**Location:** [ui/video_to_text_widget.py](ui/video_to_text_widget.py:289-377)

Progress bar uses **smooth simulation** to avoid appearing frozen during transcription:

**Implementation:**
- Progress stages: 0-10% (preprocess) → 10-20% (load model) → **30-85% (smooth simulation)** → 85-90% (transcribe done) → 90-100% (process segments)
- Simulation runs in background thread while `model.transcribe()` blocks
- Progress increases gradually with decreasing speed (faster at start, slower near end)
- Stops immediately when transcription completes

```python
# Smooth simulation thread
def simulate_progress():
    current = 30
    target = 85
    step = 1
    delay = 0.8  # seconds

    while current < target and not self._stop_progress_simulation:
        time.sleep(delay)
        current += step

        # Slow down approaching target
        if current > 70:
            delay = 1.5
            step = 0.5
        elif current > 60:
            delay = 1.2
```

**Why This Approach:**
- `model.transcribe()` is blocking with no progress callbacks
- Users need visual feedback that app is working
- Smooth animation prevents "frozen" perception
- Common pattern (YouTube, browsers use similar technique)

### Fonts

Application uses platform-specific fonts:
- Windows: Segoe UI
- macOS: SF Pro Display

### Web Scraping with Auto-Login

**Link to Text Widget** ([ui/link_to_text_widget.py](ui/link_to_text_widget.py)) supports automatic login for protected websites.

#### Supported Websites

**Location:** [ui/link_to_text_widget.py](ui/link_to_text_widget.py:140-157)

Only 2 websites are currently supported and tested:

1. **truyenphuongdong.com** - Truyện Phương Đông (Vietnamese)
   - Type: SPA (Single Page App) - Requires Selenium
   - Auth: Login required (configured in Settings)
   - Features: Auto-login, Swiper.js navigation, menu-based chapter selection

2. **piaotia.com** - 飘天文学 (Chinese)
   - Type: Static HTML
   - Auth: None required
   - Encoding: GBK
   - Features: Direct scraping with BeautifulSoup

**Important:** Other websites (truyenfull.vn, tangthuvien.vn, etc.) have been removed as they were not tested/validated.

```python
SUPPORTED_WEBSITES = {
    "truyenphuongdong.com": {
        "name": "Truyện Phương Đông",
        "type": "spa",
        ...
    },
    "piaotia.com": {
        "name": "飘天文学",
        "type": "static",
        "encoding": "gbk",
        ...
    },
}
```

#### truyenphuongdong.com Integration

This website requires authentication and uses anti-bot protection. The scraper handles this automatically:

**Setup:**
1. Install optional dependency: `pip install undetected-chromedriver`
2. Configure credentials in Settings → 🔐 Truyện Phương Đông Login
   - Username/email field
   - Password field (stored in `settings` table)

**Technical Details:**
- Uses `undetected-chromedriver` to bypass Cloudflare/reCAPTCHA
- Falls back to regular Selenium if undetected-chromedriver not available
- Login form uses `name="email"` (NOT `name="username"`)
- Story metadata is embedded as escaped JSON in Next.js `<script>` tags
- Pattern: `\\"book\\":\{...\\"title\\":\\"...\\",\\"chapterNumber\\":1641\}`

**Workflow:**
1. Navigate to `/login` page
2. Fill `name="email"` and `name="password"` fields
3. Submit and wait for redirect (success = URL changes from `/login`)
4. Navigate to story page
5. Extract JSON metadata from page source
6. Parse title and chapter count

**Credentials Storage:**
```python
# In settings_dialog.py
db.set_setting('truyenphuongdong_username', username)
db.set_setting('truyenphuongdong_password', password)

# In link_to_text_widget.py
username = db.get_setting('truyenphuongdong_username', '')
password = db.get_setting('truyenphuongdong_password', '')
```

**Error Handling:**
- Missing credentials → "Cần cấu hình tài khoản đăng nhập trong Settings"
- Login failure → Saves debug HTML to `truyenphuongdong_login_failed.html`
- Parse failure → Saves debug HTML to `truyenphuongdong_logged_in_debug.html`

**UI Display:**
Story info is displayed with emoji labels:
- 🌐 Website: domain name
- 📖 Tên truyện: story title
- 📚 Tổng chương: total chapters

#### Chapter Navigation - Critical Implementation Details

**Website Architecture:**
- ALL chapters share the SAME URL: `https://truyenphuongdong.com/read/story-slug`
- Uses Swiper.js with virtual slides for chapter content
- Virtual slides only render on **user interaction**, not programmatic API calls

**Why Programmatic Navigation Fails:**
```javascript
// ❌ DOES NOT WORK - Virtual slides don't render
swiper.slideNext();
swiper.slideTo(chapterIndex);
swiper.update();
```

Even with `swiper.update()`, `swiper.updateSlides()`, or waiting for title changes, virtual slides remain unrendered. The content stays the same because Swiper only triggers rendering on actual user clicks/swipes.

**Solution: Menu-Based Navigation**

Menu navigation is the ONLY reliable method. For each chapter:

1. **Open menu** - Click button with `aria-label="menu"`
2. **Find chapter element** - Use JavaScript with exact matching
3. **Scroll menu if needed** - Ensure chapter is visible
4. **Click chapter** - Navigate to content
5. **Close menu** - Click backdrop to dismiss

**XPATH Selector Pitfall:**

```python
# ❌ WRONG - Matches parent containers containing the text
chapter_elem = driver.find_element(By.XPATH, f"//*[contains(., 'Chương 12:')]")
# This matches ANY element with "Chương 12:" in textContent, including:
# - Parent <div> containing all chapters
# - Page headers
# - Navigation breadcrumbs
# Result: Clicks wrong element, stays on current chapter

# ❌ ALSO WRONG - Fails if text is in child elements
chapter_elem = driver.find_element(By.XPATH, f"//*[contains(text(), 'Chương 12:')]")
# Only matches direct text nodes, not textContent of children
```

**Correct Implementation:**

Use JavaScript with `startsWith()` for exact matching on clickable elements only:

```javascript
// ✅ CORRECT - Exact matching on clickable elements
const patterns = ['Chương 12:', 'Chương 12 '];
const menuElements = document.querySelectorAll('button, a, li, div[role="button"], div[role="menuitem"]');

for (const elem of menuElements) {
    const text = elem.textContent.trim();
    for (const pattern of patterns) {
        if (text.startsWith(pattern)) {  // Exact match at start
            // Scroll menu container if needed
            const menuContainer = elem.closest('[role="menu"]') || elem.parentElement;
            if (menuContainer) {
                const containerRect = menuContainer.getBoundingClientRect();
                const elemRect = elem.getBoundingClientRect();
                if (elemRect.top < containerRect.top || elemRect.bottom > containerRect.bottom) {
                    elem.scrollIntoView({block: 'nearest', behavior: 'smooth'});
                }
            }
            elem.click();
            return;
        }
    }
}
```

**Implementation Locations:**
- Starting chapter navigation: [ui/link_to_text_widget.py:793-851](ui/link_to_text_widget.py)
- Subsequent chapter navigation: [ui/link_to_text_widget.py:970-1034](ui/link_to_text_widget.py)

**Key Lessons:**
1. Always use JavaScript for element finding/clicking when XPATH is unreliable
2. Use `startsWith()` instead of `contains()` for exact pattern matching
3. Only search within clickable element types to avoid matching containers
4. Implement menu scrolling for chapters beyond visible area (500+, 1000+)
5. Verify element text before clicking to ensure correct navigation

### Claude Processing Options

**Link to Text Widget** ([ui/link_to_text_widget.py](ui/link_to_text_widget.py)) offers three processing levels:

1. **Chỉ lấy text thô** - Scrape only, no Claude processing
2. **Lấy + Biên tập bằng Claude (realtime)** - Streaming API, real-time processing
3. **Lấy + Biên tập bằng Claude (batch - rẻ hơn 50%)** - Batch API, cheaper but delayed

#### Realtime Processing (ClaudeProcessWorker)

**Location:** [ui/link_to_text_widget.py:1295-1362](ui/link_to_text_widget.py)

Processes chapters sequentially with streaming API:
- ✅ Real-time: See results as each chapter completes
- ✅ Cancellable: Can stop mid-process
- ❌ More expensive: Standard API pricing (2x Batch)
- ❌ Slower: Sequential processing

```python
for chunk in claude_client.stream_message(messages, system_prompt):
    full_response += chunk
```

#### Batch Processing (BatchProcessWorker)

**Location:** [ui/link_to_text_widget.py:1365-1480](ui/link_to_text_widget.py)

Processes all chapters in parallel with Batch API:
- ✅ 50% cheaper: Batch API pricing
- ✅ Parallel processing: All chapters at once
- ❌ Delayed: Must wait 2-10 minutes for results
- ❌ No real-time feedback: Get all results at end

```python
batch_info = claude_client.create_batch(batch_requests)
# Poll every 10 seconds until status == 'ended'
batch_results = claude_client.get_batch_results(batch_id)
```

**When to use Batch:**
- Scraping 10+ chapters
- Not time-sensitive
- Want to minimize costs

#### Data Flow for Claude Processing

**CRITICAL**: Text content is stored in **RAM only**, not database.

```python
self.scraped_chapters = [
    (chapter_num, title, content),  # Tuples in memory
    ...
]
```

**How project context is loaded:**

```python
# ✅ CORRECT - Get instructions from project
project = db.get_project(project_id)
instructions = project['instructions']  # From projects.instructions column

# ✅ CORRECT - Get memory items
memory_items = db.get_memory(project_id)  # From project_memory table
memory = "\n".join([
    f"**{item['category']}** - {item['key']}: {item['value']}"
    for item in memory_items
])

# ✅ CORRECT - Get formatted glossary
glossary = db.get_glossary_for_prompt(project_id)  # From glossary_terms table
```

**Common Bug to Avoid:**

```python
# ❌ WRONG - These functions don't exist!
instructions = db.get_instructions(project_id)  # No such method
memory = db.get_memory(project_id)  # Returns list, not string
glossary_items = db.get_glossary(project_id)  # No such method
```

**System prompt construction:**

```python
system_parts = []
if instructions:
    system_parts.append(instructions)
if glossary:
    system_parts.append(f"\n## Thuật ngữ cần tuân thủ:\n{glossary}")
if memory:
    system_parts.append(f"\n## Thông tin bổ sung:\n{memory}")

system_prompt = "\n\n".join(system_parts)
```

**User message format:**

```python
content = f"Hãy biên tập nội dung chương truyện sau theo hướng dẫn:\n\n**{title}**\n\n{content}"
```

**What's included:**
- ✅ Instructions (from project)
- ✅ Memory (from project_memory table)
- ✅ Glossary (from glossary_terms table)
- ❌ Files (NOT included - would need custom implementation)

## Vietnamese Language Context

The application is designed for Vietnamese audiobook production with:
- Vietnamese UI throughout
- Templates for cultivation novel (tiên hiệp) editing
- Glossary categories: Cảnh giới (realms), Nhân vật (characters), Chiêu thức (techniques), Vật phẩm (items), Địa danh (places), Thế lực (factions)
- Focus on converting translated text to natural spoken Vietnamese

## Build & Deployment

### Building Executable with PyInstaller

**Location:** [build.py](build.py)

The build script packages the application as a standalone executable using PyInstaller.

**Usage:**
```bash
python build.py
```

**Key Features:**
1. **Auto-cleanup** - Removes `build/`, `dist/`, and `.spec` files before building to ensure clean builds
2. **Auto-detect virtual environment** - Uses `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Unix)
3. **Auto-install PyInstaller** - Checks and installs if missing
4. **Platform-specific data files** - Uses `;` separator on Windows, `:` on Unix
5. **Size calculation** - Reports final build size after completion

**Quick Rebuild:**
```bash
rebuild.bat  # Windows - Auto-cleanup and rebuild
```

**Critical: faster-whisper Assets**

The build script automatically includes `faster_whisper/assets` folder which contains:
- `silero_vad_v6.onnx` - Voice Activity Detection model (1.2 MB)

**Implementation (lines 87-109):**
```python
# Auto-detect faster_whisper assets
faster_whisper_path = venv_dir / 'Lib' / 'site-packages' / 'faster_whisper'
if faster_whisper_path.exists():
    assets_path = faster_whisper_path / 'assets'
    if assets_path.exists():
        print(f"  Found faster_whisper assets: {assets_path}")
        args.append(f'--add-data={assets_path}{separator}faster_whisper/assets')
```

**Why This Matters:**
- Without this, Video to Text will crash with: `[ONNXRuntimeError]: 3: NO_SUCHFILE: Load model from ...silero_vad_v6.onnx failed`
- The file must be at: `dist/AnhMinAudio/_internal/faster_whisper/assets/silero_vad_v6.onnx`
- PyInstaller does NOT automatically include data files from packages

**Build Output:**
- Executable: `dist/AnhMinAudio/AnhMinAudio.exe` (Windows)
- Size: ~3.9 GB (includes PyTorch, torchaudio, numpy, PyQt6, etc.)
- To reduce size: Exclude torch/torchaudio if Video to Text not needed

**Critical: Hidden Imports for Auto-Update**

The build script must include ALL dependencies for the auto-update system:

```python
'--hidden-import=gdown',              # For Google Drive downloads
'--hidden-import=packaging',          # For version comparison
'--hidden-import=requests',           # For HTTP downloads
'--hidden-import=urllib3',            # Dependency of requests
'--hidden-import=certifi',            # SSL certificates for requests
'--hidden-import=charset_normalizer', # Dependency of requests
'--hidden-import=filelock',           # Dependency of gdown
'--hidden-import=tqdm',               # Dependency of gdown (progress bar)
```

**Why This Matters:**
- Missing ANY of these will cause the app to crash when clicking "Tải về" (Download) in the update dialog
- PyInstaller does NOT auto-detect these transitive dependencies
- The app will work fine from source but crash when built as .exe without these imports

**Critical: stdout/stderr Redirection**

Windowed apps (`--windowed` mode) have `sys.stdout = None` and `sys.stderr = None`, causing ANY `print()` statement to crash the app.

**Solution:** Redirect stdout/stderr to null device at entry points:

In [main.py](main.py) (lines 13-21):
```python
# CRITICAL FIX: Redirect stdout/stderr to null when running as frozen windowed app
# This prevents crashes from print() statements throughout the entire app
if getattr(sys, 'frozen', False) and sys.stdout is None:
    if os.name == 'nt':  # Windows
        sys.stdout = open('nul', 'w', encoding='utf-8')
        sys.stderr = open('nul', 'w', encoding='utf-8')
    else:  # Unix-like
        sys.stdout = open('/dev/null', 'w', encoding='utf-8')
        sys.stderr = open('/dev/null', 'w', encoding='utf-8')
```

In [updater/updater.py](updater/updater.py) (lines 16-24):
```python
# CRITICAL FIX: Redirect stdout/stderr to null when running as frozen windowed app
# This prevents crashes from print() and sys.stdout.flush() calls
if getattr(sys, 'frozen', False) and sys.stdout is None:
    if os.name == 'nt':  # Windows
        sys.stdout = open('nul', 'w')
        sys.stderr = open('nul', 'w')
    else:  # Unix-like
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
```

**Why This Matters:**
- Without this, ANY `print()` or `sys.stdout.flush()` call crashes the app silently
- The app will work perfectly with `--console` mode but crash with `--windowed` mode
- This is the #1 cause of "app closes immediately" bugs in PyInstaller windowed apps

## Auto-Update System

**Location:** [updater/](updater/)

The application includes a complete auto-update system that checks for new versions from GitHub Releases and allows users to download and install updates with a single click.

### Module Structure

```
updater/
├── __init__.py           # Package exports
├── update_checker.py     # GitHub Releases API integration
└── updater.py           # Download and installation with UAC elevation
```

### Components

#### 1. UpdateChecker ([updater/update_checker.py](updater/update_checker.py))

Checks for updates from GitHub Releases API:

```python
class UpdateChecker:
    def __init__(self, repo_owner: str, repo_name: str, current_version: str)

    def check_for_updates(self) -> Optional[Dict]:
        # Returns dict with:
        # - version: str (e.g., "1.0.1")
        # - download_url: str (direct link to .exe)
        # - changelog: str (release body/notes)
        # - size: int (file size in bytes)
        # Returns None if no update or on error
```

**Key Features:**
- Uses `packaging.version.parse()` for semantic version comparison
- Fetches from `https://api.github.com/repos/{owner}/{repo}/releases/latest`
- Automatically strips 'v' prefix from versions
- Handles network errors gracefully

#### 2. Updater & DownloadWorker ([updater/updater.py](updater/updater.py))

**DownloadWorker** (QThread):
- Downloads update file to temp directory
- **Supports both regular HTTP and Google Drive downloads**
- **Automatically extracts .zip files** (for large updates >2GB)
- Streams download in 8KB chunks
- Emits progress signals for UI updates
- Supports cancellation mid-download

```python
class DownloadWorker(QThread):
    progress = pyqtSignal(int, int)  # (downloaded_bytes, total_bytes)
    finished = pyqtSignal(str, bool)  # (path, is_folder)
    error = pyqtSignal(str)           # error_message
```

**Google Drive Support:**

For large files (>2GB), GitHub's asset limit is 2GB. Use Google Drive instead:

```python
# In update_info from GitHub release body
{
    'download_url': 'https://drive.google.com/uc?export=download&id=FILE_ID&confirm=t',
    'file_name': 'AnhMinAudio-v1.0.1.zip'  # Can be .zip or .exe
}
```

**Implementation:**
- Uses `gdown` library to bypass Google Drive virus scan warnings
- Extracts file ID from URL: `?id=FILE_ID` or `/d/FILE_ID/`
- Downloads with `gdown.download(url, output=file_path, quiet=True, fuzzy=True)`
- **CRITICAL:** `quiet=True` is required to prevent crash in windowed mode (no stdout)

**ZIP Extraction:**

If `file_name` ends with `.zip`:
1. Download to temp directory
2. Extract to `C:\Users\...\Temp\AnhMinAudio_Update\`
3. Find folder containing `.exe` file
4. Delete ZIP file
5. Emit `finished.emit(app_folder, is_folder=True)`

If single `.exe` file:
1. Download to temp directory
2. Emit `finished.emit(file_path, is_folder=False)`

**Updater** (Static class):
- Requests UAC admin elevation automatically
- Creates self-deleting batch script to replace files
- **Supports both folder (extracted ZIP) and single .exe replacement**
- Restarts application after update

```python
class Updater:
    @staticmethod
    def request_admin_and_install(update_path: str, is_folder: bool = False) -> bool:
        # Creates batch script:
        # 1. Wait 2 seconds for app to close
        # 2. Replace files (folder or single .exe)
        # 3. Restart application
        # 4. Delete batch script itself

        # Uses ctypes.windll.shell32.ShellExecuteW with "runas" for UAC
```

**Batch Script Template (Folder Replacement):**
```batch
@echo off
chcp 65001 >nul
timeout /t 2 /nobreak >nul
echo Removing old files...
del /q "C:\App\*.exe"
del /q "C:\App\*.dll"
if exist "C:\App\_internal" rmdir /s /q "C:\App\_internal"
echo Copying new files...
xcopy /E /I /Y "C:\Temp\AnhMinAudio_Update\*" "C:\App\"
rmdir /s /q "C:\Temp\AnhMinAudio_Update"
start "" "C:\App\AnhMinAudio.exe"
del "%~f0"
```

**Batch Script Template (Single .exe Replacement):**
```batch
@echo off
chcp 65001 >nul
timeout /t 2 /nobreak >nul
copy /y "C:\Temp\Update.exe" "C:\App\AnhMinAudio.exe"
del "C:\Temp\Update.exe"
start "" "C:\App\AnhMinAudio.exe"
del "%~f0"
```

#### 3. UpdateDialog ([ui/update_dialog.py](ui/update_dialog.py))

User interface for update process:

**UI Elements:**
- Version info and changelog display
- File size information
- Progress bar (hidden until download starts)
- Download/Cancel buttons

**Update Flow:**
1. User clicks "Tải về" → DownloadWorker starts
2. Progress bar updates in real-time
3. On completion → Confirmation dialog
4. User clicks OK → UAC popup → Install → Restart

### Integration Points

#### Main Window ([ui/main_window.py](ui/main_window.py))

**Background Check on Startup:**

```python
def check_for_updates_background(self):
    """Check for updates in background thread."""
    class UpdateCheckWorker(QThread):
        finished = pyqtSignal(object)

        def run(self):
            checker = UpdateChecker(GITHUB_OWNER, GITHUB_REPO, APP_VERSION)
            update_info = checker.check_for_updates()
            self.finished.emit(update_info)

    self.update_check_worker = UpdateCheckWorker()
    self.update_check_worker.finished.connect(self.on_update_check_finished)
    self.update_check_worker.start()

def on_update_check_finished(self, update_info):
    if update_info:
        self.update_info = update_info
        self.sidebar.show_update_badge(True)  # Show red dot
```

**Manual Check:**

```python
def check_for_updates_manual(self):
    """Manually check when user clicks button."""
    if self.update_info:
        self.show_update_dialog()  # Use cached info
    else:
        # Check again and show loading message
```

#### Sidebar ([ui/sidebar.py](ui/sidebar.py))

**Update Button with Red Dot Badge:**

```python
# Update button (lines 290-314)
update_btn_container = QFrame()
self.update_btn = QPushButton("🔄 Cập nhật")
self.update_btn.clicked.connect(self.update_clicked.emit)

# Red dot notification badge (hidden by default)
self.update_badge = QLabel("●")
self.update_badge.setStyleSheet(f"color: #EF4444; font-size: 20px;")
self.update_badge.setVisible(False)

def show_update_badge(self, show: bool = True):
    """Show or hide the update notification badge."""
    self.update_badge.setVisible(show)
```

### Configuration

**GitHub Repository Settings** ([config.py](config.py)):

```python
# GitHub Update Configuration (lines 14-18)
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"  # Must be updated before release
GITHUB_REPO = "anhmin-audio"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
```

**Version Number:**

```python
APP_VERSION = "1.0.0"  # Increment for each release
```

**Dependencies:**

```python
# requirements.txt
packaging>=23.0  # Version comparison for auto-update
```

### Update Flow

**Complete Update Process:**

```
1. App Startup
   ↓
2. Background UpdateCheckWorker starts (non-blocking)
   ↓
3. Fetch latest release from GitHub API
   ↓
4. Compare versions using packaging.version.parse()
   ↓
5a. No update → Hide red dot badge
5b. Update available → Show red dot badge, cache update_info
   ↓
6. User clicks "🔄 Cập nhật" button
   ↓
7. Show UpdateDialog with changelog
   ↓
8. User clicks "Tải về"
   ↓
9. DownloadWorker downloads file
   - If Google Drive: Use gdown with quiet=True
   - If regular HTTP: Stream with requests
   ↓
10. Progress bar updates (0% → 100%)
   ↓
11a. If .zip file:
    - Extract to C:\Users\...\Temp\AnhMinAudio_Update\
    - Find folder containing .exe
    - Delete .zip file
11b. If .exe file:
    - Keep in temp directory
   ↓
12. Download complete → Show confirmation dialog
   ↓
13. User clicks OK → Updater.request_admin_and_install(path, is_folder)
   ↓
14. UAC popup → User clicks "Yes"
   ↓
15. Batch script runs (hidden window):
    - Wait 2 seconds
    - Replace files (folder copy or single .exe)
    - Restart application
    - Clean up temp files
    - Self-delete
   ↓
16. App closes → New version starts → Update complete
```

### Data Safety

**Critical:** User data is NOT lost during updates!

- Database location: `C:\Users\<username>\.anhmin_audio\database.db`
- .exe location: `C:\Users\<username>\...\AnhMinAudio.exe` (or wherever user extracted)
- Update only replaces the .exe file, NOT the database

**Safe Update Process:**
1. Only the executable is replaced
2. Database and project files remain untouched
3. All settings, API keys, projects preserved

### Error Handling

**Download Errors:**
```python
def on_download_error(self, error_msg: str):
    # Shows error message with retry option
    # Download button re-enabled for retry
```

**Installation Errors:**
```python
def install_update(self):
    success = Updater.request_admin_and_install(self.downloaded_file)
    if not success:
        # Shows error: "Please install manually"
```

**Version Check Errors:**
- Silent failure - no popup
- App continues normally
- Red dot badge not shown

### Setup Instructions

For developers setting up GitHub releases, see detailed guide in [GITHUB_SETUP.md](GITHUB_SETUP.md):

1. Create GitHub account
2. Create repository: `https://github.com/USERNAME/anhmin-audio`
3. Update `GITHUB_OWNER` in [config.py](config.py)
4. Build executable with `python build.py`
5. Create release on GitHub with tag `v1.0.0`
6. Upload .exe to release assets
7. Publish release

### Testing Auto-Update

**Test Scenario:**

1. Build app v1.0.0
2. Create GitHub release v1.0.0 with .exe
3. Update `config.py` to `APP_VERSION = "1.0.1"`
4. Build app v1.0.1
5. Create GitHub release v1.0.1 with new .exe
6. Run app v1.0.0 → Red dot appears
7. Click update → Download → Install → App restarts as v1.0.1

### Common Issues and Troubleshooting

#### Issue: App crashes when clicking "Tải về" (Download)

**Symptoms:**
- App works from source (`python main.py`) but crashes when built as .exe
- No error message shown, app just closes immediately

**Root Causes:**
1. **Missing PyInstaller hidden imports** - Check build.py includes all 8 dependencies:
   - gdown, packaging, requests, urllib3, certifi, charset_normalizer, filelock, tqdm

2. **stdout/stderr redirection missing** - Check main.py and updater/updater.py have redirection code at top

**Solution:**
```bash
# Clean rebuild to ensure fresh build
rebuild.bat
```

#### Issue: Progress bar stuck at 0%

**Symptoms:**
- Download completes successfully (files downloaded)
- Progress bar never moves from 0%
- No error shown

**Root Cause:**
- `gdown.download(quiet=False)` tries to write to stdout, which is None in windowed mode
- Progress signals are emitted but `gdown` internal progress overwrites them

**Solution:**
- Already fixed in current code with `quiet=True`
- If rebuilding from older version, ensure line 97 in updater/updater.py has `quiet=True`

#### Issue: Double popup messages when checking for updates

**Symptoms:**
- Two popups appear when clicking "🔄 Cập nhật" button
- First: "Đang kiểm tra phiên bản mới..."
- Second: "Bạn đang sử dụng phiên bản mới nhất"

**Root Cause:**
- Old build cache contains outdated main_window.py with loading message popup

**Solution:**
```bash
# Clean rebuild to remove cached files
rebuild.bat
```

#### Debugging Tips

**Run with console to see errors:**
1. Open `build.py`
2. Change line 67: `'--windowed'` → `'--console'`
3. Build: `python build.py`
4. Run: `.\dist\AnhMinAudio\AnhMinAudio.exe`
5. All print() statements and errors will show in console window

**Check if dependencies are bundled:**
```bash
# After building, check if gdown is included
dir dist\AnhMinAudio\_internal\gdown*
```

### Future Enhancements

Potential improvements (not yet implemented):

1. **Delta Updates**: Only download changed files (reduce bandwidth)
2. **Rollback Mechanism**: Backup old .exe before replacing
3. **Auto-install Option**: Skip confirmation dialog
4. **Update Scheduler**: Check for updates daily/weekly
5. **Beta Channel**: Separate channel for pre-release versions
6. **Portable Mode Detection**: Skip update if running from USB drive

## Auto-Memory Detection System

**Location:** [api/memory_detector.py](api/memory_detector.py)

The application automatically detects and extracts memory items from chapter content using Claude API. This system eliminates manual memory entry and ensures comprehensive context tracking.

### How It Works

1. **Content Analysis**: When chapters are processed (Chat, Link to Text), the content is sent to Claude with a detection prompt
2. **Memory Extraction**: Claude analyzes and returns memory items in Markdown format
3. **Auto-Addition**: Detected items are automatically added to the project's memory database
4. **Duplicate Prevention**: System checks for existing keys before adding new items

### Memory Categories

The system detects 6 main categories:

| Category | Database Key | Description |
|----------|--------------|-------------|
| Nhân vật | `character` | Characters, protagonists, antagonists |
| Địa danh | `location` | Locations, places, cities |
| Cảnh giới | `realm` | Cultivation realms, power levels |
| Kỹ năng | `skill` | Techniques, martial arts, spells |
| Vật phẩm | `item` | Items, artifacts, treasures |
| Thế lực | `faction` | Organizations, sects, factions |

### Detection Prompt Format

Claude is instructed to return memory in this Markdown format:

```markdown
## Nhân vật:
- tieu_viem: Tiêu Viêm - nhân vật chính
- duoc_lao: Dược Lão - thầy của Tiêu Viêm

## Địa danh:
- o_dam_thanh: Ô Đàm Thành - nơi xuất phát

## Cảnh giới:
- dau_chi: Đấu Khí - cảnh giới đầu tiên
```

**Key Requirements:**
- `key_name` must be snake_case (lowercase, underscores, no Vietnamese diacritics)
- Only extract IMPORTANT information, not minor details
- Skip categories with no new information
- Each item: one line, concise description

### Integration Points

#### 1. Chat Widget

**Location:** [ui/chat_widget.py:612-614](ui/chat_widget.py#L612-L614)

Auto-detects memory from Claude's response after streaming completes:

```python
def on_stream_finished(self, full_response: str):
    # Save to database
    db.add_message(self.session_id, 'assistant', full_response)

    # Auto-detect and add memory from response
    if self.project_id:
        auto_detect_and_add_memory(full_response, self.project_id)
```

**Behavior:** Silent addition, no popup notification

#### 2. Link to Text - Realtime Processing

**Location:** [ui/link_to_text_widget.py:2315-2317](ui/link_to_text_widget.py#L2315-L2317)

Detects memory immediately after each chapter is processed:

```python
def on_claude_chapter_done(self, chapter_num: int, title: str, content: str):
    self.results_list.append(f"✨ Claude: {title} ({len(content)} ký tự)")

    # Auto-detect and add memory from processed chapter
    if self.project_id:
        auto_detect_and_add_memory(content, self.project_id)
```

**Behavior:** Per-chapter detection, incremental memory building

#### 3. Link to Text - Batch Processing

**Location:** [ui/link_to_text_widget.py:2359-2363](ui/link_to_text_widget.py#L2359-L2363)

Detects memory from all chapters after batch completion:

```python
def on_batch_finished(self, results: list):
    # Auto-detect and add memory from all processed chapters
    if self.project_id:
        for chapter_num, title, content in results:
            self.results_list.append(f"✨ {title} ({len(content)} ký tú)")
            auto_detect_and_add_memory(content, self.project_id)
```

**Behavior:** Batch detection, all chapters processed sequentially

### Memory Widget - Read-Only Display

**Location:** [ui/memory_widget.py](ui/memory_widget.py)

The Memory Widget has been redesigned as a **read-only display** for auto-detected memory:

**Removed Features:**
- ❌ Manual input form
- ❌ "Paste từ Claude" button
- ❌ Edit mode toggle
- ❌ Delete buttons on individual items

**Current Features:**
- ✅ Read-only list display of all memory items
- ✅ Category labels for each item
- ✅ "🗑️ Xóa tất cả Memory" button with confirmation dialog

**UI Elements:**
```python
# Header
title = "Project Memory"
subtitle = "Memory tự động cập nhật từ các chương được xử lý."

# Clear all button
clear_btn = QPushButton("🗑️ Xóa tất cả Memory")
# Shows confirmation: "Memory sẽ được tự động tạo lại từ các chương tiếp theo sau khi xóa"
```

**Philosophy:** Memory is fully automated. Users should not manually add items to ensure accuracy. If memory is incorrect, delete all and let the system rebuild from subsequent chapters.

### API Function

**Main Entry Point:**

```python
from api.memory_detector import auto_detect_and_add_memory

items_added, error_msg = auto_detect_and_add_memory(content, project_id)
```

**Returns:**
- `items_added` (int): Number of new memory items added
- `error_msg` (str): Error message if failed, empty string if success

**Internal Flow:**

1. `MemoryDetector.detect_memory()` - Calls Claude API with detection prompt
2. `MemoryDetector._parse_and_add_memory()` - Parses Markdown response
3. `db.set_memory()` - Adds to database (skips duplicates)

### Error Handling

```python
try:
    items_added, error = auto_detect_and_add_memory(content, project_id)
    if error:
        # Log error, but don't interrupt main workflow
        print(f"Memory detection failed: {error}")
except Exception as e:
    # Silent failure - memory detection should never crash the app
    pass
```

**Design Decision:** Memory detection failures are silent and non-blocking. The main workflow (chat, scraping) continues regardless of memory detection success.

### Database Storage

Memory items are stored in the `project_memory` table:

```sql
CREATE TABLE project_memory (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    category TEXT,      -- character, location, realm, skill, item, faction
    key TEXT,           -- snake_case identifier
    value TEXT,         -- Display name and description
    created_at TIMESTAMP
)
```

**Duplicate Check:**
```python
existing_memory = db.get_memory(project_id)
key_exists = any(
    mem['key'] == key and mem['category'] == current_category
    for mem in existing_memory
)
if not key_exists:
    db.set_memory(project_id, key, value, current_category)
```

### Use Cases

**Scenario 1: Starting New Project**
1. User creates project
2. User scrapes first 10 chapters with Claude processing
3. Memory auto-populates with characters, locations, etc.
4. Memory is available for subsequent chapter processing

**Scenario 2: Wrong Genre Detected**
1. User accidentally processes wrong novel
2. Memory fills with incorrect information
3. User clicks "🗑️ Xóa tất cả Memory"
4. Confirms deletion
5. Processes correct chapters → Memory rebuilds automatically

**Scenario 3: Ongoing Series**
1. User processes chapters 1-100
2. Memory contains all major characters/locations
3. New chapters 101-110 introduce new characters
4. Auto-detection adds only NEW items (no duplicates)
5. Memory stays up-to-date automatically

### Performance Considerations

- **API Calls**: Each chapter triggers one additional Claude API call for memory detection
- **Cost**: Uses standard API (not batch) for immediate feedback
- **Token Usage**: Detection prompt + chapter content (varies by length)
- **Optimization**: Memory detection runs AFTER chapter processing completes, not during streaming

### Future Enhancements

Potential improvements (not yet implemented):

1. **Smart Filtering**: Only detect memory from chapters where new information is likely (skip filler chapters)
2. **Batch Detection**: For Link to Text batch processing, send all chapters in one detection call
3. **Memory Confidence**: Track which memory items are most frequently mentioned
4. **Category Auto-Expansion**: Learn new categories from user patterns
5. **Memory Merging**: Detect when two keys refer to same entity and merge
