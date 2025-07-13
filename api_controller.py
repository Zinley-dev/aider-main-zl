import os
import json
import asyncio
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import HTTPException, UploadFile

from api_util import (
    get_or_create_session, 
    create_sse_response, 
    get_image_files_info, 
    create_enhanced_message,
    handle_file_extraction,
    get_edited_files,
    create_temp_repo,
    get_session_manager
)
from api_io import StreamingApiInputOutput
from config import settings

# Lấy session manager
session_manager = get_session_manager()

async def chat_stream(request) -> AsyncGenerator[str, None]:
    """
    Streaming chat với SSE - enhanced with detailed code generation streaming
    """
    streaming_io = None
    original_cwd = os.getcwd()
    
    try:
        # Emit start event
        yield f"event: start\ndata: {json.dumps({'message': 'Starting chat...'})}\n\n"
        
        # Tạo session với streaming IO
        session, session_id = get_or_create_session(
            session_id=request.session_id, 
            repo_path=request.repo_path,
            model=request.model,
            files=request.files,
            read_only_files=request.read_only_files,
            edit_format=request.edit_format,
            use_streaming=True
        )
        
        coder = session["coder"]
        streaming_io = session["io"]
        
        # Debug: Check IO type
        print(f"🔍 IO type: {type(streaming_io)}")
        print(f"🔍 Has get_stream_events: {hasattr(streaming_io, 'get_stream_events')}")
        
        # Ensure we have StreamingApiInputOutput for streaming
        if not isinstance(streaming_io, StreamingApiInputOutput):
            print("⚠️ Wrong IO type for streaming, creating new StreamingApiInputOutput")
            streaming_io = StreamingApiInputOutput()
            session["io"] = streaming_io
            coder.io = streaming_io
        
        # Đảm bảo working directory đúng
        repo_path = session.get("repo_path")
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            yield f"event: info\ndata: {json.dumps({'message': f'Working in directory: {repo_path}'})}\n\n"
        
        # Clear any previous state
        if hasattr(coder, 'aider_edited_files'):
            coder.aider_edited_files = set()
        streaming_io.clear_buffers()
        
        # DEBUG: Check streaming configuration
        print(f"🔍 Model name: {coder.main_model.name}")
        print(f"🔍 Model streaming support: {getattr(coder.main_model, 'streaming', 'NOT_SET')}")
        print(f"🔍 Coder stream setting: {coder.stream}")
        
        # FORCE enable streaming for the coder if model supports it
        if hasattr(coder.main_model, 'streaming') and coder.main_model.streaming:
            coder.stream = True
            print(f"🔧 FORCED coder.stream = True (model supports streaming)")
        elif not hasattr(coder.main_model, 'streaming'):
            # If model doesn't have streaming attribute, assume it supports streaming
            coder.stream = True
            print(f"🔧 FORCED coder.stream = True (no streaming attribute found)")
        
        print(f"🔍 Final coder.stream setting: {coder.stream}")

        # Start streaming
        streaming_io.start_streaming()
        print(f"🌊 Started streaming with io: {type(streaming_io)}")
        print(f"🌊 Streaming active: {streaming_io.streaming}")
        
        # Stream initial analysis
        yield f"event: execution_step\ndata: {json.dumps({'step': 'analyzing_request', 'message': 'Analyzing your request...', 'status': 'running'})}\n\n"
        
        # Debug: Check coder state
        print(f"🔍 Coder files: {list(getattr(coder, 'abs_fnames', []))}")
        print(f"🔍 Edited files before: {list(getattr(coder, 'aider_edited_files', []))}")
        
        # Stream file analysis
        if request.files:
            yield f"event: execution_step\ndata: {json.dumps({'step': 'analyzing_files', 'message': f'Analyzing files: {request.files}', 'status': 'running'})}\n\n"
            for file in request.files:
                if os.path.exists(file):
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    yield f"event: execution_step\ndata: {json.dumps({'step': 'file_analyzed', 'message': f'📄 {file}: {len(content)} characters', 'status': 'complete'})}\n\n"
                else:
                    yield f"event: execution_step\ndata: {json.dumps({'step': 'file_analyzed', 'message': f'📄 {file}: New file (will be created)', 'status': 'complete'})}\n\n"
        
        # Lấy thông tin về file ảnh
        image_files_info = get_image_files_info(coder)
        if image_files_info:
            yield f"event: execution_step\ndata: {json.dumps({'step': 'image_analysis', 'message': 'Found reference images in session', 'status': 'complete'})}\n\n"
        
        # Check if there's conversation history
        if hasattr(coder, 'done_messages') and coder.done_messages:
            yield f"event: execution_step\ndata: {json.dumps({'step': 'context_analysis', 'message': f'Found {len(coder.done_messages)} previous messages in conversation history', 'status': 'complete'})}\n\n"
        
        # Chuẩn bị message với Aider's native context
        enhanced_message = create_enhanced_message(request.message, request.files, image_files_info)
        print(f"🔍 Enhanced message: {enhanced_message[:200]}..." if len(enhanced_message) > 200 else enhanced_message)
        
        # Stream AI thinking process
        yield f"event: ai_thinking\ndata: {json.dumps({'message': 'AI is analyzing the requirements and planning the code structure...'})}\n\n"
        
        # Emit processing event
        yield f"event: processing\ndata: {json.dumps({'message': 'Starting AI code generation...'})}\n\n"
        
        # Stream AI response start
        yield f"event: ai_response_start\ndata: {json.dumps({'message': 'AI is generating response...'})}\n\n"
        
        print(f"🔍 Start coder with streaming.....")
        # Tạo task để chạy coder với enhanced streaming
        async def run_coder_with_streaming():
            print(f"🔍 XXX Run coder with streaming.....")
            loop = asyncio.get_event_loop()
            
            # Stream code generation start for target files
            if request.files:
                for file in request.files:
                    file_ext = os.path.splitext(file)[1].lower()
                    language = {
                        '.html': 'html',
                        '.css': 'css', 
                        '.js': 'javascript',
                        '.py': 'python',
                        '.json': 'json'
                    }.get(file_ext, 'text')
                    
                    streaming_io.stream_code_generation_start(file, language)
            
            # Run the actual coder with streaming - FIXED: Now properly streams AI text chunks
            def run_coder_stream():
                # Get the stream generator
                stream_generator = coder.run_stream(user_message=enhanced_message)
                final_result = ""
                chunk_count = 0
                
                try:
                    for chunk in stream_generator:
                        chunk_count += 1
                        if chunk:
                            chunk_str = str(chunk)
                            final_result += chunk_str
                            
                            print(f"🔍 Processing chunk #{chunk_count}: '{chunk_str[:50]}...'")
                            
                            # Emit the actual AI text as streaming response
                            ai_text_event = {
                                "type": "ai_response_chunk",
                                "data": {
                                    "chunk": chunk_str,
                                    "chunk_count": chunk_count,
                                    "total_length": len(final_result),
                                    "message": chunk_str  # The actual AI text content
                                },
                                "timestamp": time.time()
                            }
                            streaming_io.stream_queue.put_nowait(ai_text_event)
                            
                            # Also emit debug info
                            debug_event = {
                                "type": "ai_chunk_debug",
                                "data": {
                                    "chunk": chunk_str,
                                    "chunk_count": chunk_count,
                                    "chunk_length": len(chunk_str),
                                    "message": f"🔍 Raw chunk #{chunk_count}: {chunk_str[:100]}{'...' if len(chunk_str) > 100 else ''}"
                                },
                                "timestamp": time.time()
                            }
                            streaming_io.stream_queue.put_nowait(debug_event)
                            
                            # Emit AI output events for compatibility
                            ai_output_event = {
                                "type": "ai_output",
                                "data": {
                                    "message": chunk_str,
                                    "chunk_index": chunk_count - 1,
                                    "total_length": len(final_result),
                                    "is_streaming": True
                                },
                                "timestamp": time.time()
                            }
                            streaming_io.stream_queue.put_nowait(ai_output_event)
                            
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    
                    error_event = {
                        "type": "ai_chunk_debug",
                        "data": {
                            "chunk": f"ERROR: {str(e)}",
                            "chunk_count": chunk_count,
                            "message": f"❌ Stream error: {str(e)}"
                        },
                        "timestamp": time.time()
                    }
                    streaming_io.stream_queue.put_nowait(error_event)
                                
                # Final completion event
                completion_event = {
                    "type": "ai_response_complete",
                    "data": {
                        "final_content": final_result,
                        "final_length": len(final_result),
                        "total_chunks": chunk_count,
                        "message": f"AI response completed with {chunk_count} chunks"
                    },
                    "timestamp": time.time()
                }
                streaming_io.stream_queue.put_nowait(completion_event)
                
                return final_result
            
            # Run in executor
            result = await loop.run_in_executor(None, run_coder_stream)
            
            # Stream code generation complete
            if request.files:
                for file in request.files:
                    if os.path.exists(file):
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        lines = len(content.split('\n'))
                        streaming_io.stream_code_generation_complete(file, lines)
            
            return result
        
        # Chạy coder task
        coder_task = asyncio.create_task(run_coder_with_streaming())
        
        # Stream events cho đến khi coder hoàn thành
        response = None
        stream_generator = streaming_io.get_stream_events()
        
        # Counter for different event types
        event_counts = {
            'ai_output': 0,
            'ai_chunk_debug': 0,
            'ai_response_chunk': 0,
            'code_chunk': 0,
            'file_write': 0,
            'execution_step': 0
        }

        print(f"🔍 Start streaming events.....")
        
        stream_event_count = 0
        while not coder_task.done():
            try:
                # Lấy event từ stream với timeout ngắn
                event = await asyncio.wait_for(stream_generator.__anext__(), timeout=0.1)
                event_type = event.get("type", "message")
                data = event.get("data", {})
                
                stream_event_count += 1
                print(f"🌊 Chat stream event #{stream_event_count}: {event_type}")
                
                # Track event counts
                if event_type in event_counts:
                    event_counts[event_type] += 1
                
                # Add sequence number for tracking
                data["sequence"] = event_counts.get(event_type, 0)
                
                print(f"🔍 Event type: {event_type}")
                print(f"🔍 Data: {data}")

                event_json = json.dumps(data)
                sse_output = f"event: {event_type}\ndata: {event_json}\n\n"
                print(f"📡 Yielding SSE: {sse_output[:100]}...")
                yield sse_output
                
                # Special handling for code chunks - simulate progressive code generation
                if event_type == "ai_output" and "message" in data:
                    # Simulate code streaming for demo purposes
                    message = data["message"]
                    if any(keyword in message.lower() for keyword in ['html', 'css', 'javascript', 'function', 'class', 'div']):
                        # Stream as code chunk
                        streaming_io.stream_code_chunk(message[:50], request.files[0] if request.files else "generated.html")
                
            except asyncio.TimeoutError:
                # Gửi heartbeat với more details
                heartbeat_sse = f"event: heartbeat\ndata: {json.dumps({'status': 'alive', 'events_processed': sum(event_counts.values()), 'stream_events': stream_event_count})}\n\n"
                print(f"💓 Sending heartbeat (stream events: {stream_event_count})")
                yield heartbeat_sse
            except StopAsyncIteration:
                print(f"🏁 Stream iteration ended, total stream events: {stream_event_count}")
                break
        
        # Lấy kết quả từ coder
        print(f"🔍 Start getting response from coder.....")
        response = await coder_task
        print(f"🔍 Response: {response}")
        streaming_io.stop_streaming()
        
        # Stream final analysis
        yield f"event: execution_step\ndata: {json.dumps({'step': 'analyzing_results', 'message': 'Analyzing generated code...', 'status': 'running'})}\n\n"
        
        # Debug: Check state after coder run
        print(f"🔍 Edited files after coder: {list(getattr(coder, 'aider_edited_files', []))}")
        print(f"🔍 Response type: {type(response)}")
        print(f"🔍 Response: {str(response)[:100]}..." if response else "🔍 Response: None")
        
        # Enhanced file processing with streaming
        if request.files and len(request.files) > 0:
            for file in request.files:
                yield f"event: execution_step\ndata: {json.dumps({'step': 'processing_file', 'message': f'Processing {file}...', 'status': 'running'})}\n\n"
                
                # Check if file exists and read content
                if os.path.exists(file):
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Stream file analysis
                    lines = len(content.split('\n'))
                    chars = len(content)
                    
                    yield f"event: file_analysis\ndata: {json.dumps({'filename': file, 'lines': lines, 'characters': chars, 'message': f'📊 {file}: {lines} lines, {chars} characters'})}\n\n"
                    
                    # Stream code preview
                    preview = content[:300] + ("..." if len(content) > 300 else "")
                    yield f"event: code_preview\ndata: {json.dumps({'filename': file, 'preview': preview, 'message': f'Preview of {file}'})}\n\n"
                    
                    # Ensure file is tracked
                    if not hasattr(coder, 'aider_edited_files'):
                        coder.aider_edited_files = set()
                    coder.aider_edited_files.add(os.path.abspath(file))
                    
                    yield f"event: execution_step\ndata: {json.dumps({'step': 'file_processed', 'message': f'✅ {file} processed successfully', 'status': 'complete'})}\n\n"
        
        # Xử lý file extraction nếu cần
        await handle_file_extraction(request, response, streaming_io, coder)
        
        # Debug: Check state after file extraction
        print(f"🔍 Edited files after extraction: {list(getattr(coder, 'aider_edited_files', []))}")
        
        # Lấy edited files SAU khi đã xử lý file extraction
        edited_files = await get_edited_files(coder, streaming_io, request.files)
        print(f"🔍 Final edited files count: {len(edited_files)}")
        
        # Stream final results
        yield f"event: execution_step\ndata: {json.dumps({'step': 'generating_summary', 'message': 'Generating result summary...', 'status': 'running'})}\n\n"
        
        # Emit response event - với enhanced content
        if edited_files and len(edited_files) > 0:
            file_content = edited_files[0].get("content", "")
            file_name = edited_files[0].get("name", "unknown")
            
            # Stream file summary
            yield f"event: file_summary\ndata: {json.dumps({'filename': file_name, 'content_length': len(file_content), 'message': f'Generated {file_name} with {len(file_content)} characters'})}\n\n"
            
            # Stream response with metadata
            yield f"event: response\ndata: {json.dumps({'message': file_content, 'filename': file_name, 'type': 'file_content'})}\n\n"
        else:
            yield f"event: response\ndata: {json.dumps({'message': 'ERROR: No files were edited. Please ensure the AI actually modifies the files.', 'type': 'error'})}\n\n"
        
        # Stream completion statistics
        completion_stats = {
            'files_modified': len(edited_files),
            'events_streamed': sum(event_counts.values()),
            'total_characters': sum(len(f.get('content', '')) for f in edited_files)
        }
        
        yield f"event: completion_stats\ndata: {json.dumps(completion_stats)}\n\n"
        
        # Use Aider's native chat history management
        if response and edited_files and len(edited_files) > 0:
            # Move current conversation to done_messages for future context
            commit_message = f"Updated {len(edited_files)} file(s) via API"
            coder.move_back_cur_messages(commit_message)
            print(f"🔄 Moved conversation to done_messages for session {session_id}")
        
        # Emit final result với enhanced data
        final_result = {
            "response": edited_files[0].get("content", "") if edited_files and len(edited_files) > 0 else "ERROR: No files were edited",
            "edited_files": edited_files,
            "session_id": session_id,
            "tokens_sent": getattr(coder, 'message_tokens_sent', 0),
            "tokens_received": getattr(coder, 'message_tokens_received', 0),
            "cost": getattr(coder, 'message_cost', 0.0),
            "statistics": completion_stats
        }
        
        yield f"event: complete\ndata: {json.dumps(final_result)}\n\n"
        
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e), 'type': 'exception'})}\n\n"
    finally:
        if streaming_io:
            streaming_io.stop_streaming()
        try:
            os.chdir(original_cwd)
        except:
            pass

