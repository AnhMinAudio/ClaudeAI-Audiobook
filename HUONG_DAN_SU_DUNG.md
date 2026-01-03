# 📚 HƯỚNG DẪN SỬ DỤNG ANHMIN AUDIO

## Mục lục
1. [Giới thiệu](#-giới-thiệu)
2. [Cài đặt](#-cài-đặt)
3. [Giao diện chính](#-giao-diện-chính)
4. [Các tính năng](#-các-tính-năng)
5. [Hướng dẫn từng tab](#-hướng-dẫn-từng-tab)
6. [Phím tắt](#-phím-tắt)
7. [Khắc phục lỗi](#-khắc-phục-lỗi)
8. [FAQ](#-faq)

---

## 🎯 Giới thiệu

**AnhMin Audio** là ứng dụng desktop hỗ trợ tạo nội dung audiobook tiếng Việt, đặc biệt phù hợp cho việc chuyển đổi và biên tập truyện Trung Quốc (xianxia, tiên hiệp).

### Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| 💬 **Chat với Claude AI** | Trò chuyện và biên tập nội dung với AI |
| 📝 **Template Prompt** | Hướng dẫn có sẵn cho từng loại công việc |
| 📁 **Quản lý Files** | Upload và quản lý tài liệu tham khảo |
| 🧠 **Memory** | Lưu trữ thông tin về series, nhân vật |
| 📦 **Batch Processing** | Xử lý hàng loạt nhiều chương cùng lúc |
| 📚 **Glossary** | Quản lý thuật ngữ, tên riêng |
| 🎬 **Video to Text** | Chuyển video/audio thành văn bản |
| 🔗 **Link to Text** | Lấy nội dung từ website truyện |

---

## 🛠 Cài đặt

### Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| **Hệ điều hành** | Windows 10/11, macOS 11+, Linux |
| **Python** | 3.9 trở lên |
| **RAM** | 8GB (16GB khuyến nghị) |
| **Ổ cứng** | 5GB trống |

### Bước 1: Cài đặt Python

#### Windows
1. Tải Python từ https://www.python.org/downloads/
2. Chạy installer, **tick ✅ "Add Python to PATH"**
3. Mở Command Prompt, kiểm tra: `python --version`

#### macOS
```bash
brew install python@3.11
```

#### Linux
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Bước 2: Cài đặt Visual Studio Code (Khuyến nghị)

1. Tải VS Code từ https://code.visualstudio.com/
2. Cài đặt Extension **Python** (Microsoft)
3. Cài đặt Extension **Pylance** (Microsoft)

### Bước 3: Clone/Tải project

```bash
# Tạo thư mục project
mkdir anhmin_audio
cd anhmin_audio

# Giải nén file zip vào thư mục này
```

### Bước 4: Tạo môi trường ảo (Virtual Environment)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 5: Cài đặt thư viện cơ bản

```bash
pip install -r requirements.txt
```

**Hoặc cài từng thư viện:**

```bash
# Thư viện bắt buộc
pip install PyQt6 PyQt6-Qt6 anthropic python-docx docx2txt keyring

# Link to Text (bắt buộc)
pip install beautifulsoup4 requests selenium webdriver-manager
```

### Bước 6: Cài đặt thư viện Video to Text (tùy chọn)

#### Windows (NVIDIA GPU)
```bash
pip install faster-whisper yt-dlp
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
winget install ffmpeg
```

#### macOS (Apple Silicon M1/M2/M3)
```bash
pip install mlx-whisper yt-dlp
brew install ffmpeg
```

#### macOS (Intel) / Linux
```bash
pip install faster-whisper yt-dlp
# FFmpeg: brew install ffmpeg (macOS) hoặc sudo apt install ffmpeg (Linux)
```

### Bước 7: Chạy ứng dụng

```bash
# Windows
python main.py

# macOS / Linux
python3 main.py
```

**Hoặc dùng script có sẵn:**
- Windows: Double-click `run_windows.bat`
- macOS: `./run_macos.sh`

---

## 🖥 Giao diện chính

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AnhMin Audio v8.0                                                      │
├──────────┬──────────────────────────────────────────────────────────────┤
│          │  📁 Tên Project                           [💬 Chat mới]      │
│  SIDEBAR │  ────────────────────────────────────────────────────────── │
│          │  💬 Chat │ 📝 Hướng dẫn │ 📁 Files │ 🧠 Memory │ ...        │
│  ┌─────┐ │  ┌────────────────────────────────────────────────────────┐ │
│  │ Dự  │ │  │                                                        │ │
│  │ án  │ │  │                    NỘI DUNG TAB                        │ │
│  │ 1   │ │  │                                                        │ │
│  ├─────┤ │  │                                                        │ │
│  │ Dự  │ │  │                                                        │ │
│  │ án  │ │  │                                                        │ │
│  │ 2   │ │  └────────────────────────────────────────────────────────┘ │
│  └─────┘ │                                                              │
│          │                                                              │
│ [⚙️ Cài │                                                              │
│  đặt]   │                                                              │
└──────────┴──────────────────────────────────────────────────────────────┘
```

### Sidebar (Bên trái)
- **Danh sách dự án**: Click để chọn dự án
- **➕ Tạo mới**: Tạo dự án mới
- **⚙️ Cài đặt**: Quản lý API Key, model, cài đặt

### Tabs (8 tab)
| Tab | Phím tắt | Mô tả |
|-----|----------|-------|
| 💬 Chat | Ctrl+1 | Chat với Claude AI |
| 📝 Hướng dẫn | Ctrl+2 | Thiết lập Instructions/Template |
| 📁 Files | Ctrl+3 | Quản lý tài liệu tham khảo |
| 🧠 Memory | Ctrl+4 | Thông tin về series, nhân vật |
| 📦 Batch | Ctrl+5 | Xử lý hàng loạt |
| 📚 Thuật ngữ | Ctrl+6 | Quản lý glossary |
| 🎬 Video to Text | Ctrl+7 | Video/audio → văn bản |
| 🔗 Link to Text | Ctrl+8 | Website → văn bản |

---

## 📋 Các tính năng

### 1. Quản lý API Key

1. Click **⚙️ Cài đặt** ở góc dưới trái
2. Trong tab **🔑 API Keys**:
   - Nhập tên key (ví dụ: "Main Key")
   - Dán API Key từ https://console.anthropic.com/
   - Click **➕ Thêm**
3. Có thể thêm nhiều key để backup

### 2. Chọn Model

1. Click **⚙️ Cài đặt**
2. Tab **🤖 Model**
3. Chọn model phù hợp:
   - **claude-sonnet-4-20250514**: Nhanh, cân bằng (khuyến nghị)
   - **claude-opus-4-20250514**: Mạnh nhất, chậm hơn
   - **claude-3-5-haiku-20241022**: Nhanh nhất, rẻ nhất

### 3. Extended Thinking

1. Click **⚙️ Cài đặt** → Tab **🤖 Model**
2. Tick **Bật Extended Thinking**
3. Điều chỉnh budget token (mặc định: 10,000)
4. Tính năng này giúp Claude suy nghĩ sâu hơn trước khi trả lời

---

## 📖 Hướng dẫn từng tab

### 💬 Tab Chat

**Mục đích:** Trò chuyện trực tiếp với Claude AI

**Cách sử dụng:**
1. Nhập tin nhắn vào ô chat
2. Nhấn **Enter** hoặc click **Gửi**
3. Claude sẽ trả lời dựa trên:
   - Instructions (tab Hướng dẫn)
   - Files đã upload (tab Files)
   - Memory (tab Memory)
   - Glossary (tab Thuật ngữ)

**Tính năng:**
- 📎 **Đính kèm file**: Upload file trực tiếp vào chat
- 💬 **Chat mới**: Bắt đầu cuộc hội thoại mới
- 📋 **Copy**: Copy câu trả lời

---

### 📝 Tab Hướng dẫn (Instructions)

**Mục đích:** Thiết lập hướng dẫn cho Claude về cách xử lý nội dung

**Cách sử dụng:**
1. Chọn **Template** có sẵn (dropdown)
2. Hoặc viết hướng dẫn riêng
3. Click **💾 Lưu**

**Các template có sẵn:**
- **Biên tập Audiobook**: Chuyển văn phong sang dạng đọc
- **Dịch thuật**: Dịch tiếng Trung sang tiếng Việt
- **Tóm tắt**: Tóm tắt nội dung
- **Viết lại**: Viết lại hoàn toàn theo phong cách mới

---

### 📁 Tab Files

**Mục đích:** Upload tài liệu tham khảo (chương trước, context, ...)

**Cách sử dụng:**
1. Click **📁 Upload file** hoặc kéo thả
2. Hỗ trợ: .txt, .docx, .pdf
3. Các file này sẽ được gửi kèm khi chat với Claude

**Lưu ý:**
- Giới hạn: 10 file, mỗi file tối đa 5MB
- File text được ưu tiên (nhẹ, nhanh)

---

### 🧠 Tab Memory

**Mục đích:** Lưu thông tin về series, nhân vật, bối cảnh

**Cách sử dụng:**
1. Nhập thông tin cần nhớ
2. Click **💾 Lưu**

**Ví dụ:**
```
## Thông tin series
- Tên truyện: Đấu Phá Thương Khung Hậu Truyện
- Nhân vật chính: Tiêu Viêm
- Bối cảnh: Sau khi đánh bại Hồn Thiên Đế

## Nhân vật quan trọng
- Tiêu Viêm: Chủ nhân Đấu Đế
- Cổ Huân Nhi: Vợ của Tiêu Viêm
- Dược Lão: Sư phụ luyện đan
```

---

### 📦 Tab Batch

**Mục đích:** Xử lý nhiều chương cùng lúc

**Cách sử dụng:**
1. Click **📂 Chọn thư mục** chứa các file chương
2. Hoặc **📄 Chọn files** để chọn từng file
3. Chọn định dạng output: TXT hoặc DOCX
4. Click **🚀 Bắt đầu**

**Lưu ý:**
- Mỗi file sẽ được xử lý riêng
- Kết quả lưu vào thư mục bạn chọn
- Chi phí API tính theo số chương

---

### 📚 Tab Thuật ngữ (Glossary)

**Mục đích:** Quản lý tên riêng, thuật ngữ cần giữ nguyên

**Cách sử dụng:**
1. Nhập **Thuật ngữ** và **Định nghĩa/Cách dịch**
2. Click **➕ Thêm**
3. Claude sẽ tuân thủ khi biên tập

**Ví dụ:**
| Thuật ngữ | Định nghĩa |
|-----------|------------|
| 斗帝 | Đấu Đế |
| 萧炎 | Tiêu Viêm |
| 古薰儿 | Cổ Huân Nhi |
| 药老 | Dược Lão |

---

### 🎬 Tab Video to Text

**Mục đích:** Chuyển video/audio thành văn bản

**Yêu cầu:**
- Cài đặt thư viện Whisper (xem phần Cài đặt)
- FFmpeg

**Cách sử dụng:**
1. Nhập **YouTube URL** hoặc click **📁 Chọn file**
2. Chọn **Model Whisper** (large-v3 khuyến nghị)
3. Nếu model chưa tải, click **⬇️ Tải về**
4. Chọn mức độ xử lý:
   - **Chỉ Whisper**: Lấy text thô (miễn phí)
   - **Whisper + Claude**: Biên tập bằng Claude (tốn phí)
5. Click **🚀 Bắt đầu**

---

### 🔗 Tab Link to Text

**Mục đích:** Lấy nội dung từ website truyện

**Website hỗ trợ:**
- ✅ truyenphuongdong.com
- ✅ piaotia.com
- ✅ truyenfull.vn
- ✅ tangthuvien.vn
- ✅ metruyencv.com
- ✅ wikidich.com
- ✅ sstruyen.vn

**Cách sử dụng:**

#### Với truyenphuongdong.com:
1. Dán link truyện vào ô **🔗 Link truyện**
2. Click **🔍 Kiểm tra**
3. Nhập phạm vi chương: **Từ** và **Đến**
4. Chọn mức độ xử lý:
   - **Chỉ lấy nội dung**: Scrape text (miễn phí)
   - **Lấy + Claude**: Biên tập bằng Claude (tốn phí)
5. Click **🚀 Bắt đầu**

#### Với piaotia.com và các trang khác:
1. Dán nhiều link vào ô text (mỗi link 1 dòng)
2. Hoặc tải file .txt chứa danh sách link
3. Click **🚀 Bắt đầu**

**Kết quả:**
- Mỗi chương → 1 file riêng
- Hoặc gộp tất cả → 1 file

---

## ⌨️ Phím tắt

| Phím | Chức năng |
|------|-----------|
| **Ctrl+N** | Tạo dự án mới |
| **Ctrl+U** | Upload file |
| **Ctrl+Enter** | Gửi tin nhắn |
| **Ctrl+1** | Tab Chat |
| **Ctrl+2** | Tab Hướng dẫn |
| **Ctrl+3** | Tab Files |
| **Ctrl+4** | Tab Memory |
| **Ctrl+5** | Tab Batch |
| **Ctrl+6** | Tab Thuật ngữ |
| **Ctrl+7** | Tab Video to Text |
| **Ctrl+8** | Tab Link to Text |

---

## 🔧 Khắc phục lỗi

### Lỗi: "ModuleNotFoundError: No module named 'PyQt6'"

```bash
pip install PyQt6 PyQt6-Qt6
```

### Lỗi: "API key not found"

1. Mở **⚙️ Cài đặt**
2. Tab **🔑 API Keys**
3. Thêm API key từ https://console.anthropic.com/

### Lỗi: "selenium not found" (Link to Text)

```bash
pip install selenium webdriver-manager
```

### Lỗi: "Chrome not found" (Link to Text)

1. Cài đặt Google Chrome
2. Webdriver sẽ tự động tải khi chạy

### Lỗi: "faster-whisper not found" (Video to Text)

```bash
# Windows (NVIDIA GPU)
pip install faster-whisper
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# macOS
pip install mlx-whisper  # Apple Silicon
pip install faster-whisper  # Intel
```

### Lỗi: "ffmpeg not found"

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Lỗi: Database locked

```bash
# Đóng tất cả instance của app
# Xóa database (sẽ mất dữ liệu)

# Windows
del "%USERPROFILE%\.anhmin_audio\database.db"

# macOS / Linux
rm ~/.anhmin_audio/database.db
```

---

## ❓ FAQ

### 1. API key lấy ở đâu?

1. Truy cập https://console.anthropic.com/
2. Đăng nhập/Tạo tài khoản
3. Vào **Settings** → **API Keys**
4. Click **Create Key**

### 2. Chi phí sử dụng Claude API?

| Model | Input | Output |
|-------|-------|--------|
| Claude Sonnet | $3/1M tokens | $15/1M tokens |
| Claude Opus | $15/1M tokens | $75/1M tokens |
| Claude Haiku | $0.25/1M tokens | $1.25/1M tokens |

**Ước tính:**
- 1 chương (~3000 từ): ~500-1000 VND
- 10 chương: ~5,000-10,000 VND

### 3. Dữ liệu lưu ở đâu?

```
Windows: %USERPROFILE%\.anhmin_audio\
macOS/Linux: ~/.anhmin_audio/

Bao gồm:
- database.db: Dự án, chat, memory, glossary
- projects/: Files đã upload
```

### 4. Có thể chạy offline không?

| Tính năng | Offline |
|-----------|---------|
| Giao diện app | ✅ Có |
| Whisper (Video to Text) | ✅ Có (sau khi tải model) |
| Claude AI | ❌ Không |
| Link to Text | ❌ Không |

### 5. Tốc độ xử lý Video to Text?

| Thiết bị | Model | Tốc độ |
|----------|-------|--------|
| RTX 4060 | large-v3 | ~2-3 phút/10 phút video |
| Mac M2 | large-v3 | ~4-5 phút/10 phút video |
| CPU Intel i7 | large-v3 | ~20-30 phút/10 phút video |

### 6. Tốc độ xử lý Link to Text?

| Website | Phương pháp | Tốc độ |
|---------|-------------|--------|
| piaotia.com | Scrape HTML | ~1 giây/chương |
| truyenphuongdong.com | Selenium | ~3-5 giây/chương |

### 7. Làm sao để backup dữ liệu?

Copy toàn bộ thư mục:
```
Windows: %USERPROFILE%\.anhmin_audio\
macOS/Linux: ~/.anhmin_audio/
```

---

## 📝 Changelog

### Version 8.0 (Hiện tại)
- ✅ Thêm tab **🔗 Link to Text**
- ✅ Hỗ trợ truyenphuongdong.com, piaotia.com, và 5 website khác
- ✅ Selenium cho website SPA
- ✅ BeautifulSoup cho website static

### Version 7.0
- ✅ Thêm tab **🎬 Video to Text**
- ✅ Hỗ trợ Windows (CUDA), macOS (MLX)
- ✅ Quản lý model Whisper

### Version 6.0
- ✅ Thêm **Template Prompt**
- ✅ Thêm tab **📚 Thuật ngữ (Glossary)**
- ✅ Cải thiện UI nút xóa

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:

1. Kiểm tra phiên bản Python: `python --version`
2. Kiểm tra thư viện: `pip list`
3. Chạy với debug: `python main.py --debug`
4. Đọc log trong terminal/console

---

*Cập nhật lần cuối: Tháng 12, 2024*
