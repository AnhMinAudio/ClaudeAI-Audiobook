# Hướng Dẫn Setup GitHub cho Auto-Update

Tài liệu này hướng dẫn chi tiết cách thiết lập GitHub repository để sử dụng tính năng tự động cập nhật trong AnhMin Audio.

## 📋 Mục Lục

1. [Tạo Tài Khoản GitHub](#1-tạo-tài-khoản-github)
2. [Tạo Repository](#2-tạo-repository)
3. [Cài Đặt Git](#3-cài-đặt-git)
4. [Upload Code Lên GitHub](#4-upload-code-lên-github)
5. [Cập Nhật Config](#5-cập-nhật-config)
6. [Tạo Release Đầu Tiên](#6-tạo-release-đầu-tiên)
7. [Test Auto-Update](#7-test-auto-update)
8. [Phát Hành Bản Cập Nhật Mới](#8-phát-hành-bản-cập-nhật-mới)

---

## 1. Tạo Tài Khoản GitHub

### Bước 1.1: Đăng ký tài khoản

1. Truy cập: https://github.com/signup
2. Nhập email của bạn
3. Tạo mật khẩu (tối thiểu 8 ký tự)
4. Chọn username (tên người dùng duy nhất)
5. Xác minh bằng puzzle
6. Nhấn **Create account**
7. Xác minh email (check hộp thư)

### Bước 1.2: Hoàn tất thiết lập

1. Chọn **Free** plan (miễn phí)
2. Bỏ qua các câu hỏi khảo sát (hoặc trả lời nếu muốn)
3. Nhấn **Complete setup**

✅ **Hoàn tất**: Bạn đã có tài khoản GitHub!

---

## 2. Tạo Repository

### Bước 2.1: Tạo repository mới

1. Đăng nhập vào GitHub
2. Nhấn nút **+** ở góc trên bên phải
3. Chọn **New repository**

### Bước 2.2: Cấu hình repository

Điền các thông tin sau:

| Trường | Giá trị | Ghi chú |
|--------|---------|---------|
| **Repository name** | `anhmin-audio` | Tên repository (không dấu, không khoảng trắng) |
| **Description** | `AnhMin Audio - Claude AI Audiobook Manager` | Mô tả ngắn (tùy chọn) |
| **Public/Private** | **Public** | Chọn Public để dùng GitHub Releases miễn phí |
| **Initialize repository** | ❌ **KHÔNG TICK** | Để trống (chúng ta sẽ push code sẵn có) |

### Bước 2.3: Tạo repository

1. Nhấn **Create repository**
2. **Lưu lại URL**: https://github.com/YOUR_USERNAME/anhmin-audio
   - Thay `YOUR_USERNAME` bằng username GitHub của bạn

✅ **Hoàn tất**: Repository đã được tạo!

---

## 3. Cài Đặt Git

### Windows

**Cách 1: Dùng winget (khuyến nghị)**
```bash
winget install Git.Git
```

**Cách 2: Tải về thủ công**
1. Truy cập: https://git-scm.com/download/win
2. Tải file installer (.exe)
3. Chạy installer, nhấn Next → Next → Install
4. Sau khi cài xong, mở lại terminal mới

### macOS

**Cách 1: Dùng Homebrew**
```bash
brew install git
```

**Cách 2: Xcode Command Line Tools**
```bash
xcode-select --install
```

### Linux

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git
```

**Fedora:**
```bash
sudo dnf install git
```

### Kiểm tra cài đặt

```bash
git --version
```

Nếu hiển thị version (ví dụ: `git version 2.43.0`), Git đã được cài đặt thành công.

### Cấu hình Git (lần đầu)

```bash
git config --global user.name "Tên Của Bạn"
git config --global user.email "email@example.com"
```

✅ **Hoàn tất**: Git đã sẵn sàng!

---

## 4. Upload Code Lên GitHub

### Bước 4.1: Mở terminal tại thư mục dự án

**Windows:**
- Mở File Explorer
- Điều hướng đến: `e:\CodeWeb\anhmin_audio`
- Chuột phải trong thư mục → **Open in Terminal** (hoặc **Git Bash Here**)

**macOS/Linux:**
```bash
cd /path/to/anhmin_audio
```

### Bước 4.2: Khởi tạo Git repository

```bash
git init
```

**Kết quả**: `Initialized empty Git repository in ...`

### Bước 4.3: Thêm tất cả files

```bash
git add .
```

**Giải thích**: Dấu `.` nghĩa là thêm tất cả files trong thư mục.

### Bước 4.4: Tạo commit đầu tiên

```bash
git commit -m "Initial commit - v1.0.0"
```

**Kết quả**: Hiển thị số lượng files được commit.

### Bước 4.5: Đổi tên branch thành main

```bash
git branch -M main
```

### Bước 4.6: Kết nối với GitHub repository

```bash
git remote add origin https://github.com/YOUR_USERNAME/anhmin-audio.git
```

⚠️ **Thay `YOUR_USERNAME`** bằng username GitHub thực tế của bạn!

**Ví dụ**:
```bash
git remote add origin https://github.com/phamdung2209/anhmin-audio.git
```

### Bước 4.7: Push code lên GitHub

```bash
git push -u origin main
```

**Yêu cầu đăng nhập**:
- Username: `your_github_username`
- Password: **Không phải mật khẩu tài khoản**, mà là **Personal Access Token**

#### Tạo Personal Access Token

1. Vào: https://github.com/settings/tokens
2. Nhấn **Generate new token** → **Generate new token (classic)**
3. Điền thông tin:
   - **Note**: `AnhMin Audio Upload`
   - **Expiration**: `No expiration` (hoặc 1 year)
   - **Scopes**: Tick ✅ **repo** (toàn bộ)
4. Nhấn **Generate token**
5. **Sao chép token** (chỉ hiển thị 1 lần!)
6. Paste vào terminal khi hỏi password

**Lưu token**: Lưu vào file text hoặc password manager để dùng lại sau.

### Bước 4.8: Kiểm tra kết quả

1. Truy cập: https://github.com/YOUR_USERNAME/anhmin-audio
2. Refresh trang
3. Bạn sẽ thấy tất cả files đã được upload

✅ **Hoàn tất**: Code đã lên GitHub!

---

## 5. Cập Nhật Config

### Bước 5.1: Mở file config.py

File: `e:\CodeWeb\anhmin_audio\config.py`

### Bước 5.2: Sửa dòng 16

**Trước:**
```python
GITHUB_OWNER = "YOUR_GITHUB_USERNAME"  # Change this to your GitHub username
```

**Sau:**
```python
GITHUB_OWNER = "phamdung2209"  # Thay bằng username thực tế của bạn
```

### Bước 5.3: Lưu file

### Bước 5.4: Commit và push thay đổi

```bash
git add config.py
git commit -m "Update GitHub owner in config"
git push
```

✅ **Hoàn tất**: Config đã được cập nhật!

---

## 6. Tạo Release Đầu Tiên

### Bước 6.1: Build ứng dụng

```bash
python build.py
```

**Kết quả**: Thư mục `dist/AnhMinAudio/` chứa:
- `AnhMinAudio.exe` - File chính (~10 MB)
- `_internal/` - Folder chứa dependencies (~3.8 GB)

⚠️ **LƯU Ý**: File `.exe` **KHÔNG THỂ** chạy độc lập, phải có folder `_internal/` cùng cấp!

**Kích thước tổng**: ~3.9 GB

### Bước 6.2: Nén folder (BẮT BUỘC)

⚠️ **BẮT BUỘC phải nén** vì auto-update yêu cầu file .zip:
- Giảm kích thước: 3.9 GB → ~1.5 GB
- Dễ upload lên GitHub
- Auto-update tự động giải nén

**Cách nén:**

**Windows:**
1. Vào thư mục `dist/`
2. Chuột phải folder `AnhMinAudio`
3. Chọn **Send to** → **Compressed (zipped) folder**
4. Đặt tên: `AnhMinAudio-v1.0.0-Windows.zip`

**macOS/Linux:**
```bash
cd dist/
zip -r AnhMinAudio-v1.0.0-Windows.zip AnhMinAudio/
```

### Bước 6.3: Tạo Release trên GitHub

1. Vào repository: https://github.com/YOUR_USERNAME/anhmin-audio
2. Nhấn **Releases** (bên phải, dưới About)
3. Nhấn **Create a new release**

### Bước 6.4: Điền thông tin Release

| Trường | Giá trị | Ghi chú |
|--------|---------|---------|
| **Choose a tag** | `v1.0.0` | Nhập và chọn **Create new tag: v1.0.0 on publish** |
| **Release title** | `AnhMin Audio v1.0.0` | Tiêu đề hiển thị |
| **Describe this release** | Xem bên dưới | Mô tả changelog |

**Mẫu mô tả**:
```markdown
## AnhMin Audio v1.0.0 - Phiên bản đầu tiên 🎉

### ✨ Tính năng chính:

- 💬 Chat với Claude AI
- 📝 Quản lý Instructions theo dự án
- 📁 Upload và quản lý files
- 🧠 Project Memory tự động
- 📦 Batch API (giảm 50% chi phí)
- 📚 Quản lý Thuật ngữ (Glossary)
- 🎬 Video to Text (Whisper)
- 🔗 Link to Text (Web scraping)
- 🔄 Auto-update từ GitHub

### 📥 Cài đặt:

1. Tải file `AnhMinAudio.exe` (hoặc file .zip)
2. Giải nén (nếu là .zip)
3. Chạy `AnhMinAudio.exe`
4. Cấu hình API key trong Settings

### 📝 Yêu cầu hệ thống:

- Windows 10/11
- Không cần cài Python
- Kết nối internet (cho Claude API)

---

🔗 **GitHub**: https://github.com/YOUR_USERNAME/anhmin-audio
```

### Bước 6.5: Upload file

⚠️ **LƯU Ý**: Nếu file .zip > 2GB, GitHub KHÔNG cho upload trực tiếp!

#### **Option A: File < 2GB** (Upload trực tiếp GitHub)

1. Kéo thả file `AnhMinAudio-v1.0.0.zip` vào vùng **Attach binaries**
2. Đợi upload hoàn tất (hiển thị checkmark ✓)

#### **Option B: File > 2GB** (Upload qua Google Drive) ⭐

**Bước 1: Upload lên Google Drive**

1. Vào: https://drive.google.com
2. Tạo folder mới: `AnhMin Audio Releases`
3. Upload file `AnhMinAudio-v1.0.0.zip` vào folder
4. Chuột phải file → **Get link** → Chọn **Anyone with the link**
5. Copy link (dạng: `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`)

**Bước 2: Chuyển thành Direct Download Link**

Link gốc:
```
https://drive.google.com/file/d/1A2b3C4d5E6f7G8h9I0j/view?usp=sharing
```

**Lấy FILE_ID** (phần giữa `/d/` và `/view`): `1A2b3C4d5E6f7G8h9I0j`

Chuyển thành direct link (với `&confirm=t` để bypass virus scan warning):
```
https://drive.google.com/uc?export=download&id=1A2b3C4d5E6f7G8h9I0j&confirm=t
```

⚠️ **QUAN TRỌNG**: Phải thêm `&confirm=t` ở cuối link để tải file lớn!

**Bước 3: Tạo file download_link.txt**

Tạo file `download_link.txt` với nội dung:
```
https://drive.google.com/uc?export=download&id=1A2b3C4d5E6f7G8h9I0j&confirm=t
```

(Thay `FILE_ID` bằng ID thật của bạn)

**Bước 4: Upload file .txt lên GitHub Release**

1. Kéo thả file `download_link.txt` vào vùng **Attach binaries**
2. App sẽ tự động đọc link từ file này để download

**Bước 5: Cập nhật Description**

Thêm link download trong phần Description:

```markdown
## 📥 Download

⚠️ **File lớn (>2GB)**, tải về từ Google Drive:

👉 [AnhMinAudio-v1.0.0.zip](https://drive.google.com/uc?export=download&id=FILE_ID)

### Cài đặt:
1. Tải file .zip từ link trên
2. Giải nén
3. Chạy `AnhMinAudio.exe`
```

### Bước 6.6: Publish Release

1. Kiểm tra lại thông tin
2. Nhấn **Publish release**

✅ **Hoàn tất**: Release v1.0.0 đã được tạo!

**URL Release**: https://github.com/YOUR_USERNAME/anhmin-audio/releases/tag/v1.0.0

---

## 7. Test Auto-Update

### Bước 7.1: Chạy app v1.0.0

1. Chạy file `AnhMinAudio.exe` (đã build)
2. App sẽ tự động kiểm tra update khi khởi động

**Kết quả mong đợi**:
- ✅ **KHÔNG** có chấm đỏ bên cạnh "🔄 Cập nhật" (vì đang chạy version mới nhất)

### Bước 7.2: Tạo Release v1.0.1 (để test)

1. Sửa file `config.py` dòng 11:
   ```python
   APP_VERSION = "1.0.1"
   ```

2. Build lại:
   ```bash
   python build.py
   ```

3. Tạo Release mới trên GitHub:
   - Tag: `v1.0.1`
   - Title: `AnhMin Audio v1.0.1`
   - Description: `Test update - Added new features`
   - Upload file .exe mới

### Bước 7.3: Test update flow

1. Chạy app v1.0.0 (bản cũ)
2. Đợi 5-10 giây (app đang check update ở background)
3. **Chấm đỏ xuất hiện** bên cạnh "🔄 Cập nhật" ✅
4. Click nút "🔄 Cập nhật"
5. Dialog hiển thị:
   - Version mới: `v1.0.1`
   - Kích thước file
   - Changelog
6. Click **Tải về**
7. Progress bar chạy (0% → 100%)
8. Click **OK** khi hỏi cài đặt
9. UAC popup yêu cầu quyền admin → Nhấn **Yes**
10. App tự động đóng và khởi động lại

### Bước 7.4: Kiểm tra sau update

1. App khởi động lại
2. Kiểm tra title bar: `AnhMin Audio v1.0.1` ✅
3. Kiểm tra data: Projects, chats vẫn còn nguyên ✅
4. Chấm đỏ đã biến mất (không còn update mới) ✅

✅ **Hoàn tất**: Auto-update hoạt động!

---

## 8. Phát Hành Bản Cập Nhật Mới

### Khi nào nên tạo bản update?

- ✅ Thêm tính năng mới
- ✅ Sửa bug quan trọng
- ✅ Cải thiện performance
- ✅ Cập nhật UI/UX
- ❌ Sửa lỗi chính tả nhỏ (không cần thiết)
- ❌ Thay đổi code nội bộ không ảnh hưởng user

### Quy tắc đánh version

**Semantic Versioning**: `MAJOR.MINOR.PATCH`

| Loại thay đổi | Version | Ví dụ |
|---------------|---------|-------|
| **Breaking changes** (không tương thích ngược) | `MAJOR` | 1.0.0 → **2.0.0** |
| **Thêm tính năng mới** (tương thích ngược) | `MINOR` | 1.0.0 → 1.**1**.0 |
| **Sửa bug** (tương thích ngược) | `PATCH` | 1.0.0 → 1.0.**1** |

**Ví dụ**:
- `1.0.0` → `1.0.1`: Sửa bug chat widget
- `1.0.1` → `1.1.0`: Thêm tính năng Export PDF
- `1.1.0` → `2.0.0`: Đổi database schema (breaking change)

### Các bước phát hành update

#### Bước 1: Cập nhật version trong code

Sửa file `config.py`:
```python
APP_VERSION = "1.1.0"  # Thay đổi từ 1.0.0
```

#### Bước 2: Commit code changes

```bash
git add .
git commit -m "Release v1.1.0: Add PDF export feature"
git push
```

#### Bước 3: Build và nén ứng dụng

```bash
# Build
python build.py

# Nén thành .zip
cd dist/
# Windows: Chuột phải folder AnhMinAudio → Send to → Compressed folder
# Đổi tên thành: AnhMinAudio-v1.1.0.zip
```

⚠️ **Nhớ**: Đổi tên file .zip theo version mới (v1.1.0)

#### Bước 4: Tạo Release trên GitHub

1. Vào: https://github.com/YOUR_USERNAME/anhmin-audio/releases
2. Nhấn **Draft a new release**
3. Tag: `v1.1.0`
4. Title: `AnhMin Audio v1.1.0`
5. Description (changelog):

```markdown
## 🆕 Tính năng mới:

- 📄 Xuất nội dung ra PDF
- 🎨 Cải thiện UI/UX cho Chat widget
- ⚡ Tăng tốc độ xử lý batch API

## 🐛 Sửa lỗi:

- Fix lỗi crash khi upload file lớn
- Fix lỗi hiển thị tiếng Việt có dấu

## 🔧 Cải tiến:

- Giảm kích thước ứng dụng từ 4GB xuống 3.5GB
- Cải thiện thời gian khởi động

---

**Full Changelog**: https://github.com/YOUR_USERNAME/anhmin-audio/compare/v1.0.0...v1.1.0
```

6. Upload file:
   - **Nếu < 2GB**: Upload `AnhMinAudio-v1.1.0.zip` trực tiếp vào Assets
   - **Nếu > 2GB**: Upload lên Google Drive, tạo `download_link.txt` (xem Bước 6.5 Option B)

7. Nhấn **Publish release**

⚠️ **Quan trọng**: File > 2GB KHÔNG thể upload trực tiếp lên GitHub, phải dùng Google Drive!

#### Bước 5: Thông báo cho users

**Discord/Telegram/Facebook Group:**
```
📢 AnhMin Audio v1.1.0 đã ra mắt!

🆕 Tính năng mới:
• Xuất PDF
• UI/UX cải tiến
• Batch API nhanh hơn

🔄 Cập nhật:
• Chạy app → Click "🔄 Cập nhật" → Tải về và cài đặt

📥 Tải về trực tiếp:
https://github.com/YOUR_USERNAME/anhmin-audio/releases/tag/v1.1.0
```

✅ **Hoàn tất**: Bản update đã được phát hành!

---

## 🔧 Troubleshooting

### Lỗi: "Permission denied" khi push

**Nguyên nhân**: Token không có quyền hoặc đã hết hạn.

**Giải pháp**:
1. Tạo token mới: https://github.com/settings/tokens
2. Nhập lại khi push

### Lỗi: "Could not resolve host"

**Nguyên nhân**: Không có kết nối internet.

**Giải pháp**:
- Kiểm tra kết nối mạng
- Thử ping: `ping github.com`

### Lỗi: "failed to push some refs"

**Nguyên nhân**: Repository có commits mới hơn.

**Giải pháp**:
```bash
git pull origin main
git push origin main
```

### App không thấy update mới

**Checklist**:
- ✅ Release đã publish (không phải draft)?
- ✅ Tag đúng định dạng `vX.Y.Z`?
- ✅ File .exe đã upload vào Assets?
- ✅ `config.py` có đúng `GITHUB_OWNER`?
- ✅ Có kết nối internet?

**Debug**:
1. Mở Developer Console (nếu có)
2. Kiểm tra log khi click "🔄 Cập nhật"
3. Thử truy cập URL thủ công:
   ```
   https://api.github.com/repos/YOUR_USERNAME/anhmin-audio/releases/latest
   ```

### UAC không xuất hiện khi cài đặt

**Nguyên nhân**: User đã có quyền admin hoặc UAC bị tắt.

**Giải pháp**:
- Không cần làm gì, batch script sẽ chạy bình thường
- App vẫn được cập nhật thành công

---

## 📚 Tài Liệu Tham Khảo

- **GitHub Docs**: https://docs.github.com/en/get-started
- **Git Tutorial**: https://git-scm.com/docs/gittutorial
- **Semantic Versioning**: https://semver.org/
- **GitHub Releases**: https://docs.github.com/en/repositories/releasing-projects-on-github

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra lại các bước trong tài liệu này
2. Xem phần Troubleshooting
3. Mở issue trên GitHub: https://github.com/YOUR_USERNAME/anhmin-audio/issues

---

**Chúc bạn thành công!** 🎉
