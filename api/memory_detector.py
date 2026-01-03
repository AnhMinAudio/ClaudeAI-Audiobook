"""
AnhMin Audio - Auto Memory Detector
Automatically detect and extract memory from chapter content using Claude API
"""

import re
from typing import List, Dict, Tuple
from api import claude_client
from database import db


class MemoryDetector:
    """Automatically detect memory items from chapter content."""

    # Prompt template for memory detection
    DETECTION_PROMPT = """Hãy phân tích nội dung chương truyện sau và trích xuất các thông tin quan trọng cần ghi nhớ.

Trả về kết quả theo format Markdown sau:

## Nhân vật:
- key_name: Tên nhân vật - mô tả ngắn gọn
- ...

## Địa danh:
- key_name: Tên địa danh - mô tả ngắn gọn
- ...

## Cảnh giới:
- key_name: Tên cảnh giới - mô tả ngắn gọn
- ...

## Kỹ năng:
- key_name: Tên kỹ năng - mô tả ngắn gọn
- ...

## Vật phẩm:
- key_name: Tên vật phẩm - mô tả ngắn gọn
- ...

## Thế lực:
- key_name: Tên thế lực - mô tả ngắn gọn
- ...

LƯU Ý:
- key_name phải là snake_case (chữ thường, dấu gạch dưới), không dấu tiếng Việt
- Chỉ trích xuất thông tin QUAN TRỌNG, không trích xuất chi tiết nhỏ
- Nếu một category không có thông tin mới thì BỎ QUA category đó
- Mỗi item chỉ cần 1 dòng mô tả ngắn gọn

NỘI DUNG CHƯƠNG:

{content}
"""

    @staticmethod
    def detect_memory(content: str, project_id: int) -> Tuple[int, str]:
        """
        Detect memory from chapter content and auto-add to database.

        Args:
            content: Chapter content text
            project_id: Project ID to add memory to

        Returns:
            Tuple of (items_added, error_message)
            - items_added: Number of new memory items added
            - error_message: Error message if failed, empty string if success
        """
        try:
            # Build prompt
            prompt = MemoryDetector.DETECTION_PROMPT.format(content=content)

            # Call Claude API (non-streaming for simple parsing)
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = claude_client.send_message(messages, system_prompt="")

            if not response:
                return 0, "Không nhận được phản hồi từ Claude API"

            # Parse markdown response and add to database
            items_added = MemoryDetector._parse_and_add_memory(response, project_id)

            return items_added, ""

        except Exception as e:
            return 0, f"Lỗi khi phát hiện memory: {str(e)}"

    @staticmethod
    def _parse_and_add_memory(markdown_text: str, project_id: int) -> int:
        """
        Parse markdown memory format and add to database.

        Args:
            markdown_text: Markdown formatted memory text
            project_id: Project ID

        Returns:
            Number of items added
        """
        items_added = 0
        current_category = "general"

        # Category mapping
        category_map = {
            "nhân vật": "character",
            "địa danh": "location",
            "cảnh giới": "realm",
            "kỹ năng": "skill",
            "vật phẩm": "item",
            "thế lực": "faction",
            "series": "series",
            "phong cách": "style",
            "tiến độ": "progress",
        }

        lines = markdown_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for category headers (## Category)
            if line.startswith('##'):
                category_text = line.lstrip('#').strip().lower().rstrip(':')

                # Find matching category
                matched = False
                for key, value in category_map.items():
                    if key in category_text:
                        current_category = value
                        matched = True
                        break

                if not matched:
                    current_category = "general"
                continue

            # Parse key-value pairs (format: "- key: value")
            if line.startswith('-') and ':' in line:
                # Remove leading "- "
                line = line.lstrip('-').strip()

                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    if key and value:
                        # Check if key already exists for this project
                        existing_memory = db.get_memory(project_id)
                        key_exists = any(
                            mem['key'] == key and mem['category'] == current_category
                            for mem in existing_memory
                        )

                        if not key_exists:
                            # Add new memory item
                            db.set_memory(project_id, key, value, current_category)
                            items_added += 1

        return items_added


def auto_detect_and_add_memory(content: str, project_id: int) -> Tuple[int, str]:
    """
    Convenience function to detect and add memory from content.

    Args:
        content: Chapter content text
        project_id: Project ID

    Returns:
        Tuple of (items_added, error_message)
    """
    return MemoryDetector.detect_memory(content, project_id)
