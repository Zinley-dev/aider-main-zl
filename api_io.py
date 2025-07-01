from aider.io import InputOutput
import os
import asyncio
import json
from typing import AsyncGenerator
import time

class ApiInputOutput(InputOutput):
    """
    Lớp InputOutput đặc biệt cho REST API
    Không yêu cầu đầu vào từ người dùng và capture tất cả output
    """
    
    def __init__(self):
        super().__init__(yes=True, pretty=False, dry_run=False)
        self.output_buffer = []
        self.error_buffer = []
        self.warning_buffer = []
    
    def tool_output(self, msg, log_only=False):
        """Capture tool output"""
        if not log_only:
            self.output_buffer.append(str(msg))
        super().tool_output(msg, log_only=log_only)
    
    def tool_error(self, msg):
        """Capture tool errors"""
        self.error_buffer.append(str(msg))
        super().tool_error(msg)
    
    def tool_warning(self, msg):
        """Capture tool warnings"""
        self.warning_buffer.append(str(msg))
        super().tool_warning(msg)
    
    def user_input(self, msg):
        """Override user input - không cần input từ user trong API"""
        self.output_buffer.append(f"User: {msg}")
        return ""  # Trả về empty string thay vì gọi super()
    
    def ai_output(self, msg, pretty=None):
        """Capture AI output"""
        self.output_buffer.append(f"AI: {msg}")
        super().ai_output(msg)
    
    def assistant_output(self, msg, pretty=None):
        """Capture assistant output"""
        self.output_buffer.append(f"Assistant: {msg}")
        super().assistant_output(msg, pretty)
    
    def get_input(self, root, files, addable_files, commands, read_only_files, edit_format=None):
        """
        Override get_input - không gọi input từ người dùng trong API
        Trả về None để báo hiệu không có input
        """
        return None
    
    def confirm_ask(self, question, default="y", subject=None, group=None, allow_never=False, explicit_yes_required=False):
        """
        Override confirm_ask - tự động trả về True cho tất cả xác nhận
        """
        self.output_buffer.append(f"Auto-confirmed: {question}")
        return True
    
    def write_text(self, filename, content, encoding="utf-8"):
        """
        Override write_text để đảm bảo file được ghi thực tế
        """
        try:
            # Ghi file trực tiếp
            with open(filename, 'w', encoding=encoding) as f:
                f.write(content)
            self.tool_output(f"✅ Successfully wrote file: {filename}")
            print(f"✅ API: Wrote file {filename} ({len(content)} chars)")
            return True
        except Exception as e:
            self.tool_error(f"❌ Failed to write file {filename}: {e}")
            print(f"❌ API: Failed to write file {filename}: {e}")
            return False
    
    def read_text(self, filename, encoding="utf-8"):
        """
        Override read_text để đọc file thực tế
        """
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"📖 API: Read file {filename} ({len(content)} chars)")
                return content
            else:
                print(f"⚠️ API: File not found: {filename}")
                return None
        except Exception as e:
            self.tool_error(f"❌ Failed to read file {filename}: {e}")
            print(f"❌ API: Failed to read file {filename}: {e}")
            return None
    
    def get_captured_output(self):
        """Lấy tất cả output đã capture và clear buffer"""
        output = "\n".join(self.output_buffer)
        self.output_buffer = []
        return output
    
    def get_captured_errors(self):
        """Lấy tất cả errors đã capture và clear buffer"""
        errors = "\n".join(self.error_buffer)
        self.error_buffer = []
        return errors
    
    def get_captured_warnings(self):
        """Lấy tất cả warnings đã capture và clear buffer"""
        warnings = "\n".join(self.warning_buffer)
        self.warning_buffer = []
        return warnings
    
    def clear_buffers(self):
        """Clear tất cả buffers"""
        self.output_buffer = []
        self.error_buffer = []
        self.warning_buffer = []
    
    def get_all_captured(self):
        """Lấy tất cả captured content"""
        return {
            "output": self.get_captured_output(),
            "errors": self.get_captured_errors(),
            "warnings": self.get_captured_warnings()
        }
    
    def start_streaming(self):
        """Dummy method for compatibility - ApiInputOutput doesn't support streaming"""
        pass
    
    def stop_streaming(self):
        """Dummy method for compatibility - ApiInputOutput doesn't support streaming"""
        pass
    
    async def get_stream_events(self):
        """Dummy method for compatibility - ApiInputOutput doesn't support streaming"""
        # Return empty generator
        return
        yield  # This line will never be reached, but makes it a generator


