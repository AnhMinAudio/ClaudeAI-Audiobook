"""
AnhMin Audio - Video to Text Widget
Convert video/audio to text using Whisper + Claude
"""

import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTextEdit, QComboBox, QRadioButton,
    QButtonGroup, QProgressBar, QFileDialog, QMessageBox,
    QCheckBox, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor

from database import db
from api import claude_client
from api.file_handler import FileHandler
from ui.styles import COLORS

# Check if faster-whisper is available
WHISPER_AVAILABLE = False
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
    
    # Check if CUDA is available
    try:
        import torch
        if torch.cuda.is_available():
            WHISPER_DEVICE = "cuda"
            WHISPER_COMPUTE = "float16"
    except ImportError:
        pass
except ImportError:
    pass

# Check for mlx-whisper on Apple Silicon
MLX_WHISPER_AVAILABLE = False
try:
    import mlx_whisper
    MLX_WHISPER_AVAILABLE = True
except ImportError:
    pass


# Model information
WHISPER_MODELS = {
    "large-v3": {"name": "Large V3", "size": "3.1 GB", "vram": "~10 GB", "accuracy": "⭐⭐⭐⭐⭐"},
    "large-v2": {"name": "Large V2", "size": "3.1 GB", "vram": "~10 GB", "accuracy": "⭐⭐⭐⭐⭐"},
    "medium": {"name": "Medium", "size": "1.5 GB", "vram": "~5 GB", "accuracy": "⭐⭐⭐⭐"},
    "small": {"name": "Small", "size": "488 MB", "vram": "~2 GB", "accuracy": "⭐⭐⭐"},
    "base": {"name": "Base", "size": "145 MB", "vram": "~1 GB", "accuracy": "⭐⭐"},
    "tiny": {"name": "Tiny", "size": "75 MB", "vram": "~1 GB", "accuracy": "⭐"},
}


def get_whisper_cache_dir() -> Path:
    """Get Whisper model cache directory."""
    return Path.home() / ".cache" / "huggingface" / "hub"


def is_model_downloaded(model_name: str) -> bool:
    """Check if a Whisper model is already downloaded."""
    cache_dir = get_whisper_cache_dir()
    
    # faster-whisper model path
    model_dir = cache_dir / f"models--Systran--faster-whisper-{model_name}"
    if model_dir.exists():
        # Check if model files exist
        snapshots = model_dir / "snapshots"
        if snapshots.exists() and any(snapshots.iterdir()):
            return True
    
    # Also check for original whisper format
    model_dir_alt = cache_dir / f"models--openai--whisper-{model_name}"
    if model_dir_alt.exists():
        return True
    
    return False


def get_downloaded_models() -> list:
    """Get list of downloaded model names."""
    return [name for name in WHISPER_MODELS.keys() if is_model_downloaded(name)]


def delete_model(model_name: str) -> bool:
    """Delete a downloaded Whisper model from cache."""
    import shutil
    cache_dir = get_whisper_cache_dir()
    deleted = False

    # Try deleting faster-whisper format
    model_dir = cache_dir / f"models--Systran--faster-whisper-{model_name}"
    if model_dir.exists():
        try:
            shutil.rmtree(model_dir)
            deleted = True
        except Exception as e:
            print(f"Error deleting {model_dir}: {e}")

    # Try deleting original whisper format
    model_dir_alt = cache_dir / f"models--openai--whisper-{model_name}"
    if model_dir_alt.exists():
        try:
            shutil.rmtree(model_dir_alt)
            deleted = True
        except Exception as e:
            print(f"Error deleting {model_dir_alt}: {e}")

    return deleted


class ModelDownloadWorker(QThread):
    """Worker thread for downloading Whisper models."""
    progress = pyqtSignal(str, int)  # message, percent
    finished = pyqtSignal(str)  # model name
    error = pyqtSignal(str)

    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
        self._is_cancelled = False

    def run(self):
        import time

        try:
            # Stage 1: Preparing
            self.progress.emit(f"🔍 Đang chuẩn bị tải model {self.model_name}...", 5)
            time.sleep(0.3)

            if MLX_WHISPER_AVAILABLE and not WHISPER_AVAILABLE:
                # Download MLX model
                import mlx_whisper
                self.progress.emit("🌐 Đang kết nối với Hugging Face...", 15)
                time.sleep(0.5)

                self.progress.emit(f"⬇️ Đang tải model MLX Whisper {self.model_name}...", 25)
                # MLX downloads on first use, so we trigger it
                mlx_whisper.transcribe(
                    "",
                    path_or_hf_repo=f"mlx-community/whisper-{self.model_name}-mlx",
                    language="vi"
                )
                self.progress.emit("📦 Đang giải nén và cài đặt model...", 85)
            else:
                # Download faster-whisper model
                from faster_whisper import WhisperModel
                self.progress.emit("🌐 Đang kết nối với Hugging Face...", 15)
                time.sleep(0.5)

                self.progress.emit(f"⬇️ Đang tải model Faster-Whisper {self.model_name}...", 25)
                time.sleep(0.3)

                # Simulate smooth progress
                for i in range(25, 80, 5):
                    if self._is_cancelled:
                        return
                    self.progress.emit(f"⬇️ Đang tải model... (tùy model có thể mất vài phút)", i)
                    time.sleep(0.5)

                # This will download the model if not present
                model = WhisperModel(
                    self.model_name,
                    device="cpu",  # Use CPU for download to avoid CUDA issues
                    compute_type="int8"
                )

                self.progress.emit("📦 Đang xác thực và cài đặt model...", 90)

                # Clean up
                del model

            self.progress.emit("✅ Hoàn thành!", 100)
            time.sleep(0.3)
            self.finished.emit(self.model_name)

        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """Cancel the download."""
        self._is_cancelled = True

