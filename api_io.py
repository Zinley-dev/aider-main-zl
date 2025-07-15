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
        self.current_code_buffer = ""
        self.current_file = None
    
    def start_streaming(self):
        """Bắt đầu streaming mode"""
        self.streaming = True
        self.clear_buffers()
        self.current_code_buffer = ""
        self.current_file = None
    
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
    
    def emit_event_sync(self, event_type: str, data: dict):
        """Emit event synchronously - helper method"""
        if self.streaming:
            print(f"🌊 Emitting event: {event_type} - {str(data)[:100]}...")
            # Always put directly into queue to avoid RuntimeWarning
            event = {
                "type": event_type,
                "data": data,
                "timestamp": time.time()
            }
            self.stream_queue.put_nowait(event)
            print(f"📨 Event queued: {event_type}")
        else:
            print(f"⚠️ Not streaming, event {event_type} ignored")
    
    # Stream thinking process
    def stream_thinking(self, msg):
        """Stream AI thinking process"""
        self.emit_event_sync("ai_thinking", {"message": str(msg)})
    
    # Stream code generation process
    def stream_code_generation_start(self, filename, language=""):
        """Stream start of code generation for a file"""
        self.current_file = filename
        self.current_code_buffer = ""
        self.emit_event_sync("code_gen_start", {
            "filename": filename,
            "language": language,
            "message": f"Starting code generation for {filename}"
        })
    
    def stream_code_chunk(self, chunk, filename=None):
        """Stream a chunk of generated code"""
        if filename:
            self.current_file = filename
        
        self.current_code_buffer += chunk
        self.emit_event_sync("code_chunk", {
            "filename": self.current_file or "unknown",
            "chunk": chunk,
            "total_length": len(self.current_code_buffer),
            "message": f"Code chunk: {chunk[:50]}{'...' if len(chunk) > 50 else ''}"
        })
    
    def stream_code_generation_complete(self, filename=None, total_lines=0):
        """Stream completion of code generation"""
        if filename:
            self.current_file = filename
            
        self.emit_event_sync("code_gen_complete", {
            "filename": self.current_file or "unknown",
            "total_length": len(self.current_code_buffer),
            "total_lines": total_lines,
            "message": f"Completed code generation for {self.current_file}"
        })
    
    # Stream file modification process
    def stream_file_modification_start(self, filename, action="modify"):
        """Stream start of file modification"""
        self.emit_event_sync("file_mod_start", {
            "filename": filename,
            "action": action,
            "message": f"Starting {action} for {filename}"
        })
    
    def stream_file_modification_step(self, filename, step, details=""):
        """Stream individual file modification step"""
        self.emit_event_sync("file_mod_step", {
            "filename": filename,
            "step": step,
            "details": details,
            "message": f"{filename}: {step} - {details}"
        })
    
    def stream_file_modification_complete(self, filename, success=True, details=""):
        """Stream completion of file modification"""
        self.emit_event_sync("file_mod_complete", {
            "filename": filename,
            "success": success,
            "details": details,
            "message": f"{'✅' if success else '❌'} {filename}: {details}"
        })
    
    # Stream AI response progressively
    def stream_ai_response_start(self):
        """Stream start of AI response"""
        self.emit_event_sync("ai_response_start", {
            "message": "AI is generating response..."
        })
    
    def stream_ai_response_chunk(self, chunk):
        """Stream chunk of AI response"""
        self.emit_event_sync("ai_response_chunk", {
            "chunk": chunk,
            "message": chunk[:100] + ("..." if len(chunk) > 100 else "")
        })
    
    def stream_ai_chunk_debug(self, chunk, chunk_number):
        """Stream AI chunk with debug info for real-time monitoring"""
        print(f"🔍 XXX Chunk #{chunk_number}: '{chunk}' (type: {type(chunk)})")
        
        # Emit raw chunk event for debugging
        self.emit_event_sync("ai_chunk_debug", {
            "chunk": str(chunk),
            "chunk_number": chunk_number,
            "chunk_type": str(type(chunk)),
            "chunk_length": len(str(chunk)),
            "message": f"Chunk #{chunk_number}: {repr(chunk)}"
        })
        print(f"📨 XXX Direct queued chunk event #{chunk_number}")
        
        # Also emit regular chunk event
        self.emit_event_sync("ai_response_chunk", {
            "chunk": str(chunk),
            "chunk_number": chunk_number,
            "message": str(chunk)
        })
    
    def stream_ai_response_complete(self):
        """Stream completion of AI response"""
        self.emit_event_sync("ai_response_complete", {
            "message": "AI response completed"
        })
    
    # Stream execution steps
    def stream_execution_step(self, step_name, details="", status="running"):
        """Stream execution step"""
        self.emit_event_sync("execution_step", {
            "step": step_name,
            "details": details,
            "status": status,
            "message": f"{step_name}: {details}"
        })
    
    def tool_output(self, msg, log_only=False):
        """Override để stream tool output"""
        super().tool_output(msg, log_only)
        if self.streaming and not log_only:
            self.emit_event_sync("tool_output", {"message": str(msg)})
    
    def tool_error(self, msg):
        """Override để stream tool errors"""
        super().tool_error(msg)
        if self.streaming:
            self.emit_event_sync("tool_error", {"message": str(msg)})
    
    def tool_warning(self, msg):
        """Override để stream tool warnings"""
        super().tool_warning(msg)
        if self.streaming:
            self.emit_event_sync("tool_warning", {"message": str(msg)})
    
    def ai_output(self, msg, pretty=None):
        """Override để stream AI output với enhanced chunking"""
        super().ai_output(msg)
        if self.streaming:
            # Enhanced chunking with debug info
            chunk_size = 50  # Smaller chunks for better real-time feel
            msg_str = str(msg)
            total_chunks = (len(msg_str) + chunk_size - 1) // chunk_size
            
            print(f"🎯 AI output streaming: {len(msg_str)} chars, {total_chunks} chunks")
            
            for i in range(0, len(msg_str), chunk_size):
                chunk = msg_str[i:i + chunk_size]
                chunk_number = i // chunk_size + 1
                
                # Use our new debug method
                self.stream_ai_chunk_debug(chunk, chunk_number)
                
                # Also emit traditional ai_output event
                self.emit_event_sync("ai_output", {
                    "message": chunk,
                    "is_chunk": True,
                    "chunk_index": chunk_number - 1,
                    "total_chunks": total_chunks,
                    "chunk_size": len(chunk)
                })
            
            # Emit summary event
            self.emit_event_sync("ai_output_complete", {
                "total_length": len(msg_str),
                "total_chunks": total_chunks,
                "message": f"AI output complete: {len(msg_str)} characters"
            })
            
            print(f"🎉 XXX Final result length: {len(msg_str)} characters, total chunks: {total_chunks}")

    def assistant_output(self, msg, pretty=None):
        """Override để stream assistant output"""
        super().assistant_output(msg)
        if self.streaming:
            self.emit_event_sync("assistant_output", {"message": str(msg)})
    
    def write_text(self, filename, content, encoding="utf-8"):
        """Override để stream file write events with detailed progress"""
        if self.streaming:
            self.stream_file_modification_start(filename, "write")
            
            # Stream content preview
            preview = content[:200] + ("..." if len(content) > 200 else "")
            self.stream_file_modification_step(filename, "preparing_content", 
                                             f"Content length: {len(content)} chars")
        
        result = super().write_text(filename, content, encoding)
        
        if self.streaming:
            if result:
                self.stream_file_modification_step(filename, "writing_file", "Writing to disk...")
                self.stream_file_modification_complete(filename, True, 
                                                     f"Successfully written {len(content)} characters")
                # Also emit the traditional file_write event for backward compatibility
                self.emit_event_sync("file_write", {
                    "filename": filename,
                    "content_length": len(content),
                    "success": result,
                    "content_preview": content[:200] + ("..." if len(content) > 200 else "")
                })
            else:
                self.stream_file_modification_complete(filename, False, "Failed to write file")
        
        return result
    
    async def get_stream_events(self) -> AsyncGenerator[dict, None]:
        """Generator để lấy stream events"""
        event_count = 0
        print(f"🎬 Starting get_stream_events generator (streaming={self.streaming})")
        
        while self.streaming:
            try:
                # Check if there are events in the queue
                if not self.stream_queue.empty():
                    event = self.stream_queue.get_nowait()
                    event_count += 1
                    print(f"📤 Yielding event #{event_count}: {event.get('type', 'unknown')} - {str(event.get('data', {}))[:50]}...")
                    yield event
                else:
                    # If no events, wait a bit and send heartbeat
                    await asyncio.sleep(0.1)
                    if event_count % 50 == 0:  # Send heartbeat every 5 seconds (50 * 0.1s)
                        heartbeat = {
                            "type": "heartbeat",
                            "data": {"status": "alive", "events_sent": event_count, "queue_size": self.stream_queue.qsize()},
                            "timestamp": time.time()
                        }
                        print(f"💓 Heartbeat sent (events so far: {event_count}, queue size: {self.stream_queue.qsize()})")
                        yield heartbeat
                    
            except asyncio.QueueEmpty:
                # Queue is empty, continue waiting
                await asyncio.sleep(0.1)
                continue
            except Exception as e:
                print(f"❌ Error in get_stream_events: {e}")
                error_event = {
                    "type": "error",
                    "data": {"message": str(e)},
                    "timestamp": time.time()
                }
                yield error_event
                break
        
        print(f"🏁 Stream ended, total events sent: {event_count}")
        
        # Send final event to indicate stream end
        final_event = {
            "type": "stream_end",
            "data": {"total_events": event_count},
            "timestamp": time.time()
        }
        yield final_event

    def force_flush_events(self):
        """Force flush all pending events from the queue"""
        if self.streaming:
            queue_size = self.stream_queue.qsize()
            print(f"🔄 Force flushing {queue_size} pending events...")
            flushed_count = 0
            while not self.stream_queue.empty():
                try:
                    event = self.stream_queue.get_nowait()
                    flushed_count += 1
                    print(f"💨 Flushed event #{flushed_count}: {event.get('type', 'unknown')}")
                except:
                    break
            print(f"✅ Flushed {flushed_count} events") 