class StreamingApiInputOutput(ApiInputOutput):
    """
    Streaming version của ApiInputOutput cho SSE
    """
    
    def __init__(self):
        super().__init__()
        self.stream_queue = asyncio.Queue()
        self.streaming = False
    
    def start_streaming(self):
        """Bắt đầu streaming mode"""
        self.streaming = True
        self.clear_buffers()
    
    def stop_streaming(self):
        """Dừng streaming mode"""
        self.streaming = False
    
    async def emit_event(self, event_type: str, data: dict):
        """Emit một SSE event"""
        if self.streaming:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": time.time()
            }
            await self.stream_queue.put(event)
    
    def tool_output(self, msg, log_only=False):
        """Override để stream tool output"""
        super().tool_output(msg, log_only)
        if self.streaming and not log_only:
            # Tạo event cho stream - sử dụng try/except để tránh lỗi event loop
            try:
                asyncio.create_task(self.emit_event("tool_output", {
                    "message": str(msg)
                }))
            except RuntimeError:
                # Không có event loop, thêm vào queue trực tiếp
                self.stream_queue.put_nowait({
                    "type": "tool_output",
                    "data": {"message": str(msg)},
                    "timestamp": time.time()
                })
    
    def tool_error(self, msg):
        """Override để stream tool errors"""
        super().tool_error(msg)
        if self.streaming:
            try:
                asyncio.create_task(self.emit_event("tool_error", {
                    "message": str(msg)
                }))
            except RuntimeError:
                self.stream_queue.put_nowait({
                    "type": "tool_error",
                    "data": {"message": str(msg)},
                    "timestamp": time.time()
                })
    
    def tool_warning(self, msg):
        """Override để stream tool warnings"""
        super().tool_warning(msg)
        if self.streaming:
            try:
                asyncio.create_task(self.emit_event("tool_warning", {
                    "message": str(msg)
                }))
            except RuntimeError:
                self.stream_queue.put_nowait({
                    "type": "tool_warning",
                    "data": {"message": str(msg)},
                    "timestamp": time.time()
                })
    
    def ai_output(self, msg, pretty=None):
        """Override để stream AI output"""
        super().ai_output(msg)
        if self.streaming:
            try:
                asyncio.create_task(self.emit_event("ai_output", {
                    "message": str(msg)
                }))
            except RuntimeError:
                self.stream_queue.put_nowait({
                    "type": "ai_output",
                    "data": {"message": str(msg)},
                    "timestamp": time.time()
                })
    
    def assistant_output(self, msg, pretty=None):
        """Override để stream assistant output"""
        super().assistant_output(msg, pretty)
        if self.streaming:
            try:
                asyncio.create_task(self.emit_event("assistant_output", {
                    "message": str(msg)
                }))
            except RuntimeError:
                self.stream_queue.put_nowait({
                    "type": "assistant_output",
                    "data": {"message": str(msg)},
                    "timestamp": time.time()
                })
    
    def write_text(self, filename, content, encoding="utf-8"):
        """Override để stream file write events"""
        result = super().write_text(filename, content, encoding)
        if self.streaming:
            try:
                asyncio.create_task(self.emit_event("file_write", {
                    "filename": filename,
                    "content_length": len(content),
                    "success": result
                }))
            except RuntimeError:
                self.stream_queue.put_nowait({
                    "type": "file_write",
                    "data": {
                        "filename": filename,
                        "content_length": len(content),
                        "success": result
                    },
                    "timestamp": time.time()
                })
        return result
    
    async def get_stream_events(self) -> AsyncGenerator[dict, None]:
        """Generator để lấy stream events"""
        while self.streaming:
            try:
                # Đợi event với timeout
                event = await asyncio.wait_for(self.stream_queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                # Gửi heartbeat event
                yield {
                    "type": "heartbeat",
                    "data": {"status": "alive"},
                    "timestamp": time.time()
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "data": {"message": str(e)},
                    "timestamp": time.time()
                }
                break 