async def chat_non_stream(request):
    """
    Non-streaming chat (original logic)
    """
    original_cwd = os.getcwd()
    print(f"🔍 Original cwd: {original_cwd}")
    try:
        session, session_id = get_or_create_session(
            session_id=request.session_id, 
            repo_path=request.repo_path,
            model=request.model,
            files=request.files,
            read_only_files=request.read_only_files,
            edit_format=request.edit_format
        )
        coder = session["coder"]
        io = session["io"]
        
        # Đảm bảo working directory đúng
        repo_path = session.get("repo_path")
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"Chat: Working in directory: {repo_path}")
        
        # Clear buffers trước khi xử lý
        io.clear_buffers()
        
        # Lấy thông tin về file ảnh
        image_files_info = get_image_files_info(coder)
        
        # Chuẩn bị message với instruction rõ ràng
        enhanced_message = create_enhanced_message(request.message, request.files, image_files_info)
        
        # Thực hiện chat
        print(f"🤖 Starting chat with message: {request.message[:100]}...")
        response = coder.run(with_message=enhanced_message, preproc=True)
        print(f"🤖 Chat completed. Response: {response[:100] if response else 'No response'}...")
        
        # Debug: Check what files are in the chat
        if hasattr(coder, 'abs_fnames'):
            print(f"📁 Files in chat: {list(coder.abs_fnames)}")
        if hasattr(coder, 'aider_edited_files'):
            print(f"✏️ Edited files: {list(coder.aider_edited_files) if coder.aider_edited_files else 'None'}")
        
        # Xử lý file extraction
        await handle_file_extraction(request, response, io, coder)
        
        # Force flush any pending file writes
        if hasattr(coder, 'repo') and coder.repo:
            try:
                coder.repo.commit_if_dirty("API chat changes")
                print("📝 Committed changes to git")
            except Exception as e:
                print(f"⚠️ Git commit failed: {e}")
        
        # Lấy edited files
        edited_files = await get_edited_files(coder, io, request.files)
        
        # Lấy output, errors, warnings
        output = io.get_captured_output()
        errors = io.get_captured_errors()
        warnings = io.get_captured_warnings()
        
        print(f"Edited files: {edited_files}")
        
        # Use Aider's native chat history management
        if response and edited_files and len(edited_files) > 0:
            # Move current conversation to done_messages for future context
            commit_message = f"Updated {len(edited_files)} file(s) via API"
            coder.move_back_cur_messages(commit_message)
            print(f"🔄 Moved conversation to done_messages for session {session_id}")
        
        # Chỉ trả về nội dung file được cập nhật
        if edited_files and len(edited_files) > 0:
            # Trả về nội dung file đầu tiên được edit
            file_content = edited_files[0].get("content", "")
            return {
                "response": file_content,
                "edited_files": edited_files,
                "session_id": session_id,
                "tokens_sent": getattr(coder, 'message_tokens_sent', 0),
                "tokens_received": getattr(coder, 'message_tokens_received', 0),
                "cost": getattr(coder, 'message_cost', 0.0),
                "output": "",
                "errors": errors,
                "warnings": ""
            }
        else:
            # Nếu không có file nào được edit, trả về lỗi
            return {
                "response": "ERROR: No files were edited. Please ensure the AI actually modifies the files.",
                "edited_files": [],
                "session_id": session_id,
                "tokens_sent": getattr(coder, 'message_tokens_sent', 0),
                "tokens_received": getattr(coder, 'message_tokens_received', 0),
                "cost": getattr(coder, 'message_cost', 0.0),
                "output": "",
                "errors": errors,
                "warnings": ""
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    finally:
        try:
            os.chdir(original_cwd)
        except:
            pass

async def list_models():
    """
    Lấy danh sách model được hỗ trợ
    """
    try:
        from aider.models import OPENAI_MODELS, ANTHROPIC_MODELS, MODEL_ALIASES
        
        models_data = {
            "openai": OPENAI_MODELS,
            "anthropic": ANTHROPIC_MODELS,
            "aliases": MODEL_ALIASES
        }
        
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

async def add_file_to_session(session_id: str, file_path: str):
    """
    Thêm file vào session chat
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    coder = session["coder"]
    
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_path} not found")
        
        coder.add_rel_fname(file_path)
        return {"success": True, "message": f"Added {file_path} to the chat"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def create_session_controller(session_request):
    """
    Tạo session mới
    """
    try:
        # Nếu không có repo_path, tạo thư mục mới với UUID trong folder temp
        repo_path = session_request.repo_path
        files = session_request.files or []
        
        if not repo_path:
            repo_path = create_temp_repo(files)
        
        _, session_id = get_or_create_session(
            repo_path=repo_path,
            model=session_request.model,
            files=files,
            read_only_files=session_request.read_only_files,
            edit_format=session_request.edit_format,
            auto_commits=session_request.auto_commits
        )
        return {
            "session_id": session_id,
            "message": "Session created successfully",
            "repo_path": repo_path,
            "model": session_request.model,
            "files": files,
            "read_only_files": session_request.read_only_files or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

async def delete_session_controller(session_id: str):
    """
    Xóa session
    """
    success = session_manager.delete_session(session_id)
    if success:
        return {"success": True, "message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

async def get_session_files(session_id: str):
    """
    Lấy danh sách file trong session
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    coder = session["coder"]
    files = coder.get_inchat_relative_files()
    return {"files": files}

async def get_file_content_controller(session_id: str, file_path: str):
    """
    Lấy nội dung file
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    coder = session["coder"]
    io = session["io"]
    
    try:
        abs_path = coder.abs_root_path(file_path)
        content = io.read_text(abs_path)
        
        if content is None:
            raise HTTPException(status_code=404, detail=f"File {file_path} not found or cannot be read")
        
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def check_file_controller(file_path: str, repo_path: str = None):
    """
    Kiểm tra nội dung file
    """
    try:
        original_cwd = os.getcwd()
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "exists": True,
                "path": os.path.abspath(file_path),
                "content": content,
                "size": len(content)
            }
        else:
            return {
                "exists": False,
                "path": os.path.abspath(file_path) if repo_path else file_path,
                "error": "File not found"
            }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }
    finally:
        os.chdir(original_cwd)

async def upload_file_controller(session_id: str, file: UploadFile, add_to_chat: bool = False):
    """
    Upload file vào repo_path của session
    """
    try:
        # Kiểm tra session có tồn tại không
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Lấy repo_path từ session
        repo_path = session.get("repo_path")
        if not repo_path or not os.path.exists(repo_path):
            raise HTTPException(status_code=400, detail="Session repo_path not found or invalid")
        
        # Tạo đường dẫn file đích
        file_path = os.path.join(repo_path, file.filename)
        
        # Kiểm tra file đã tồn tại
        if os.path.exists(file_path):
            # Tạo tên file mới với timestamp để tránh trùng
            name, ext = os.path.splitext(file.filename)
            timestamp = int(time.time())
            new_filename = f"{name}_{timestamp}{ext}"
            file_path = os.path.join(repo_path, new_filename)
        
        # Lưu file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Lấy thông tin file
        file_size = os.path.getsize(file_path)
        file_type = file.content_type or "unknown"
        relative_path = os.path.relpath(file_path, repo_path)
        
        print(f"📁 Uploaded file: {file_path} ({file_size} bytes)")
        
        # Thêm file vào chat session nếu được yêu cầu
        if add_to_chat:
            try:
                coder = session["coder"]
                file_ext = os.path.splitext(file.filename)[1].lower()
                
                # Thêm file text vào chat
                text_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.csv']
                if file_ext in text_extensions:
                    coder.add_rel_fname(relative_path)
                    print(f"📝 Added text file {relative_path} to chat session")
                
                # Thêm file ảnh vào read-only files để AI biết có ảnh
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
                if file_ext in image_extensions:
                    abs_path = os.path.abspath(file_path)
                    coder.abs_read_only_fnames.add(abs_path)
                    print(f"🖼️ Added image file {relative_path} to chat session as read-only")
                
                # Các file khác cũng có thể thêm vào read-only
                other_extensions = ['.pdf', '.doc', '.docx']
                if file_ext in other_extensions:
                    abs_path = os.path.abspath(file_path)
                    coder.abs_read_only_fnames.add(abs_path)
                    print(f"📎 Added document file {relative_path} to chat session as read-only")
                    
            except Exception as e:
                print(f"⚠️ Failed to add file to chat: {e}")
        
        return {
            "success": True,
            "message": f"File uploaded successfully: {os.path.basename(file_path)}",
            "file_path": relative_path,
            "file_size": file_size,
            "file_type": file_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def list_files_controller(session_id: str):
    """
    Lấy danh sách tất cả file trong repo_path của session
    """
    try:
        # Kiểm tra session có tồn tại không
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Lấy repo_path từ session
        repo_path = session.get("repo_path")
        if not repo_path or not os.path.exists(repo_path):
            raise HTTPException(status_code=400, detail="Session repo_path not found or invalid")
        
        # Lấy danh sách file trong chat
        coder = session["coder"]
        chat_files = set()
        if hasattr(coder, 'abs_fnames'):
            chat_files = {coder.get_rel_fname(abs_file) for abs_file in coder.abs_fnames}
        
        # Duyệt tất cả file trong repo_path
        files_info = []
        repo_path_obj = Path(repo_path)
        
        for file_path in repo_path_obj.rglob('*'):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(repo_path_obj)
                    stat = file_path.stat()
                    
                    # Xác định type từ extension
                    suffix = file_path.suffix.lower()
                    if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        file_type = 'image'
                    elif suffix in ['.pdf']:
                        file_type = 'pdf'
                    elif suffix in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
                        file_type = 'text'
                    elif suffix in ['.doc', '.docx']:
                        file_type = 'document'
                    else:
                        file_type = 'other'
                    
                    files_info.append({
                        "name": file_path.name,
                        "path": str(relative_path),
                        "size": stat.st_size,
                        "type": file_type,
                        "modified_time": stat.st_mtime,
                        "in_chat": str(relative_path) in chat_files
                    })
                except Exception as e:
                    print(f"⚠️ Error processing file {file_path}: {e}")
                    continue
        
        # Sắp xếp theo thời gian modified (mới nhất trước)
        files_info.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "files": files_info,
            "total_count": len(files_info)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List files failed: {str(e)}")

async def clear_chat_history_controller(session_id: str):
    """
    Clear chat history của session (giống /clear command)
    """
    try:
        # Kiểm tra session có tồn tại không
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Lấy coder từ session
        coder = session["coder"]
        
        # Đếm số message trước khi clear
        total_messages = len(getattr(coder, 'done_messages', [])) + len(getattr(coder, 'cur_messages', []))
        
        # Clear chat history giống như /clear command
        coder.done_messages = []
        coder.cur_messages = []
        
        # Clear buffers trong IO
        io = session["io"]
        if hasattr(io, 'clear_buffers'):
            io.clear_buffers()
        
        # Reset commit hashes để tránh conflict với undo
        if hasattr(coder, 'aider_commit_hashes'):
            coder.aider_commit_hashes = set()
        
        print(f"🧹 Cleared chat history for session {session_id} ({total_messages} messages)")
        
        return {
            "success": True,
            "message": "Chat history cleared successfully. The AI can't see anything before this point.",
            "cleared_messages": total_messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear chat failed: {str(e)}")

async def sync_file_controller(request):
    """
    Đồng bộ nội dung file trong repo_path của session
    """
    try:
        # Kiểm tra session có tồn tại không
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Lấy repo_path từ session
        repo_path = session.get("repo_path")
        if not repo_path or not os.path.exists(repo_path):
            raise HTTPException(status_code=400, detail="Session repo_path not found or invalid")
        
        # Tạo đường dẫn file đầy đủ
        file_path = os.path.join(repo_path, request.file_path)
        
        # Kiểm tra file có nằm trong repo_path không (security check)
        try:
            # Resolve để tránh path traversal attacks
            resolved_file_path = os.path.realpath(file_path)
            resolved_repo_path = os.path.realpath(repo_path)
            
            if not resolved_file_path.startswith(resolved_repo_path):
                raise HTTPException(status_code=400, detail="File path must be within session repo directory")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Kiểm tra file có tồn tại không
        file_exists = os.path.exists(file_path)
        was_created = False
        
        if not file_exists and not request.create_if_not_exists:
            raise HTTPException(status_code=404, detail=f"File {request.file_path} not found and create_if_not_exists is False")
        
        # Tạo thư mục parent nếu cần
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            print(f"📁 Created directory: {parent_dir}")
        
        # Ghi nội dung vào file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
            
            if not file_exists:
                was_created = True
                print(f"📝 Created new file: {request.file_path}")
            else:
                print(f"✏️ Updated existing file: {request.file_path}")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")
        
        # Lấy thông tin file
        file_size = os.path.getsize(file_path)
        
        # Kiểm tra file có trong chat session không
        coder = session["coder"]
        in_chat = False
        if hasattr(coder, 'abs_fnames'):
            abs_file_path = os.path.abspath(file_path)
            in_chat = abs_file_path in coder.abs_fnames
        
        # Thêm file vào chat session nếu được yêu cầu
        if request.add_to_chat and not in_chat:
            try:
                file_ext = os.path.splitext(request.file_path)[1].lower()
                
                # Thêm file text vào chat
                text_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.csv', '.ts', '.jsx', '.tsx']
                if file_ext in text_extensions:
                    coder.add_rel_fname(request.file_path)
                    in_chat = True
                    print(f"📝 Added {request.file_path} to chat session")
                else:
                    # Thêm file khác vào read-only
                    abs_path = os.path.abspath(file_path)
                    coder.abs_read_only_fnames.add(abs_path)
                    in_chat = True
                    print(f"📎 Added {request.file_path} to chat session as read-only")
                    
            except Exception as e:
                print(f"⚠️ Failed to add file to chat: {e}")
        
        return {
            "success": True,
            "message": f"File {'created' if was_created else 'updated'} successfully: {request.file_path}",
            "file_path": request.file_path,
            "file_size": file_size,
            "was_created": was_created,
            "in_chat": in_chat
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync file failed: {str(e)}")

async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": time.time()} 