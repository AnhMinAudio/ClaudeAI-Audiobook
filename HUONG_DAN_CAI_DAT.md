# 📚 HƯỚNG DẪN CÀI ĐẶT ANHMIN AUDIO

## Mục lục
1. [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
2. [Cài đặt cơ bản](#-cài-đặt-cơ-bản)
3. [Cài đặt Video to Text](#-cài-đặt-video-to-text)
4. [Cấu hình API Key](#-cấu-hình-api-key)
5. [Khắc phục lỗi thường gặp](#-khắc-phục-lỗi-thường-gặp)
6. [Câu hỏi thường gặp](#-câu-hỏi-thường-gặp)

---

## 💻 Yêu cầu hệ thống

### Yêu cầu tối thiểu

| Thành phần | Yêu cầu |
|------------|---------|
| **Hệ điều hành** | Windows 10/11, macOS 11+, Linux Ubuntu 20.04+ |
| **Python** | 3.9 trở lên |
| **RAM** | 8GB (16GB khuyến nghị cho Video to Text) |
| **Ổ cứng** | 5GB trống (thêm 3GB cho mỗi model Whisper) |

### Yêu cầu cho Video to Text

| Hệ điều hành | GPU | Thư viện Whisper | Tốc độ |
|--------------|-----|------------------|--------|
| Windows | NVIDIA (CUDA) | faster-whisper | ⚡ Rất nhanh |
| Windows | Không có | faster-whisper | 🐢 Chậm |
| macOS M1/M2/M3 | Apple Silicon | mlx-whisper | ⚡ Nhanh |
| macOS Intel | Không có | faster-whisper | 🐢 Chậm |
| Linux | NVIDIA (CUDA) | faster-whisper | ⚡ Rất nhanh |

---

## 🛠 Cài đặt cơ bản

### Bước 1: Cài đặt Python

#### Windows
1. Tải Python từ https://www.python.org/downloads/
2. Chạy installer, **QUAN TRỌNG**: Tick ✅ "Add Python to PATH"
3. Mở Command Prompt, kiểm tra: `python --version`

#### macOS
```bash
# Dùng Homebrew
brew install python@3.11

# Kiểm tra
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Bước 2: Tạo môi trường ảo (khuyến nghị)

```bash
# Windows
python -m venv anhmin_env
anhmin_env\Scripts\activate

# macOS / Linux
python3 -m venv anhmin_env
source anhmin_env/bin/activate
```

### Bước 3: Cài đặt thư viện chính

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
```
pip install selenium webdriver-manager

pip install undetected-chromedriver

### Bước 4: Chạy ứng dụng

```bash
# Windows
python main.py

# macOS / Linux
python3 main.py
```

---

## 🎬 Cài đặt Video to Text

### WINDOWS (NVIDIA GPU) ⚡

#### Bước 1: Kiểm tra GPU
```bash
# Mở PowerShell hoặc Command Prompt
nvidia-smi
```

Nếu thấy thông tin GPU → Tiếp tục. Nếu không → Xem phần "Windows không có GPU".

#### Bước 2: Cài đặt CUDA Toolkit
1. Tải CUDA Toolkit 12.1 từ https://developer.nvidia.com/cuda-downloads
2. Cài đặt theo hướng dẫn
3. Khởi động lại máy

#### Bước 3: Cài đặt thư viện

```bash
# PyTorch với CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Whisper và YouTube downloader
pip install faster-whisper yt-dlp
```

#### Bước 4: Cài đặt FFmpeg

```bash
# Mở PowerShell với quyền Admin
winget install ffmpeg

# Hoặc tải từ: https://www.gyan.dev/ffmpeg/builds/
# Giải nén và thêm thư mục bin vào PATH
```

#### Bước 5: Kiểm tra cài đặt

```bash
# Kiểm tra FFmpeg
ffmpeg -version

# Kiểm tra Whisper
python -c "from faster_whisper import WhisperModel; print('OK')"

# Kiểm tra CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

---

### WINDOWS (Không có GPU) 🐢

```bash
# Whisper và YouTube downloader
pip install faster-whisper yt-dlp

# FFmpeg
winget install ffmpeg
```

**Lưu ý:** Chế độ CPU sẽ chậm hơn nhiều. Video 10 phút có thể mất 15-25 phút.

---

### macOS (Apple Silicon M1/M2/M3) ⚡

#### Bước 1: Cài đặt Homebrew (nếu chưa có)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Bước 2: Cài đặt FFmpeg

```bash
brew install ffmpeg
```

#### Bước 3: Cài đặt thư viện

```bash
# MLX Whisper (tối ưu cho Apple Silicon)
pip install mlx-whisper yt-dlp
```

#### Bước 4: Kiểm tra

```bash
ffmpeg -version
python3 -c "import mlx_whisper; print('OK')"
```

---

### macOS (Intel) 🐢

```bash
# FFmpeg
brew install ffmpeg

# Whisper (chạy CPU)
pip install faster-whisper yt-dlp
```

---

### Linux (NVIDIA GPU) ⚡

```bash
# FFmpeg
sudo apt install ffmpeg

# CUDA (nếu chưa có)
# Tham khảo: https://developer.nvidia.com/cuda-downloads

# PyTorch với CUDA
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Whisper
pip install faster-whisper yt-dlp
```

---

## 🔑 Cấu hình API Key

### Lấy API Key từ Anthropic

1. Truy cập https://console.anthropic.com/
2. Đăng nhập hoặc tạo tài khoản
3. Vào **Settings** → **API Keys**
4. Click **Create Key**
5. Đặt tên và copy key

### Thêm API Key vào ứng dụng

1. Mở AnhMin Audio
2. Click **⚙️ Settings** ở góc trái dưới
3. Nhập tên key (ví dụ: "Main Key")
4. Dán API Key
5. Click **➕ Thêm**

### Quản lý nhiều API Key

- Có thể thêm nhiều key để backup
- Key với priority cao hơn sẽ được dùng trước
- Khi key lỗi 3 lần, tự động chuyển sang key khác

---

## 🔧 Khắc phục lỗi thường gặp

### Lỗi: "ModuleNotFoundError: No module named 'PyQt6'"

```bash
pip install PyQt6 PyQt6-Qt6
```

### Lỗi: "No CUDA runtime is found"

```bash
# Kiểm tra NVIDIA driver
nvidia-smi

# Nếu không có output → Cài đặt NVIDIA driver
# Tải từ: https://www.nvidia.com/Download/index.aspx

# Cài lại PyTorch
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Lỗi: "ffmpeg not found"

#### Windows
```bash
# Kiểm tra PATH
echo %PATH%

# Thêm FFmpeg vào PATH:
# 1. Tải FFmpeg từ https://www.gyan.dev/ffmpeg/builds/
# 2. Giải nén vào C:\ffmpeg
# 3. Thêm C:\ffmpeg\bin vào System PATH
# 4. Khởi động lại Command Prompt
```

#### macOS
```bash
brew install ffmpeg
```

### Lỗi: "large-v3 model not loading"

```bash
# Xóa cache model cũ
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface" -ErrorAction SilentlyContinue

# macOS / Linux
rm -rf ~/.cache/huggingface

# Cập nhật thư viện
pip install -U faster-whisper

# Thử lại hoặc dùng large-v2
```

### Lỗi: "yt-dlp: ERROR: unable to download"

```bash
# Cập nhật yt-dlp
pip install -U yt-dlp

# Nếu vẫn lỗi, có thể YouTube đã thay đổi
# Kiểm tra issues: https://github.com/yt-dlp/yt-dlp/issues
```

### Lỗi: Database locked

```bash
# Đóng tất cả instance của app
# Xóa database cũ (sẽ mất dữ liệu)

# Windows
del "%USERPROFILE%\.anhmin_audio\database.db"

# macOS / Linux
rm ~/.anhmin_audio/database.db
```

---

## ❓ Câu hỏi thường gặp

### 1. Model Whisper lưu ở đâu?

| Hệ điều hành | Đường dẫn |
|--------------|-----------|
| Windows | `C:\Users\<tên>\.cache\huggingface\hub\` |
| macOS | `~/.cache/huggingface/hub/` |
| Linux | `~/.cache/huggingface/hub/` |

### 2. Cách tải model Whisper?

**Ứng dụng KHÔNG tự động tải model.** Bạn cần chủ động tải:

1. Mở tab **🎬 Video to Text**
2. Chọn model trong dropdown (ví dụ: Large V3)
3. Nếu model chưa tải, nút bên cạnh sẽ hiện **"⬇️ Tải về"**
4. Click nút để tải model
5. Sau khi tải xong, nút sẽ hiện **"✅ Đã tải"**

### 3. Dung lượng các model Whisper?

| Model | Dung lượng | VRAM cần | Độ chính xác |
|-------|------------|----------|--------------|
| tiny | 75 MB | ~1 GB | ⭐⭐ |
| base | 145 MB | ~1 GB | ⭐⭐⭐ |
| small | 488 MB | ~2 GB | ⭐⭐⭐ |
| medium | 1.5 GB | ~5 GB | ⭐⭐⭐⭐ |
| large-v2 | 3.1 GB | ~10 GB | ⭐⭐⭐⭐⭐ |
| large-v3 | 3.1 GB | ~10 GB | ⭐⭐⭐⭐⭐ |

### 3. Tốc độ xử lý video 10 phút?

| Thiết bị | Model | Thời gian |
|----------|-------|-----------|
| RTX 4060 | large-v3 | ~2-3 phút |
| RTX 3060 | large-v3 | ~3-4 phút |
| Mac M2 | large-v3 | ~4-5 phút |
| CPU Intel i7 | large-v3 | ~20-30 phút |
| CPU Intel i7 | medium | ~10-15 phút |

### 4. Chi phí Claude API?

| Thao tác | Chi phí ước tính |
|----------|------------------|
| Sửa lỗi 10 phút audio | ~250 VND |
| Viết lại 1 chương (~3000 từ) | ~500-1000 VND |
| Xử lý 1 giờ audio | ~1,500 VND |

### 5. Có thể chạy offline không?

| Tính năng | Offline |
|-----------|---------|
| Whisper (Video to Text) | ✅ Có (sau khi tải model) |
| Claude AI | ❌ Không (cần internet) |
| YouTube download | ❌ Không (cần internet) |

### 6. Làm sao để cập nhật ứng dụng?

```bash
# Tải phiên bản mới
# Giải nén đè lên thư mục cũ
# Dữ liệu được lưu trong ~/.anhmin_audio/ nên không mất
```

### 7. Backup dữ liệu ở đâu?

```bash
# Toàn bộ dữ liệu trong thư mục:
# Windows: %USERPROFILE%\.anhmin_audio\
# macOS/Linux: ~/.anhmin_audio/

# Bao gồm:
# - database.db (projects, chats, memory, glossary...)
# - projects/ (files đã upload)
```

---

## 📋 Tổng hợp lệnh cài đặt

### Windows (NVIDIA GPU) - Copy/Paste

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install faster-whisper yt-dlp
winget install ffmpeg
```

### Windows (Không GPU) - Copy/Paste

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
pip install faster-whisper yt-dlp
winget install ffmpeg
```

### macOS (Apple Silicon) - Copy/Paste

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
pip install mlx-whisper yt-dlp
brew install ffmpeg
```

### macOS (Intel) - Copy/Paste

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
pip install faster-whisper yt-dlp
brew install ffmpeg
```

### Linux (NVIDIA GPU) - Copy/Paste

```bash
pip install PyQt6 anthropic python-docx docx2txt keyring
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install faster-whisper yt-dlp
sudo apt install ffmpeg
```

---

## 📞 Hỗ trợ

Nếu gặp vấn đề không có trong hướng dẫn này:

1. Kiểm tra phiên bản Python: `python --version`
2. Kiểm tra các thư viện đã cài: `pip list`
3. Chạy app với debug: `python main.py --debug`
4. Ghi lại lỗi và liên hệ hỗ trợ

---

## 📝 Changelog

### Version 7 (Hiện tại)
- ✅ Thêm tab Video to Text
- ✅ Hỗ trợ Windows (CUDA), macOS (MLX), Linux
- ✅ Tự động nhận diện GPU/CPU
- ✅ Hỗ trợ large-v3 model
- ✅ Thêm Template Prompt
- ✅ Thêm Glossary (Thuật ngữ)
- ✅ Cải thiện UI nút xóa

---

*Cập nhật lần cuối: Tháng 12, 2024*