# Check if yt-dlp is available
YTDLP_AVAILABLE = False
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    pass


class DownloadWorker(QThread):
    """Worker thread for downloading YouTube audio."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)  # audio file path
    error = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
    
    def run(self):
        try:
            import yt_dlp
            
            output_path = os.path.join(self.output_dir, "audio.mp3")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(self.output_dir, 'audio.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            self.progress.emit("Đang tải audio từ YouTube...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            # Find the output file
            for f in os.listdir(self.output_dir):
                if f.startswith("audio") and f.endswith(".mp3"):
                    output_path = os.path.join(self.output_dir, f)
                    break
            
            self.finished.emit(output_path)
            
        except Exception as e:
            self.error.emit(str(e))


class WhisperWorker(QThread):
    """Worker thread for Whisper transcription."""
    progress = pyqtSignal(str, int)  # message, percent
    finished = pyqtSignal(str, list)  # transcribed text, segments data
    error = pyqtSignal(str)

    def __init__(self, audio_path: str, model_name: str = "large-v3",
                 language: str = "vi", preprocess: bool = True,
                 use_mlx: bool = False, keep_timestamps: bool = True):
        super().__init__()
        self.audio_path = audio_path
        self.model_name = model_name
        self.language = language
        self.preprocess = preprocess
        self.use_mlx = use_mlx
        self.keep_timestamps = keep_timestamps
        self._stop_progress_simulation = False
    
    def run(self):
        try:
            # Preprocess audio if needed
            processed_path = self.audio_path
            if self.preprocess:
                self.progress.emit("Đang xử lý audio...", 10)
                processed_path = self.preprocess_audio(self.audio_path)
            
            # Check which backend to use
            if self.use_mlx and MLX_WHISPER_AVAILABLE:
                self.run_mlx_whisper(processed_path)
            else:
                self.run_faster_whisper(processed_path)
            
            # Cleanup
            if processed_path != self.audio_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def run_faster_whisper(self, audio_path: str):
        """Run transcription with faster-whisper."""
        from faster_whisper import WhisperModel
        import time
        import threading

        # Load model with appropriate device
        device_info = f"{WHISPER_DEVICE} ({WHISPER_COMPUTE})"
        self.progress.emit(f"Đang tải model {self.model_name} trên {device_info}...", 20)

        model = WhisperModel(
            self.model_name,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE
        )

        # Start smooth progress simulation
        self.progress.emit("Đang chuyển đổi thành text...", 30)
        self._stop_progress_simulation = False

        def simulate_progress():
            """Simulate smooth progress from 30% to 85%"""
            current = 30
            target = 85
            step = 1
            delay = 0.8  # seconds between updates

            while current < target and not self._stop_progress_simulation:
                time.sleep(delay)
                if self._stop_progress_simulation:
                    break

                current += step
                # Slow down as we approach target
                if current > 70:
                    delay = 1.5
                    step = 0.5
                elif current > 60:
                    delay = 1.2

                self.progress.emit("Đang chuyển đổi thành text...", int(current))

        # Start simulation thread
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()

        # Transcribe (this is the blocking call that takes most time)
        segments, info = model.transcribe(
            audio_path,
            language=self.language,
            beam_size=5,
            best_of=5,
            vad_filter=True,
        )

        # Stop simulation and jump to 90%
        self._stop_progress_simulation = True
        progress_thread.join(timeout=0.5)
        self.progress.emit("Đang xử lý kết quả...", 90)

        # Collect results
        result_lines = []
        segments_data = []
        segment_list = list(segments)
        total_segments = len(segment_list)

        for i, segment in enumerate(segment_list):
            text = segment.text.strip()

            # Save segment data for SRT export
            segments_data.append({
                'start': segment.start,
                'end': segment.end,
                'text': text
            })

            # Format text with or without timestamps
            if self.keep_timestamps:
                start_time = self.format_time(segment.start)
                result_lines.append(f"[{start_time}] {text}")
            else:
                result_lines.append(text)

            # Progress from 90% to 100%
            progress = 90 + int((i + 1) / total_segments * 10)
            self.progress.emit(f"Đang xử lý segment {i+1}/{total_segments}...", progress)

        self.progress.emit("Hoàn thành!", 100)
        self.finished.emit("\n".join(result_lines), segments_data)
    
    def run_mlx_whisper(self, audio_path: str):
        """Run transcription with mlx-whisper (Apple Silicon)."""
        import mlx_whisper
        import time
        import threading

        self.progress.emit(f"Đang tải model {self.model_name} (MLX)...", 20)

        # Start smooth progress simulation
        self.progress.emit("Đang chuyển đổi thành text...", 30)
        self._stop_progress_simulation = False

        def simulate_progress():
            """Simulate smooth progress from 30% to 85%"""
            current = 30
            target = 85
            step = 1
            delay = 0.8  # seconds between updates

            while current < target and not self._stop_progress_simulation:
                time.sleep(delay)
                if self._stop_progress_simulation:
                    break

                current += step
                # Slow down as we approach target
                if current > 70:
                    delay = 1.5
                    step = 0.5
                elif current > 60:
                    delay = 1.2

                self.progress.emit("Đang chuyển đổi thành text...", int(current))

        # Start simulation thread
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()

        # Transcribe (this is the blocking call that takes most time)
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=f"mlx-community/whisper-{self.model_name}-mlx",
            language=self.language,
        )

        # Stop simulation and jump to 90%
        self._stop_progress_simulation = True
        progress_thread.join(timeout=0.5)
        self.progress.emit("Đang xử lý kết quả...", 90)

        # Format results
        result_lines = []
        segments_data = []
        segments = result.get("segments", [])

        for i, segment in enumerate(segments):
            text = segment["text"].strip()

            # Save segment data for SRT export
            segments_data.append({
                'start': segment["start"],
                'end': segment["end"],
                'text': text
            })

            # Format text with or without timestamps
            if self.keep_timestamps:
                start_time = self.format_time(segment["start"])
                result_lines.append(f"[{start_time}] {text}")
            else:
                result_lines.append(text)

            # Progress from 90% to 100%
            progress = 90 + int((i + 1) / len(segments) * 10)
            self.progress.emit(f"Đang xử lý segment {i+1}/{len(segments)}...", progress)

        self.progress.emit("Hoàn thành!", 100)
        self.finished.emit("\n".join(result_lines), segments_data)
    
    def preprocess_audio(self, input_path: str) -> str:
        """Preprocess audio: noise reduction, normalization."""
        output_path = input_path.rsplit(".", 1)[0] + "_processed.wav"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", "highpass=f=200,lowpass=f=3000,loudnorm",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    
    def format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


class ClaudeProcessWorker(QThread):
    """Worker thread for Claude processing."""
    progress = pyqtSignal(str)
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, text: str, instructions: str, memory: str, glossary: str):
        super().__init__()
        self.text = text
        self.instructions = instructions
        self.memory = memory
        self.glossary = glossary
    
    def run(self):
        try:
            self.progress.emit("Đang xử lý với Claude...")
            
            # Build system prompt
            system_parts = []
            
            if self.instructions:
                system_parts.append(self.instructions)
            
            if self.glossary:
                system_parts.append(f"\n## Thuật ngữ cần tuân thủ:\n{self.glossary}")
            
            if self.memory:
                system_parts.append(f"\n## Thông tin bổ sung:\n{self.memory}")
            
            system_prompt = "\n\n".join(system_parts) if system_parts else ""
            
            # Build message
            messages = [
                {
                    "role": "user",
                    "content": f"Hãy xử lý nội dung sau theo hướng dẫn:\n\n{self.text}"
                }
            ]
            
            # Stream response
            full_response = ""
            for chunk in claude_client.stream_message(messages, system_prompt):
                full_response += chunk
                self.chunk_received.emit(chunk)
            
            self.finished.emit(full_response)
            
        except Exception as e:
            self.error.emit(str(e))


class VideoToTextWidget(QWidget):
    """Video to Text conversion widget."""
    
    def __init__(self):
        super().__init__()
        self.project_id = None
        self.temp_dir = tempfile.mkdtemp()
        self.audio_path = None
        self.raw_text = ""
        self.processed_text = ""
        self.segments_data = []  # For SRT export

        self.download_worker = None
        self.whisper_worker = None
        self.claude_worker = None
        self.model_download_worker = None
        
        self.setup_ui()
        self.check_dependencies()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🎬 Video to Text")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Dependency status
        self.dep_status = QLabel("")
        self.dep_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        header.addWidget(self.dep_status)
        
        layout.addLayout(header)
        
        # Source section
        source_group = QGroupBox("📥 Nguồn")
        source_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        source_layout = QVBoxLayout(source_group)
        source_layout.setSpacing(12)
        
        # URL input
        url_row = QHBoxLayout()
        
        url_label = QLabel("🔗 YouTube URL:")
        url_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        url_row.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/watch?v=... hoặc https://youtu.be/...")
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 12px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)
        url_row.addWidget(self.url_input, 1)
        
        paste_btn = QPushButton("📋")
        paste_btn.setFixedSize(36, 36)
        paste_btn.setToolTip("Dán từ clipboard")
        paste_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        paste_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        paste_btn.clicked.connect(self.paste_url)
        url_row.addWidget(paste_btn)
        
        source_layout.addLayout(url_row)
        
        # Or file
        file_row = QHBoxLayout()
        
        file_label = QLabel("📁 Hoặc file:")
        file_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        file_row.addWidget(file_label)
        
        self.file_path_label = QLabel("Chưa chọn file")
        self.file_path_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        file_row.addWidget(self.file_path_label, 1)
        
        file_btn = QPushButton("📁 Chọn file")
        file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        file_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        file_btn.clicked.connect(self.select_file)
        file_row.addWidget(file_btn)
        
        source_layout.addLayout(file_row)
        
        layout.addWidget(source_group)
        
        # Settings section
        settings_row = QHBoxLayout()
        settings_row.setSpacing(16)
        
        # Whisper settings
        whisper_group = QGroupBox("⚙️ Whisper")
        whisper_group.setStyleSheet(source_group.styleSheet())
        whisper_layout = QVBoxLayout(whisper_group)
        
        model_row = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        model_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(180)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
            }}
        """)
        model_row.addWidget(self.model_combo, 1)
        
        # Download/status button
        self.model_status_btn = QPushButton("✅ Đã tải")
        self.model_status_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']}20;
                color: {COLORS['success']};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success']}30;
            }}
        """)
        self.model_status_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.model_status_btn.clicked.connect(self.on_model_action)
        model_row.addWidget(self.model_status_btn)

        # Delete model button
        self.model_delete_btn = QPushButton("🗑️ Xóa")
        self.model_delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']}20;
                color: {COLORS['error']};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}30;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.model_delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.model_delete_btn.clicked.connect(self.on_delete_model)
        self.model_delete_btn.setEnabled(False)  # Initially disabled
        model_row.addWidget(self.model_delete_btn)
        
        whisper_layout.addLayout(model_row)
        
        # Model info label
        self.model_info_label = QLabel("")
        self.model_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        whisper_layout.addWidget(self.model_info_label)

        # Model download progress (hidden by default)
        self.model_download_progress_frame = QFrame()
        self.model_download_progress_frame.setVisible(False)
        download_progress_layout = QVBoxLayout(self.model_download_progress_frame)
        download_progress_layout.setContentsMargins(0, 8, 0, 8)
        download_progress_layout.setSpacing(4)

        self.model_download_status_label = QLabel("")
        self.model_download_status_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: 500;
        """)
        download_progress_layout.addWidget(self.model_download_status_label)

        self.model_download_progress_bar = QProgressBar()
        self.model_download_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['bg_light']};
                text-align: center;
                color: {COLORS['text_primary']};
                font-size: 10px;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        self.model_download_progress_bar.setMinimum(0)
        self.model_download_progress_bar.setMaximum(100)
        download_progress_layout.addWidget(self.model_download_progress_bar)

        # Cancel button
        self.model_download_cancel_btn = QPushButton("⏹ Hủy tải")
        self.model_download_cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']}20;
                color: {COLORS['error']};
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}30;
            }}
        """)
        self.model_download_cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.model_download_cancel_btn.clicked.connect(self.on_cancel_model_download)
        download_progress_layout.addWidget(self.model_download_cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

        whisper_layout.addWidget(self.model_download_progress_frame)

        # Populate models and update status
        self.populate_models()
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        
        self.preprocess_check = QCheckBox("Lọc nhiễu audio")
        self.preprocess_check.setChecked(True)
        self.preprocess_check.setStyleSheet(f"color: {COLORS['text_primary']};")
        whisper_layout.addWidget(self.preprocess_check)
        
        self.timestamp_check = QCheckBox("Giữ timestamp")
        self.timestamp_check.setChecked(False)
        self.timestamp_check.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.timestamp_check.toggled.connect(self.on_timestamp_toggle)
        whisper_layout.addWidget(self.timestamp_check)
        
        settings_row.addWidget(whisper_group, 1)
        
        # Processing level
        level_group = QGroupBox("🎯 Mức độ xử lý")
        level_group.setStyleSheet(source_group.styleSheet())
        level_layout = QVBoxLayout(level_group)
        
        self.level_group = QButtonGroup(self)
        
        # Style for radio buttons
        radio_style = f"""
            QRadioButton {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 500;
                padding: 4px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {COLORS['border_light']};
                background-color: {COLORS['bg_light']};
            }}
            QRadioButton::indicator:hover {{
                border-color: {COLORS['accent']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
        """

        self.level_whisper = QRadioButton("Chỉ Whisper (miễn phí)")
        self.level_whisper.setStyleSheet(radio_style)
        self.level_whisper.setChecked(True)
        self.level_group.addButton(self.level_whisper, 0)
        level_layout.addWidget(self.level_whisper)

        whisper_desc = QLabel("→ Lấy text thô, lưu file")
        whisper_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        level_layout.addWidget(whisper_desc)

        self.level_claude = QRadioButton("Whisper + Claude (tốn phí)")
        self.level_claude.setStyleSheet(radio_style)
        self.level_group.addButton(self.level_claude, 1)
        level_layout.addWidget(self.level_claude)

        claude_desc = QLabel("→ Viết lại theo Instructions + Memory + Glossary")
        claude_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 28px;")
        level_layout.addWidget(claude_desc)
        
        settings_row.addWidget(level_group, 1)
        
        layout.addLayout(settings_row)
        
        # Start button
        self.start_btn = QPushButton("🚀 Bắt đầu chuyển đổi")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.start_btn)
        
        # Progress
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(16, 12, 16, 12)
        
        self.progress_label = QLabel("Đang xử lý...")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                background-color: {COLORS['bg_lighter']};
                height: 24px;
                text-align: center;
                color: {COLORS['text_primary']};
                font-size: 11px;
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setFormat("%p%")  # Show percentage with % sign
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_frame)
        
        # Results section
        results_label = QLabel("📄 Kết quả")
        results_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']};")
        layout.addWidget(results_label)
        
        # Split view for raw and processed
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
                width: 2px;
            }}
        """)
        
        # Raw text panel
        raw_panel = QFrame()
        raw_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border-radius: 8px;
            }}
        """)
        raw_layout = QVBoxLayout(raw_panel)
        raw_layout.setContentsMargins(12, 12, 12, 12)
        
        raw_header = QHBoxLayout()
        raw_title = QLabel("📄 Raw (Whisper)")
        raw_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        raw_header.addWidget(raw_title)
        raw_header.addStretch()
        
        self.raw_word_count = QLabel("0 từ")
        self.raw_word_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        raw_header.addWidget(self.raw_word_count)
        raw_layout.addLayout(raw_header)
        
        self.raw_text_edit = QTextEdit()
        self.raw_text_edit.setPlaceholderText("Text từ Whisper sẽ hiển thị ở đây...")
        self.raw_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        raw_layout.addWidget(self.raw_text_edit, 1)
        
        splitter.addWidget(raw_panel)
        
        # Processed text panel
        processed_panel = QFrame()
        processed_panel.setStyleSheet(raw_panel.styleSheet())
        processed_layout = QVBoxLayout(processed_panel)
        processed_layout.setContentsMargins(12, 12, 12, 12)
        
        processed_header = QHBoxLayout()
        processed_title = QLabel("✨ Đã xử lý (Claude)")
        processed_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        processed_header.addWidget(processed_title)
        processed_header.addStretch()
        
        self.processed_word_count = QLabel("0 từ")
        self.processed_word_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        processed_header.addWidget(self.processed_word_count)
        processed_layout.addLayout(processed_header)
        
        self.processed_text_edit = QTextEdit()
        self.processed_text_edit.setPlaceholderText("Text đã xử lý bởi Claude sẽ hiển thị ở đây...")
        self.processed_text_edit.setStyleSheet(self.raw_text_edit.styleSheet())
        processed_layout.addWidget(self.processed_text_edit, 1)
        
        splitter.addWidget(processed_panel)
        
        layout.addWidget(splitter, 1)
        
        # Action buttons
        actions_row = QHBoxLayout()
        
        # Add to files checkbox
        self.add_to_files_check = QCheckBox("📁 Thêm vào Files của Project")
        self.add_to_files_check.setStyleSheet(f"color: {COLORS['text_primary']};")
        actions_row.addWidget(self.add_to_files_check)
        
        actions_row.addStretch()
        
        # Continue with Claude button (when only Whisper was selected)
        self.continue_claude_btn = QPushButton("🤖 Tiếp tục xử lý với Claude")
        self.continue_claude_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        self.continue_claude_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.continue_claude_btn.clicked.connect(self.continue_with_claude)
        self.continue_claude_btn.setVisible(False)
        actions_row.addWidget(self.continue_claude_btn)
        
        # Save buttons
        self.save_raw_txt_btn = QPushButton("💾 Lưu Raw (.txt)")
        self.save_raw_txt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_lighter']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
            }}
        """)
        self.save_raw_txt_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_raw_txt_btn.clicked.connect(lambda: self.save_file("raw", "txt"))
        self.save_raw_txt_btn.setEnabled(False)
        actions_row.addWidget(self.save_raw_txt_btn)

        self.save_srt_btn = QPushButton("💾 Lưu Subtitle (.srt)")
        self.save_srt_btn.setStyleSheet(self.save_raw_txt_btn.styleSheet())
        self.save_srt_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_srt_btn.clicked.connect(self.save_srt_file)
        self.save_srt_btn.setEnabled(False)
        self.save_srt_btn.setVisible(False)  # Hidden by default
        actions_row.addWidget(self.save_srt_btn)

        self.save_processed_txt_btn = QPushButton("💾 Lưu Đã xử lý (.txt)")
        self.save_processed_txt_btn.setStyleSheet(self.save_raw_txt_btn.styleSheet())
        self.save_processed_txt_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_processed_txt_btn.clicked.connect(lambda: self.save_file("processed", "txt"))
        self.save_processed_txt_btn.setEnabled(False)
        actions_row.addWidget(self.save_processed_txt_btn)
        
        self.save_processed_docx_btn = QPushButton("📝 Lưu Đã xử lý (.docx)")
        self.save_processed_docx_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        self.save_processed_docx_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_processed_docx_btn.clicked.connect(lambda: self.save_file("processed", "docx"))
        self.save_processed_docx_btn.setEnabled(False)
        actions_row.addWidget(self.save_processed_docx_btn)
        
        layout.addLayout(actions_row)
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        missing = []
        warnings = []
        
        if not WHISPER_AVAILABLE and not MLX_WHISPER_AVAILABLE:
            missing.append("faster-whisper hoặc mlx-whisper")
        
        if not YTDLP_AVAILABLE:
            missing.append("yt-dlp")
        
        # Check FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except:
            missing.append("ffmpeg")
        
        if missing:
            self.dep_status.setText(f"⚠️ Thiếu: {', '.join(missing)}")
            self.dep_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")
            self.start_btn.setEnabled(False)
        else:
            # Show device info
            if MLX_WHISPER_AVAILABLE:
                device_info = "Apple Silicon (MLX)"
            elif WHISPER_DEVICE == "cuda":
                device_info = "NVIDIA GPU (CUDA)"
            else:
                device_info = "CPU (chậm hơn)"
            
            self.dep_status.setText(f"✅ Sẵn sàng - {device_info}")
            self.dep_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px;")
    
    def populate_models(self):
        """Populate model dropdown with download status."""
        self.model_combo.clear()
        
        downloaded = get_downloaded_models()
        
        for model_id, info in WHISPER_MODELS.items():
            status = "✅" if model_id in downloaded else "⬇️"
            display_name = f"{status} {info['name']} ({info['size']})"
            self.model_combo.addItem(display_name, model_id)
        
        # Select first downloaded model, or first model
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) in downloaded:
                self.model_combo.setCurrentIndex(i)
                break
        
        self.on_model_changed()
    
    def on_model_changed(self):
        """Handle model selection change."""
        model_id = self.model_combo.currentData()
        if not model_id:
            return
        
        info = WHISPER_MODELS.get(model_id, {})
        is_downloaded = is_model_downloaded(model_id)
        
        # Update info label
        self.model_info_label.setText(
            f"VRAM: {info.get('vram', 'N/A')} • Độ chính xác: {info.get('accuracy', 'N/A')}"
        )
        
        # Update download button
        if is_downloaded:
            self.model_status_btn.setText("✅ Đã tải")
            self.model_status_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success']}20;
                    color: {COLORS['success']};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 11px;
                }}
            """)
            self.model_status_btn.setEnabled(False)
            self.model_delete_btn.setEnabled(True)  # Enable delete button
        else:
            self.model_status_btn.setText("⬇️ Tải về")
            self.model_status_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
            """)
            self.model_status_btn.setEnabled(True)
            self.model_delete_btn.setEnabled(False)  # Disable delete button
    
    def on_model_action(self):
        """Handle download button click."""
        model_id = self.model_combo.currentData()
        if not model_id or is_model_downloaded(model_id):
            return

        # Confirm download
        info = WHISPER_MODELS.get(model_id, {})
        reply = QMessageBox.question(
            self,
            "Tải model",
            f"Bạn muốn tải model {info['name']}?\n\n"
            f"Dung lượng: {info['size']}\n"
            f"Model sẽ được lưu vào cache của hệ thống.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show progress UI
        self.model_download_progress_frame.setVisible(True)
        self.model_download_status_label.setText("Đang chuẩn bị tải model...")
        self.model_download_progress_bar.setValue(0)

        # Disable buttons
        self.model_status_btn.setEnabled(False)
        self.model_delete_btn.setEnabled(False)
        self.start_btn.setEnabled(False)

        self.model_download_worker = ModelDownloadWorker(model_id)
        self.model_download_worker.progress.connect(self.on_model_download_progress)
        self.model_download_worker.finished.connect(self.on_model_download_finished)
        self.model_download_worker.error.connect(self.on_model_download_error)
        self.model_download_worker.start()
    
    def on_model_download_progress(self, message: str, percent: int):
        """Handle model download progress."""
        self.model_download_status_label.setText(message)
        self.model_download_progress_bar.setValue(percent)
    
    def on_model_download_finished(self, model_name: str):
        """Handle model download completion."""
        # Hide progress UI
        self.model_download_progress_frame.setVisible(False)

        # Refresh UI
        self.populate_models()
        self.start_btn.setEnabled(True)

        # Select the downloaded model
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_name:
                self.model_combo.setCurrentIndex(i)
                break

        QMessageBox.information(
            self,
            "Hoàn thành",
            f"Đã tải model {model_name} thành công!"
        )
    
    def on_model_download_error(self, error: str):
        """Handle model download error."""
        # Hide progress UI
        self.model_download_progress_frame.setVisible(False)

        # Re-enable buttons
        self.model_status_btn.setEnabled(True)
        self.start_btn.setEnabled(True)

        QMessageBox.critical(
            self,
            "Lỗi",
            f"Không thể tải model:\n\n{error}"
        )

    def on_cancel_model_download(self):
        """Cancel ongoing model download."""
        if hasattr(self, 'model_download_worker') and self.model_download_worker.isRunning():
            self.model_download_worker.cancel()
            self.model_download_worker.wait()  # Wait for thread to finish

            # Hide progress UI
            self.model_download_progress_frame.setVisible(False)

            # Re-enable buttons
            self.model_status_btn.setEnabled(True)
            self.start_btn.setEnabled(True)

    def on_delete_model(self):
        """Handle delete model button click."""
        model_id = self.model_combo.currentData()
        if not model_id or not is_model_downloaded(model_id):
            return

        # Confirm deletion
        info = WHISPER_MODELS.get(model_id, {})
        reply = QMessageBox.question(
            self,
            "Xóa model",
            f"Bạn có chắc muốn xóa model {info['name']}?\n\n"
            f"Dung lượng sẽ được giải phóng: {info['size']}\n"
            f"Model sẽ bị xóa khỏi cache của hệ thống.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete model
        try:
            if delete_model(model_id):
                # Refresh UI
                self.populate_models()

                QMessageBox.information(
                    self,
                    "Hoàn thành",
                    f"Đã xóa model {info['name']} thành công!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Cảnh báo",
                    f"Không tìm thấy model để xóa."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể xóa model:\n\n{str(e)}"
            )

    def set_project(self, project_id: int):
        """Set current project."""
        self.project_id = project_id
    
    def paste_url(self):
        """Paste URL from clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())
    
    def select_file(self):
        """Select video/audio file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file video/audio",
            "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.m4a *.flac);;All Files (*)"
        )
        
        if filepath:
            self.audio_path = filepath
            self.file_path_label.setText(Path(filepath).name)
            self.url_input.clear()
    
    def start_conversion(self):
        """Start the conversion process."""
        url = self.url_input.text().strip()
        
        if not url and not self.audio_path:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập YouTube URL hoặc chọn file")
            return
        
        # Check if model is downloaded
        model_id = self.model_combo.currentData()
        if not is_model_downloaded(model_id):
            reply = QMessageBox.question(
                self,
                "Model chưa tải",
                f"Model {model_id} chưa được tải về.\n\n"
                "Bạn có muốn tải ngay không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.on_model_action()
            return
        
        # Reset
        self.raw_text = ""
        self.processed_text = ""
        self.segments_data = []
        self.raw_text_edit.clear()
        self.processed_text_edit.clear()
        self.save_raw_txt_btn.setEnabled(False)
        self.save_srt_btn.setEnabled(False)
        self.save_processed_txt_btn.setEnabled(False)
        self.save_processed_docx_btn.setEnabled(False)
        self.continue_claude_btn.setVisible(False)
        
        # Show progress
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        
        if url:
            # Download from YouTube first
            self.download_worker = DownloadWorker(url, self.temp_dir)
            self.download_worker.progress.connect(self.on_download_progress)
            self.download_worker.finished.connect(self.on_download_finished)
            self.download_worker.error.connect(self.on_error)
            self.download_worker.start()
        else:
            # Use local file directly
            self.run_whisper(self.audio_path)
    
    def on_download_progress(self, message: str):
        """Handle download progress."""
        self.progress_label.setText(message)
        self.progress_bar.setValue(5)
    
    def on_download_finished(self, audio_path: str):
        """Handle download completion."""
        self.audio_path = audio_path
        self.run_whisper(audio_path)
    
    def run_whisper(self, audio_path: str):
        """Run Whisper transcription."""
        model = self.model_combo.currentData()
        preprocess = self.preprocess_check.isChecked()
        keep_timestamps = self.timestamp_check.isChecked()

        # Use MLX on Apple Silicon if available
        use_mlx = MLX_WHISPER_AVAILABLE and not WHISPER_AVAILABLE

        self.whisper_worker = WhisperWorker(
            audio_path, model, "vi", preprocess, use_mlx, keep_timestamps
        )
        self.whisper_worker.progress.connect(self.on_whisper_progress)
        self.whisper_worker.finished.connect(self.on_whisper_finished)
        self.whisper_worker.error.connect(self.on_error)
        self.whisper_worker.start()
    
    def on_whisper_progress(self, message: str, percent: int):
        """Handle Whisper progress."""
        self.progress_label.setText(message)
        self.progress_bar.setValue(percent)
    
    def on_whisper_finished(self, text: str, segments_data: list):
        """Handle Whisper completion."""
        self.raw_text = text
        self.segments_data = segments_data

        self.raw_text_edit.setPlainText(text)
        self.update_word_count()
        self.save_raw_txt_btn.setEnabled(True)

        # Enable SRT button only if timestamps are kept
        if self.timestamp_check.isChecked() and segments_data:
            self.save_srt_btn.setEnabled(True)
        
        # Check if should continue with Claude
        if self.level_claude.isChecked():
            self.run_claude()
        else:
            # Done - show continue button
            self.progress_frame.setVisible(False)
            self.start_btn.setEnabled(True)
            self.continue_claude_btn.setVisible(True)
            
            QMessageBox.information(
                self,
                "Hoàn thành",
                "Đã chuyển đổi xong!\n\n"
                "Bạn có thể:\n"
                "• Lưu file raw\n"
                "• Tiếp tục xử lý với Claude"
            )
    
    def continue_with_claude(self):
        """Continue processing with Claude."""
        if not self.raw_text:
            return
        
        self.continue_claude_btn.setVisible(False)
        self.progress_frame.setVisible(True)
        self.start_btn.setEnabled(False)
        self.run_claude()
    
    def run_claude(self):
        """Run Claude processing."""
        self.progress_label.setText("Đang xử lý với Claude...")
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)  # Indeterminate
        
        # Get project data
        instructions = ""
        memory = ""
        glossary = ""
        
        if self.project_id:
            project = db.get_project(self.project_id)
            if project:
                instructions = project.get('instructions', '')
            
            # Get memory
            memories = db.get_memories(self.project_id)
            memory = "\n".join([m['content'] for m in memories])
            
            # Get glossary
            glossary = db.get_glossary_for_prompt(self.project_id)
        
        self.processed_text_edit.clear()
        
        self.claude_worker = ClaudeProcessWorker(
            self.raw_text,
            instructions,
            memory,
            glossary
        )
        self.claude_worker.progress.connect(self.on_claude_progress)
        self.claude_worker.chunk_received.connect(self.on_claude_chunk)
        self.claude_worker.finished.connect(self.on_claude_finished)
        self.claude_worker.error.connect(self.on_error)
        self.claude_worker.start()
    
    def on_claude_progress(self, message: str):
        """Handle Claude progress."""
        self.progress_label.setText(message)
    
    def on_claude_chunk(self, chunk: str):
        """Handle Claude streaming chunk."""
        self.processed_text_edit.insertPlainText(chunk)
        # Auto scroll
        scrollbar = self.processed_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_claude_finished(self, text: str):
        """Handle Claude completion."""
        self.processed_text = text
        self.update_word_count()
        
        self.progress_frame.setVisible(False)
        self.progress_bar.setMaximum(100)
        self.start_btn.setEnabled(True)
        
        self.save_processed_txt_btn.setEnabled(True)
        self.save_processed_docx_btn.setEnabled(True)
        
        QMessageBox.information(self, "Hoàn thành", "Đã xử lý xong với Claude!")
    
    def on_error(self, error: str):
        """Handle errors."""
        self.progress_frame.setVisible(False)
        self.progress_bar.setMaximum(100)
        self.start_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi:\n\n{error}")
    
    def update_word_count(self):
        """Update word counts."""
        if self.raw_text:
            words = len(self.raw_text.split())
            self.raw_word_count.setText(f"{words:,} từ")
        
        if self.processed_text:
            words = len(self.processed_text.split())
            self.processed_word_count.setText(f"{words:,} từ")
    
    def save_file(self, content_type: str, file_format: str):
        """Save file to disk."""
        # Determine content
        if content_type == "raw":
            content = self.raw_text_edit.toPlainText()
            default_name = "whisper_output"
        else:
            content = self.processed_text_edit.toPlainText()
            default_name = "processed_output"
        
        if not content:
            QMessageBox.warning(self, "Lỗi", "Không có nội dung để lưu")
            return
        
        # Get save path
        if file_format == "txt":
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu file",
                f"{default_name}.txt",
                "Text Files (*.txt)"
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
        elif file_format == "docx":
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Lưu file",
                f"{default_name}.docx",
                "Word Documents (*.docx)"
            )
            
            if filepath:
                try:
                    from docx import Document
                    doc = Document()
                    
                    # Add content
                    for para in content.split('\n\n'):
                        if para.strip():
                            doc.add_paragraph(para.strip())
                    
                    doc.save(filepath)
                except ImportError:
                    # Fallback to txt if python-docx not available
                    filepath = filepath.replace('.docx', '.txt')
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    QMessageBox.warning(
                        self,
                        "Cảnh báo",
                        f"Không có thư viện python-docx.\nĐã lưu thành file .txt"
                    )
        
        if filepath:
            # Add to project files if checked
            if self.add_to_files_check.isChecked() and self.project_id:
                db.add_file(self.project_id, Path(filepath).name, filepath)

            QMessageBox.information(self, "Thành công", f"Đã lưu file:\n{filepath}")

    def on_timestamp_toggle(self, checked: bool):
        """Handle timestamp checkbox toggle."""
        # Show/hide SRT button
        self.save_srt_btn.setVisible(checked)

        # Enable SRT button only if we have segments data
        if checked and self.segments_data:
            self.save_srt_btn.setEnabled(True)
        else:
            self.save_srt_btn.setEnabled(False)

    def save_srt_file(self):
        """Save subtitle file in SRT format."""
        if not self.segments_data:
            QMessageBox.warning(self, "Lỗi", "Không có dữ liệu segments để xuất SRT")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Lưu file subtitle",
            "subtitle.srt",
            "SubRip Subtitle (*.srt)"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(self.segments_data, start=1):
                    # Sequence number
                    f.write(f"{i}\n")

                    # Timestamps in format: HH:MM:SS,mmm --> HH:MM:SS,mmm
                    start_time = self.format_srt_time(segment['start'])
                    end_time = self.format_srt_time(segment['end'])
                    f.write(f"{start_time} --> {end_time}\n")

                    # Text content
                    f.write(f"{segment['text']}\n")

                    # Blank line separator
                    f.write("\n")

            # Add to project files if checked
            if self.add_to_files_check.isChecked() and self.project_id:
                db.add_file(self.project_id, Path(filepath).name, filepath)

            QMessageBox.information(self, "Thành công", f"Đã lưu file SRT:\n{filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file SRT:\n{str(e)}")

    def format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
