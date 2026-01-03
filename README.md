# 🎙️ AnhMin Audio - Claude AI Project Manager

Ứng dụng desktop quản lý dự án sản xuất audiobook với Claude AI.

## ✨ Tính năng

- 💬 **Chat với Claude AI** - Streaming real-time, giao diện đẹp
- 📝 **Project Instructions** - Hướng dẫn riêng cho từng dự án
- 📁 **Files Management** - Upload và quản lý file dự án (TXT, DOCX)
- 🧠 **Memory System** - Lưu thông tin series, nhân vật, địa danh...
- 🔄 **Auto-rotate API Keys** - Tự động chuyển key khi hết quota
- 📥 **Export DOCX** - Tải nội dung về dưới dạng Word
- 🎨 **Dark Theme** - Giao diện tối hiện đại

## 📋 Yêu cầu hệ thống

- Python 3.9 trở lên
- Windows 10/11 hoặc macOS 10.14+
- API Key từ Anthropic

## 🚀 Cài đặt

### Bước 1: Clone hoặc tải project

```bash
# Clone từ GitHub (nếu có)
git clone https://github.com/your-repo/anhmin-audio.git
cd anhmin-audio

# Hoặc giải nén file ZIP
```

### Bước 2: Tạo môi trường ảo (khuyến nghị)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Bước 4: Chạy ứng dụng

```bash
python main.py
```

## 🔧 Cấu hình

### Thêm API Key

1. Mở ứng dụng
2. Click **"⚙️ Cài đặt API"** ở sidebar
3. Click **"➕ Thêm API Key"**
4. Nhập API key từ Anthropic Console
5. Có thể thêm tối đa 3 keys để tự động chuyển đổi

### Lấy API Key

1. Truy cập [console.anthropic.com](https://console.anthropic.com)
2. Đăng ký/Đăng nhập
3. Vào **API Keys** → **Create Key**
4. Copy key (bắt đầu bằng `sk-ant-...`)

## 📖 Hướng dẫn sử dụng

### Tạo dự án mới

1. Click **"➕ Dự án mới"** ở sidebar
2. Nhập tên dự án (VD: "Đấu Phá Thương Khung")
3. Click **"Tạo dự án"**

### Cấu hình Instructions

1. Chọn tab **"📝 Hướng dẫn"**
2. Nhập hướng dẫn cho Claude về phong cách viết
3. Click **"Lưu thay đổi"**

### Upload Files

1. Chọn tab **"📁 Files"**
2. Kéo thả file vào vùng upload hoặc click để chọn
3. Hỗ trợ: TXT, DOCX

### Thêm Memory

1. Chọn tab **"🧠 Memory"**
2. Chọn loại (Nhân vật, Địa danh, v.v.)
3. Nhập key và value
4. Click **"Thêm"**

### Chat với Claude

1. Chọn tab **"💬 Chat"**
2. Nhập yêu cầu hoặc chọn template có sẵn
3. Có thể đính kèm file bằng nút 📎
4. Nhấn **Ctrl+Enter** để gửi

### Tải xuống kết quả

- Mỗi tin nhắn từ Claude có nút **"📥 Tải xuống DOCX"**
- Click để lưu nội dung thành file Word

## ⌨️ Phím tắt

| Phím | Chức năng |
|------|-----------|
| `Ctrl+Enter` | Gửi tin nhắn |
| `Ctrl+U` | Đính kèm file |
| `Ctrl+N` | Tạo dự án mới |
| `Ctrl+1` | Tab Chat |
| `Ctrl+2` | Tab Hướng dẫn |
| `Ctrl+3` | Tab Files |
| `Ctrl+4` | Tab Memory |

## 📂 Cấu trúc thư mục

```
anhmin_audio/
├── main.py              # Điểm khởi chạy
├── config.py            # Cấu hình ứng dụng
├── requirements.txt     # Thư viện cần thiết
├── api/
│   ├── claude_client.py # Claude API client
│   └── file_handler.py  # Xử lý file
├── database/
│   └── db_manager.py    # SQLite database
└── ui/
    ├── main_window.py   # Cửa sổ chính
    ├── sidebar.py       # Sidebar dự án
    ├── chat_widget.py   # Giao diện chat
    ├── instructions_widget.py
    ├── files_widget.py
    ├── memory_widget.py
    ├── settings_dialog.py
    └── styles.py        # Theme & CSS
```

## 🗄️ Dữ liệu

Dữ liệu được lưu tại:
- **Windows:** `C:\Users\<username>\.anhmin_audio\`
- **macOS:** `/Users/<username>/.anhmin_audio/`

Bao gồm:
- `database.db` - SQLite database
- `projects/` - File dự án

## ❓ Xử lý lỗi

### "Không có API key khả dụng"
→ Thêm API key trong Cài đặt

### "Tất cả API key đã hết quota"
→ Thêm API key mới hoặc chờ reset quota

### Ứng dụng không khởi động
→ Kiểm tra Python version: `python --version` (cần 3.9+)
→ Cài lại thư viện: `pip install -r requirements.txt`

## 📝 Changelog

### v1.0.0 (2025)
- Phát hành đầu tiên
- Chat với Claude API (streaming)
- Quản lý Projects, Files, Memory
- Export DOCX
- Auto-rotate API keys

## 👨‍💻 Tác giả

**PhamDung** - AnhMin Audio

## 📄 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.




1. Tại sao nên gõ /init ngay lần đầu?
Khi bạn chạy /init, Claude Code sẽ thực hiện các việc sau: 
Phân tích toàn bộ dự án: Nó quét các tệp tin để hiểu cấu trúc thư mục, ngôn ngữ lập trình và các thư viện bạn đang dùng.
Tạo file CLAUDE.md: Đây được coi là "bộ nhớ dự án". File này lưu trữ các quy ước viết code, lệnh chạy test, build và các thông tin quan trọng khác để Claude không quên trong các phiên làm việc sau.



Lời khuyên để Claude "thông minh" hơn theo thời gian:
Cuối mỗi phiên làm việc: Bạn nên hỏi: "Có thông tin quan trọng nào từ cuộc hội thoại hôm nay mà chúng ta cần cập nhật vào CLAUDE.md không?".


Sử dụng /compact: Nếu cuộc trò chuyện quá dài, hãy dùng lệnh này để Claude tóm tắt lại những gì đã học được, giúp giải phóng bộ nhớ mà không mất đi các ý chính.




Thư viện cần cài

pip install PyQt6

pip install anthropic

pip install python-docx

pip install docx2txt

pip install selenium webdriver-manager

pip install PyQt6 anthropic python-docx docx2txt

pip install undetected-chromedriver

pip install PyQt6 PyQt6-Qt6




pip install pyinstaller



pyinstaller --windowed --name "FileSyncPro" --icon=anhmin.ico main.py

pyinstaller --windowed --name "AnhMinAPIclaude" main.py