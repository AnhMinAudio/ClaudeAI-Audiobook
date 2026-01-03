"""
AnhMin Audio - Claude API Client
Handles API calls with auto-rotation, streaming, and extended thinking
"""

import anthropic
from typing import Generator, Optional, List, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from database import db
from config import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE


@dataclass
class APIKeyInfo:
    """Information about an API key."""
    id: int
    name: str
    api_key: str
    is_active: bool
    error_count: int


class ClaudeClient:
    """Claude API client with auto-rotation and extended thinking support."""
    
    # Models that support extended thinking
    THINKING_MODELS = [
        "claude-opus-4-5-20250514",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514", 
        "claude-sonnet-4-5-20250929",
    ]
    
    def __init__(self):
        self.current_key: Optional[APIKeyInfo] = None
        self.model = DEFAULT_MODEL
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        self._client: Optional[anthropic.Anthropic] = None
        self.extended_thinking_enabled = True  # Bật mặc định
        self.thinking_budget = 10000  # Token budget cho thinking
        self.available_models: List[tuple] = []  # (display_name, model_id)
    
    def fetch_available_models(self) -> List[tuple]:
        """Fetch available models from Anthropic API."""
        if not self.ensure_client():
            return []
        
        try:
            # Call the models API
            response = self._client.models.list()
            
            models = []
            for model in response.data:
                model_id = model.id
                # Create display name from model ID
                display_name = self._format_model_name(model_id)
                if display_name:
                    models.append((display_name, model_id))
            
            # Sort by name (Opus first, then Sonnet, then Haiku)
            def sort_key(item):
                name = item[0].lower()
                if 'opus' in name:
                    priority = 0
                elif 'sonnet' in name:
                    priority = 1
                elif 'haiku' in name:
                    priority = 2
                else:
                    priority = 3
                # Sort by version (4.5 before 4)
                version = '0'
                if '4.5' in name or '4-5' in item[1]:
                    version = '5'
                elif '4' in name:
                    version = '4'
                return (priority, -float(version.replace('.', '')), name)
            
            models.sort(key=sort_key)
            self.available_models = models
            return models
            
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def _format_model_name(self, model_id: str) -> Optional[str]:
        """Format model ID to display name."""
        # Only include Claude models
        if not model_id.startswith('claude-'):
            return None
        
        # Parse model ID: claude-{type}-{version}-{date}
        parts = model_id.replace('claude-', '').split('-')
        if len(parts) < 2:
            return None
        
        # Extract type (opus, sonnet, haiku)
        model_type = parts[0].capitalize()
        
        # Extract version
        version = ""
        if len(parts) >= 2:
            # Handle versions like "4-5" (4.5) or "4"
            if parts[1].isdigit():
                version = parts[1]
                if len(parts) >= 3 and parts[2].isdigit():
                    version += f".{parts[2]}"
        
        if version:
            return f"Claude {model_type} {version}"
        return f"Claude {model_type}"
    
    def _get_next_api_key(self) -> Optional[APIKeyInfo]:
        """Get the next available API key."""
        key_data = db.get_active_api_key()
        if key_data:
            return APIKeyInfo(
                id=key_data['id'],
                name=key_data['name'],
                api_key=key_data['api_key'],
                is_active=bool(key_data['is_active']),
                error_count=key_data['error_count']
            )
        return None
    
    def _init_client(self, api_key: str) -> anthropic.Anthropic:
        """Initialize Anthropic client with API key."""
        return anthropic.Anthropic(api_key=api_key)
    
    def _rotate_api_key(self) -> bool:
        """Rotate to the next available API key."""
        if self.current_key:
            db.increment_api_key_error(self.current_key.id)
        
        self.current_key = self._get_next_api_key()
        if self.current_key:
            self._client = self._init_client(self.current_key.api_key)
            return True
        return False
    
    def ensure_client(self) -> bool:
        """Ensure we have a valid client."""
        if not self._client or not self.current_key:
            self.current_key = self._get_next_api_key()
            if self.current_key:
                self._client = self._init_client(self.current_key.api_key)
                return True
            return False
        return True
    
    def set_model(self, model: str):
        """Set the model to use."""
        self.model = model
    
    def set_extended_thinking(self, enabled: bool, budget: int = 10000):
        """Enable/disable extended thinking."""
        self.extended_thinking_enabled = enabled
        self.thinking_budget = budget
    
    def supports_thinking(self) -> bool:
        """Check if current model supports extended thinking."""
        return any(m in self.model for m in self.THINKING_MODELS)
    
    # ============== Batch API Methods ==============
    
    def create_batch(self, requests: List[Dict]) -> Optional[Dict]:
        """
        Create a batch of requests.
        
        Args:
            requests: List of dicts with 'custom_id' and 'params' keys
                     params should contain: model, max_tokens, system, messages
        
        Returns:
            Batch object with id, status, etc.
        """
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng.")
        
        try:
            # Create batch
            batch = self._client.messages.batches.create(requests=requests)
            
            db.mark_api_key_used(self.current_key.id)
            
            return {
                'id': batch.id,
                'status': batch.processing_status,
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'request_counts': {
                    'total': len(requests),
                    'processing': batch.request_counts.processing,
                    'succeeded': batch.request_counts.succeeded,
                    'errored': batch.request_counts.errored,
                    'canceled': batch.request_counts.canceled,
                    'expired': batch.request_counts.expired,
                }
            }
        except Exception as e:
            raise Exception(f"Lỗi tạo batch: {str(e)}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get status of a batch."""
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng.")
        
        try:
            batch = self._client.messages.batches.retrieve(batch_id)
            
            return {
                'id': batch.id,
                'status': batch.processing_status,
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'ended_at': batch.ended_at.isoformat() if batch.ended_at else None,
                'request_counts': {
                    'processing': batch.request_counts.processing,
                    'succeeded': batch.request_counts.succeeded,
                    'errored': batch.request_counts.errored,
                    'canceled': batch.request_counts.canceled,
                    'expired': batch.request_counts.expired,
                },
                'results_url': batch.results_url
            }
        except Exception as e:
            raise Exception(f"Lỗi lấy trạng thái batch: {str(e)}")
    
    def get_batch_results(self, batch_id: str) -> List[Dict]:
        """Get results of a completed batch."""
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng.")
        
        try:
            results = []
            for result in self._client.messages.batches.results(batch_id):
                result_dict = {
                    'custom_id': result.custom_id,
                    'type': result.result.type,
                }
                
                if result.result.type == 'succeeded':
                    # Extract text from response
                    text_content = ""
                    for block in result.result.message.content:
                        if block.type == 'text':
                            text_content += block.text
                    result_dict['content'] = text_content
                elif result.result.type == 'errored':
                    result_dict['error'] = str(result.result.error)
                
                results.append(result_dict)
            
            return results
        except Exception as e:
            raise Exception(f"Lỗi lấy kết quả batch: {str(e)}")
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch."""
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng.")
        
        try:
            self._client.messages.batches.cancel(batch_id)
            return True
        except Exception as e:
            raise Exception(f"Lỗi hủy batch: {str(e)}")
    
    def build_batch_request(self, custom_id: str, content: str, 
                            system_prompt: str) -> Dict:
        """Build a single request for batch processing."""
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": content}]
        }
        
        # Add extended thinking if supported
        if self.extended_thinking_enabled and self.supports_thinking():
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
            params["temperature"] = 1
        else:
            params["temperature"] = self.temperature
        
        return {
            "custom_id": custom_id,
            "params": params
        }
    
    def build_messages(self, messages: List[Dict], 
                       attachments: List[Dict] = None) -> List[Dict]:
        """Build messages array for API call."""
        api_messages = []
        
        for msg in messages:
            content = msg['content']
            
            # If there are attachments for this message
            if msg.get('attachments'):
                content_blocks = []
                for attachment in msg['attachments']:
                    if attachment.get('type') == 'text':
                        content_blocks.append({
                            "type": "text",
                            "text": f"[File: {attachment['name']}]\n{attachment['content']}"
                        })
                content_blocks.append({
                    "type": "text",
                    "text": content
                })
                api_messages.append({
                    "role": msg['role'],
                    "content": content_blocks
                })
            else:
                api_messages.append({
                    "role": msg['role'],
                    "content": content
                })
        
        return api_messages
    
    def build_system_prompt(self, instructions: str, memory: List[Dict]) -> str:
        """Build system prompt with instructions and memory."""
        system_parts = []
        
        if instructions:
            system_parts.append(instructions)
        
        if memory:
            memory_text = "\n\n=== THÔNG TIN DỰ ÁN (MEMORY) ===\n"
            for item in memory:
                memory_text += f"• {item['key']}: {item['value']}\n"
            system_parts.append(memory_text)
        
        return "\n\n".join(system_parts)
    
    def send_message(self, messages: List[Dict], 
                     system_prompt: str = "",
                     max_retries: int = 3) -> Optional[str]:
        """Send a message and get response (non-streaming)."""
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng. Vui lòng thêm API key trong cài đặt.")
        
        for attempt in range(max_retries):
            try:
                # Build API parameters
                api_params = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "system": system_prompt,
                    "messages": messages
                }
                
                # Add extended thinking if supported and enabled
                if self.extended_thinking_enabled and self.supports_thinking():
                    api_params["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_budget
                    }
                    # Temperature must be 1 for extended thinking
                    api_params["temperature"] = 1
                else:
                    api_params["temperature"] = self.temperature
                
                response = self._client.messages.create(**api_params)
                
                # Success - reset error count and mark as used
                db.reset_api_key_errors(self.current_key.id)
                db.mark_api_key_used(self.current_key.id)
                
                # Track usage
                input_tokens = response.usage.input_tokens if response.usage else 0
                output_tokens = response.usage.output_tokens if response.usage else 0
                db.add_usage(input_tokens, output_tokens)
                
                # Extract text from response (skip thinking blocks)
                result_text = ""
                for block in response.content:
                    if block.type == "text":
                        result_text += block.text
                
                return result_text
                
            except anthropic.RateLimitError:
                # Rate limit - try to rotate
                if not self._rotate_api_key():
                    raise Exception("Tất cả API key đã hết quota. Vui lòng thử lại sau.")
            except anthropic.AuthenticationError:
                # Invalid key - rotate
                if not self._rotate_api_key():
                    raise Exception("API key không hợp lệ. Vui lòng kiểm tra lại.")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
        
        return None
    
    def stream_message(self, messages: List[Dict],
                       system_prompt: str = "") -> Generator[str, None, None]:
        """Stream a message response."""
        if not self.ensure_client():
            raise Exception("Không có API key khả dụng. Vui lòng thêm API key trong cài đặt.")
        
        try:
            # Build API parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system_prompt,
                "messages": messages
            }
            
            # Add extended thinking if supported and enabled
            if self.extended_thinking_enabled and self.supports_thinking():
                api_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }
                # Temperature must be 1 for extended thinking
                api_params["temperature"] = 1
            else:
                api_params["temperature"] = self.temperature
            
            input_tokens = 0
            output_tokens = 0
            
            with self._client.messages.stream(**api_params) as stream:
                for event in stream:
                    # Handle different event types
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_start':
                            # Check if it's a thinking block or text block
                            if hasattr(event, 'content_block'):
                                if event.content_block.type == 'thinking':
                                    yield "[🧠 Đang suy nghĩ...]\n"
                        elif event.type == 'content_block_delta':
                            if hasattr(event, 'delta'):
                                if hasattr(event.delta, 'text'):
                                    yield event.delta.text
                                elif hasattr(event.delta, 'thinking'):
                                    # Skip thinking content in output
                                    pass
                        elif event.type == 'content_block_stop':
                            pass
                        elif event.type == 'message_delta':
                            # Get usage from final message
                            if hasattr(event, 'usage'):
                                output_tokens = event.usage.output_tokens if event.usage else 0
                        elif event.type == 'message_start':
                            if hasattr(event, 'message') and hasattr(event.message, 'usage'):
                                input_tokens = event.message.usage.input_tokens if event.message.usage else 0
                    elif hasattr(event, 'text'):
                        yield event.text
            
            # Success - track usage
            db.reset_api_key_errors(self.current_key.id)
            db.mark_api_key_used(self.current_key.id)
            
            if input_tokens > 0 or output_tokens > 0:
                db.add_usage(input_tokens, output_tokens)
            
        except anthropic.RateLimitError:
            # Emit rate limit warning
            self._on_rate_limit()
            if self._rotate_api_key():
                # Retry with new key
                yield from self.stream_message(messages, system_prompt)
            else:
                raise Exception("Tất cả API key đã hết quota.")
        except anthropic.AuthenticationError:
            if self._rotate_api_key():
                yield from self.stream_message(messages, system_prompt)
            else:
                raise Exception("API key không hợp lệ.")
    
    def _on_rate_limit(self):
        """Called when rate limit is hit."""
        # Store rate limit event for UI to pick up
        db.set_setting('last_rate_limit', datetime.now().isoformat())
        if self.current_key:
            db.set_setting('last_rate_limit_key', self.current_key.name)
    
    def test_api_key(self, api_key: str) -> Dict:
        """Test if an API key is valid."""
        try:
            test_client = anthropic.Anthropic(api_key=api_key)
            
            # Try to list models (free, doesn't consume tokens)
            start_time = datetime.now()
            response = test_client.models.list()
            end_time = datetime.now()
            
            response_time = int((end_time - start_time).total_seconds() * 1000)
            model_count = len(response.data) if response.data else 0
            
            return {
                'valid': True,
                'model_count': model_count,
                'response_time_ms': response_time,
                'error': None
            }
        except anthropic.AuthenticationError as e:
            return {
                'valid': False,
                'model_count': 0,
                'response_time_ms': 0,
                'error': 'API key không hợp lệ'
            }
        except Exception as e:
            return {
                'valid': False,
                'model_count': 0,
                'response_time_ms': 0,
                'error': str(e)
            }


class StreamWorker(QThread):
    """Worker thread for streaming responses."""
    
    chunk_received = pyqtSignal(str)
    stream_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: ClaudeClient, messages: List[Dict], 
                 system_prompt: str = ""):
        super().__init__()
        self.client = client
        self.messages = messages
        self.system_prompt = system_prompt
        self._is_cancelled = False
    
    def run(self):
        """Run the streaming in background thread."""
        try:
            full_response = ""
            for chunk in self.client.stream_message(self.messages, self.system_prompt):
                if self._is_cancelled:
                    break
                full_response += chunk
                self.chunk_received.emit(chunk)
            
            if not self._is_cancelled:
                self.stream_finished.emit(full_response)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancel the streaming."""
        self._is_cancelled = True


# Singleton instance
claude_client = ClaudeClient()
