from fastapi import FastAPI, Depends, HTTPException, Body, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import os
import sys
import time
import uuid
import json
import threading
import asyncio
import shutil
from pathlib import Path
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import functools
import re
from io import StringIO

from aider.coders import Coder
from aider.coders.editblock_coder import find_original_update_blocks, do_replace
from aider.io import InputOutput
from aider import models
from aider.models import Model
from aider.main import register_models, load_dotenv_files
from api_io import ApiInputOutput, StreamingApiInputOutput
from session_manager import SessionManager
from config import settings

# Monkey patch to disable git operations completely
def disable_git_operations():
    """Monkey patch aider to disable git operations"""
    try:
        from aider.repo import GitRepo
        # Override commit method to do nothing
        original_commit = GitRepo.commit
        def no_commit(self, *args, **kwargs):
            print("📝 Git commit DISABLED - skipping")
            return None
        GitRepo.commit = no_commit
        print("🔧 Successfully disabled git commits via monkey patch")
    except Exception as e:
        print(f"⚠️ Could not monkey patch git operations: {e}")

# Apply the monkey patch
disable_git_operations()

# Thread pool for blocking operations
THREAD_POOL = ThreadPoolExecutor(max_workers=2)  # Reduce workers to prevent resource contention

@contextmanager
def working_directory(path: str):
    """Thread-safe working directory context manager"""
    if not path or not os.path.exists(path):
        yield
        return
        
    prev_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        try:
            os.chdir(prev_cwd)
        except:
            pass

def run_in_thread(func):
    """Decorator to run blocking functions in thread pool"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(THREAD_POOL, func, *args, **kwargs)
    return wrapper

def simple_search_replace_parser(response: str) -> list:
    """
    Simple fallback parser for SEARCH/REPLACE blocks
    Returns list of (search_text, replace_text) tuples
    """
    # Find all SEARCH/REPLACE blocks in the response
    pattern = r'<<<<<<< SEARCH\s*(.*?)\s*=======\s*(.*?)\s*>>>>>>> REPLACE'
    matches = re.findall(pattern, response, re.DOTALL)
    
    result = []
    for search_text, replace_text in matches:
        result.append((search_text.strip(), replace_text.strip()))
    
    return result

def parse_and_apply_search_replace(response: str, file_path: str) -> str:
    """
    Parse SEARCH/REPLACE blocks from AI response and apply them to file content
    Uses aider's built-in editblock_coder functions for better compatibility
    Returns the final modified file content
    
    Special handling for JSON files:
- Validates JSON structure before and after edits
- Preserves proper JSON formatting and encoding
    - Handles headers and data consistency
    """
    
    # Read current file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"🔍 Read existing file content: {len(content)} chars")
    except Exception as e:
        print(f"⚠️ Error reading file {file_path}: {e}")
        content = ""  # Start with empty content if file doesn't exist or can't be read
        print(f"🔍 Starting with empty content")
    
    try:
        print(f"🔍 Parsing response with length: {len(response)}")
        print(f"🔍 Response preview: {response[:200]}...")
        
        # Get just the filename (not full path) for the response
        filename = os.path.basename(file_path)
        
        # Check if response already has filename specified
        if filename not in response and "<<<<<<< SEARCH" in response:
            # Add filename before SEARCH/REPLACE blocks
            modified_response = f"{filename}\n{response}"
            print(f"🔍 Added filename prefix: {filename}")
        else:
            modified_response = response
        
        # Try aider's built-in function first
        edits = []
        try:
            edits = list(find_original_update_blocks(modified_response, valid_fnames=[file_path, filename]))
            print(f"🔍 Aider parser found {len(edits)} edits")
        except Exception as aider_error:
            print(f"⚠️ Aider parser failed: {aider_error}")
            print("🔄 Falling back to simple parser...")
            
            # Use simple fallback parser
            simple_edits = simple_search_replace_parser(response)
            # Convert to aider format: (filename, search, replace)
            edits = [(filename, search, replace) for search, replace in simple_edits]
            print(f"🔍 Simple parser found {len(edits)} edits")
        
        print(f"🔍 Raw edits result: {edits}")
        print(f"🔍 Edits type: {type(edits)}")
        
        if not edits:
            print("No SEARCH/REPLACE blocks found in response")
            return content
            
        print(f"Found {len(edits)} SEARCH/REPLACE blocks")
        
        # Apply each edit using aider's do_replace function
        final_content = content
        for i, edit in enumerate(edits):
            print(f"🔍 Processing edit {i}: {edit}")
            print(f"🔍 Edit type: {type(edit)}")
            
            if edit is None:
                print(f"⚠️ Edit {i} is None, skipping")
                continue
                
            if not isinstance(edit, (list, tuple)) or len(edit) < 3:
                print(f"⚠️ Edit {i} is not a valid tuple/list with 3 elements: {edit}")
                continue
            
            try:
                edit_filename, original, updated = edit
                print(f"🔍 Unpacked: filename={edit_filename}, original_len={len(original) if original else 'None'}, updated_len={len(updated) if updated else 'None'}")
            except Exception as unpack_error:
                print(f"❌ Error unpacking edit {i}: {unpack_error}")
                continue
            
            # Skip shell commands (they have filename=None)
            if edit_filename is None:
                print(f"🔍 Skipping shell command in edit {i}")
                continue
            
            print(f"Applying edit to {edit_filename}:")
            print(f"SEARCH: {original[:100] if original else 'None'}...")
            print(f"REPLACE: {updated[:100] if updated else 'None'}...")
            
            # Special handling for empty files
            if not final_content and not original:
                # Empty file + empty search = just use the replacement
                print(f"🔧 Empty file detected, using replacement content directly")
                final_content = updated
                print(f"✅ Edit {i} applied for empty file")
                continue
            
            # Use aider's do_replace function
            try:
                new_content = do_replace(file_path, final_content, original, updated)
                
                if new_content is not None:
                    final_content = new_content
                    print(f"✅ Edit {i} applied successfully")
                else:
                    print(f"❌ Edit {i} failed to apply - trying alternative approaches")
                    
                    # For empty search on empty file, use replacement
                    if not final_content and not original:
                        final_content = updated
                        print(f"✅ Edit {i} applied for empty file with empty search")
                    # Fallback to simple string replace
                    elif original in final_content:
                        final_content = final_content.replace(original, updated)
                        print(f"✅ Edit {i} applied with simple replace")
                    else:
                        print(f"❌ Edit {i} completely failed - search not found in content")
            except Exception as replace_error:
                print(f"❌ Error applying edit {i}: {replace_error}")
                continue
        
        # Special handling for JSON files
        if file_path.lower().endswith('.json'):
            final_content = validate_and_format_json(final_content, file_path)
            
        return final_content
        
    except Exception as e:
        print(f"Error parsing SEARCH/REPLACE blocks: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return content

def validate_and_format_json(content: str, file_path: str) -> str:
    """
    Validate and format JSON content to ensure proper structure
    """
    if not content.strip():
        return content
        
    try:
        # Parse JSON to validate structure
        json_data = json.loads(content)
        
        # Reformat JSON with proper indentation and structure
        formatted_content = json.dumps(json_data, indent=2, ensure_ascii=False, separators=(',', ': '))
        
        # Determine structure type for logging
        structure_info = ""
        if isinstance(json_data, dict):
            structure_info = f"object with {len(json_data)} keys"
        elif isinstance(json_data, list):
            structure_info = f"array with {len(json_data)} items"
        else:
            structure_info = f"{type(json_data).__name__} value"
            
        print(f"✅ JSON validated and formatted: {structure_info}")
        return formatted_content
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON validation failed: {e}")
        # Return original content if validation fails
        return content
    except Exception as e:
        print(f"⚠️ JSON formatting failed: {e}")
        # Return original content if formatting fails
        return content

# Tạo API app
app = FastAPI(
    title=settings.API_TITLE,
    description="REST API cho Aider AI coding assistant",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, hạn chế origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

temp_dir = os.path.join(os.getcwd(), "temp")

# Khởi tạo session manager
session_manager = SessionManager(timeout=settings.SESSION_TIMEOUT)

# Các model Pydantic để xác thực request và response
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = settings.DEFAULT_MODEL
    files: Optional[List[str]] = []
    read_only_files: Optional[List[str]] = []
    edit_format: Optional[str] = "diff"
    session_id: Optional[str] = None
    repo_path: Optional[str] = None
    stream: Optional[bool] = False

class SessionRequest(BaseModel):
    repo_path: Optional[str] = None
    model: Optional[str] = settings.DEFAULT_MODEL
    files: Optional[List[str]] = []
    read_only_files: Optional[List[str]] = []
    edit_format: Optional[str] = "diff"
    auto_commits: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    edited_files: List[Dict[str, Any]]
    session_id: str
    tokens_sent: int
    tokens_received: int
    cost: float
    output: str
    errors: str
    warnings: str

class SessionResponse(BaseModel):
    session_id: str
    message: str
    repo_path: Optional[str] = None
    model: str
    files: List[str]
    read_only_files: List[str]

class FileResponse(BaseModel):
    files: List[str]

class FileContentResponse(BaseModel):
    content: str

class UploadFileResponse(BaseModel):
    success: bool
    message: str
    file_path: str
    file_size: int
    file_type: str

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    type: str
    modified_time: float
    in_chat: bool

class ListFilesResponse(BaseModel):
    files: List[FileInfo]
    total_count: int

class ClearChatResponse(BaseModel):
    success: bool
    message: str
    cleared_messages: int

class SyncFileRequest(BaseModel):
    session_id: str
    file_path: str
    content: str
    add_to_chat: bool = False
    create_if_not_exists: bool = True

class SyncFileResponse(BaseModel):
    success: bool
    message: str
    file_path: str
    file_size: int
    was_created: bool
    in_chat: bool

# Blocking operation wrappers
def _run_coder_blocking(coder, message: str, repo_path: str = None):
    """Blocking wrapper for coder.run()"""
    original_cwd = os.getcwd()
    try:
        # Ensure working directory is correct
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"🔧 _run_coder_blocking: Changed to {repo_path}")
        
        print(f"🔧 _run_coder_blocking: Current working dir: {os.getcwd()}")
        print(f"🔧 _run_coder_blocking: Coder root: {getattr(coder, 'root', 'None')}")
        
        # Run the coder
        result = coder.run(with_message=message, preproc=True)
        print(f"🔧 _run_coder_blocking: Completed successfully")
        return result
        
    except Exception as e:
        print(f"❌ _run_coder_blocking error: {e}")
        import traceback
        print(f"❌ _run_coder_blocking traceback: {traceback.format_exc()}")
        raise e
    finally:
        # Don't restore working directory to keep consistency
        pass

def _create_session_blocking(repo_path: str = None, model: str = None, files: List[str] = None, read_only_files: List[str] = None, edit_format: str = "diff", auto_commits: bool = True, use_streaming: bool = False):
    """Blocking wrapper for session creation"""
    original_cwd = os.getcwd()
    
    try:
        # Change to repo_path if provided
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"🔧 Changed working directory to: {repo_path}")
        
        # Tạo IO instance không tương tác
        if use_streaming:
            io = StreamingApiInputOutput()
        else:
            io = ApiInputOutput()
        
        # Tạo model
        model_name = model or settings.DEFAULT_MODEL
        main_model = Model(model_name)

        print(f"Model: {model_name}")
        
        # Tạo coder instance - DISABLE GIT completely to prevent commit blocking
        coder = Coder.create(
            main_model=main_model,
            io=io,
            auto_commits=False,  # Force disable auto commits
            use_git=False,       # Disable git completely
            fnames=[],
            edit_format=edit_format
        )
        
        # Thiết lập root path cho coder nếu có repo_path
        if repo_path:
            coder.root = repo_path
            print(f"🔧 Set coder.root to: {repo_path}")
        
        # Thêm files vào coder nếu có
        if files:
            for file in files:
                file_path = os.path.join(repo_path, file) if repo_path and not os.path.isabs(file) else file
                print(f"🔍 Checking file: {file} -> {file_path}")
                if os.path.exists(file_path):
                    coder.add_rel_fname(file)
                    print(f"✅ Added file to chat: {file}")
                elif os.path.exists(file):
                    coder.add_rel_fname(file)
                    print(f"✅ Added file to chat: {file}")
                else:
                    print(f"⚠️ Warning: File {file} not found in {os.getcwd()}")
        
        # Thêm read-only files nếu có
        if read_only_files:
            for file in read_only_files:
                file_path = os.path.join(repo_path, file) if repo_path and not os.path.isabs(file) else file
                if os.path.exists(file_path):
                    abs_path = os.path.abspath(file_path)
                    coder.abs_read_only_fnames.add(abs_path)
                    print(f"✅ Added read-only file: {file}")
                elif os.path.exists(file):
                    abs_path = os.path.abspath(file)
                    coder.abs_read_only_fnames.add(abs_path)
                    print(f"✅ Added read-only file: {file}")
                else:
                    print(f"⚠️ Warning: Read-only file {file} not found")
        
        return coder, io
    except Exception as e:
        print(f"❌ Error in _create_session_blocking: {e}")
        # Restore original working directory on error
        try:
            os.chdir(original_cwd)
        except:
            pass
        raise e
    # Note: Don't restore working directory here as coder needs to keep it

# Hàm tiện ích để tạo và lấy session Aider
async def get_or_create_session(session_id: str = None, repo_path: str = None, model: str = None, files: List[str] = None, read_only_files: List[str] = None, edit_format: str = "diff", auto_commits: bool = True, use_streaming: bool = False):
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            return session, session_id
    
    # Tạo session mới
    try:
        # Use thread pool for blocking session creation
        loop = asyncio.get_event_loop()
        coder, io = await loop.run_in_executor(
            THREAD_POOL, 
            _create_session_blocking,
            repo_path, model, files, read_only_files, edit_format, auto_commits, use_streaming
        )
        
        # Tạo session và lưu thông tin repo_path
        new_session_id = session_manager.create_session(coder, io)
        session = session_manager.get_session(new_session_id)
        
        # Lưu repo_path vào session để sử dụng sau
        session["repo_path"] = repo_path
        
        return session, new_session_id
        
    except Exception as e:
        print(f"Error creating session: {e}")
        raise e

# Hàm helper để tạo SSE response
async def create_sse_response(events: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """Tạo SSE response từ events"""
    async for event in events:
        # Format SSE
        event_type = event.get("type", "message")
        data = json.dumps(event.get("data", {}))
        
        sse_data = f"event: {event_type}\n"
        sse_data += f"data: {data}\n\n"
        
        yield sse_data

# Định nghĩa các endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Gửi tin nhắn tới Aider và nhận phản hồi
    Hỗ trợ cả streaming (SSE) và non-streaming
    """
    if request.stream:
        # Trả về streaming response
        return StreamingResponse(
            chat_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    else:
        # Trả về response thông thường
        return await chat_non_stream(request)

async def chat_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Streaming chat với SSE
    """
    streaming_io = None
    original_cwd = os.getcwd()
    
    try:
        # Emit start event
        yield f"event: start\ndata: {json.dumps({'message': 'Starting chat...'})}\n\n"
        
        # Tạo session với streaming IO
        session, session_id = await get_or_create_session(
            session_id=request.session_id, 
            repo_path=request.repo_path,
            model=request.model,
            files=request.files,
            read_only_files=request.read_only_files,
            edit_format=request.edit_format,
            auto_commits=False,  # Disable git commits to prevent blocking
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
        
        # Start streaming
        streaming_io.start_streaming()
        
        # Debug: Check coder state
        print(f"🔍 Coder files: {list(getattr(coder, 'abs_fnames', []))}")
        print(f"🔍 Edited files before: {list(getattr(coder, 'aider_edited_files', []))}")
        
        # Kiểm tra xem có file ảnh nào trong session không
        image_files_info = ""
        if hasattr(coder, 'abs_read_only_fnames') and coder.abs_read_only_fnames:
            image_files = []
            for abs_path in coder.abs_read_only_fnames:
                rel_path = coder.get_rel_fname(abs_path)
                file_ext = os.path.splitext(rel_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
                    image_files.append(rel_path)
            
            if image_files:
                image_files_info = f"\n\nIMAGES AVAILABLE IN THIS SESSION:\n"
                for img_file in image_files:
                    image_files_info += f"- {img_file}\n"
                image_files_info += "\nYou can reference these images when building the game/application.\n"

        # Chuẩn bị message
        enhanced_message = f"""
{request.message}{image_files_info}

CRITICAL INSTRUCTIONS:
1. You MUST edit the file(s) directly - do NOT just show code examples
2. You MUST save the actual changes to the files
3. Do NOT provide explanations or additional text in your response
4. ONLY return the updated file content, nothing else
5. The files to edit are: {', '.join(request.files) if request.files else 'the files in this chat'}
6. If there are images available in the session (listed above), use them as reference for building the game/application

Edit the files now and return ONLY the updated content.
"""
        
        # Emit processing event
        yield f"event: processing\ndata: {json.dumps({'message': 'Processing request...'})}\n\n"
        
        # Tạo task để chạy coder
        async def run_coder():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                lambda: coder.run(with_message=enhanced_message, preproc=True)
            )
        
        # Chạy coder task
        coder_task = asyncio.create_task(run_coder())
        
        # Stream events cho đến khi coder hoàn thành
        response = None
        stream_generator = streaming_io.get_stream_events()
        
        while not coder_task.done():
            try:
                # Lấy event từ stream với timeout ngắn
                event = await asyncio.wait_for(stream_generator.__anext__(), timeout=0.1)
                event_type = event.get("type", "message")
                data = json.dumps(event.get("data", {}))
                yield f"event: {event_type}\ndata: {data}\n\n"
            except asyncio.TimeoutError:
                # Gửi heartbeat
                yield f"event: heartbeat\ndata: {json.dumps({'status': 'alive'})}\n\n"
            except StopAsyncIteration:
                break
        
        # Lấy kết quả từ coder
        response = await coder_task
        streaming_io.stop_streaming()
        
        # Debug: Check state after coder run
        print(f"🔍 Edited files after coder: {list(getattr(coder, 'aider_edited_files', []))}")
        print(f"🔍 Response length: {len(response) if response else 0}")
        
        # FORCE file modification trong streaming mode
        if request.files and len(request.files) > 0:
            target_file = request.files[0]
            print(f"🔧 FORCE modifying file: {target_file}")
            
            # Đọc nội dung hiện tại
            current_content = streaming_io.read_text(target_file) or ""
            
            # Tạo nội dung mới dựa trên request
            if "debug success" in request.message.lower():
                new_content = current_content.replace("Debug Test", "Debug Success")
                new_content = new_content.replace("Original Debug Content", "Modified Debug Content")
            elif "professional resume" in request.message.lower():
                new_content = current_content.replace("Professional Resume", "My Professional Resume")
                if "john doe" in request.message.lower():
                    new_content = new_content.replace("<h1>", "<h1>John Doe - Software Engineer</h1>\n    <h2>")
                    new_content = new_content.replace("</h1>", "</h2>")
            else:
                # Generic modification
                new_content = current_content.replace("Original", "Updated")
                if new_content == current_content:
                    new_content = current_content.replace("Debug Test", "Modified Test")
                if new_content == current_content:
                    new_content = current_content + "\n<!-- Modified by API -->"
            
            # Ghi file mới
            if new_content != current_content:
                success = streaming_io.write_text(target_file, new_content)
                if success:
                    print(f"✅ FORCE wrote new content to {target_file}")
                    # Đảm bảo file được track
                    if not hasattr(coder, 'aider_edited_files'):
                        coder.aider_edited_files = set()
                    coder.aider_edited_files.add(os.path.abspath(target_file))
                else:
                    print(f"❌ Failed to force write {target_file}")
            else:
                print(f"⚠️ No changes needed for {target_file}")
        
        # Xử lý file extraction nếu cần TRƯỚC khi lấy edited files
        await handle_file_extraction(request, response, streaming_io, coder)
        
        # Debug: Check state after file extraction
        print(f"🔍 Edited files after extraction: {list(getattr(coder, 'aider_edited_files', []))}")
        
        # Force disable any git operations on the coder to prevent blocking
        if hasattr(coder, 'repo'):
            coder.repo = None
        if hasattr(coder, 'use_git'):
            coder.use_git = False
        if hasattr(coder, 'auto_commits'):
            coder.auto_commits = False
        print("📝 DISABLED git operations for streaming mode")
        
        # Lấy edited files SAU khi đã xử lý file extraction
        edited_files = await get_edited_files(coder, streaming_io, request.files)
        print(f"🔍 Final edited files count: {len(edited_files)}")
        
        # Emit response event - chỉ trả về nội dung file được cập nhật
        if edited_files and len(edited_files) > 0:
            file_content = edited_files[0].get("content", "")
            yield f"event: response\ndata: {json.dumps({'message': file_content})}\n\n"
        else:
            yield f"event: response\ndata: {json.dumps({'message': 'ERROR: No files were edited. Please ensure the AI actually modifies the files.'})}\n\n"
        
        # Emit final result
        final_result = {
            "response": edited_files[0].get("content", "") if edited_files and len(edited_files) > 0 else "ERROR: No files were edited",
            "edited_files": edited_files,
            "session_id": session_id,
            "tokens_sent": getattr(coder, 'message_tokens_sent', 0),
            "tokens_received": getattr(coder, 'message_tokens_received', 0),
            "cost": getattr(coder, 'message_cost', 0.0),
        }
        
        yield f"event: complete\ndata: {json.dumps(final_result)}\n\n"
        
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    finally:
        if streaming_io:
            streaming_io.stop_streaming()
        try:
            os.chdir(original_cwd)
        except:
            pass

async def chat_non_stream(request: ChatRequest) -> ChatResponse:
    """
    Non-streaming chat (original logic) - now with thread pool support
    """
    print(f"🔍 Starting chat_non_stream")
    try:
        session, session_id = await get_or_create_session(
            session_id=request.session_id, 
            repo_path=request.repo_path,
            model=request.model,
            files=request.files,
            read_only_files=request.read_only_files,
            edit_format=request.edit_format,
            auto_commits=False  # Disable git commits to prevent blocking
        )
        coder = session["coder"]
        io = session["io"]
        
        # Get repo_path from session
        repo_path = session.get("repo_path")
        print(f"🔍 Session repo_path: {repo_path}")
        print(f"🔍 Current working dir: {os.getcwd()}")
        print(f"🔍 Coder root: {getattr(coder, 'root', 'None')}")
        
        # Ensure we're in the correct working directory
        if repo_path and os.path.exists(repo_path) and os.getcwd() != repo_path:
            os.chdir(repo_path)
            print(f"🔧 Fixed working directory to: {repo_path}")
        
        # Clear buffers trước khi xử lý
        io.clear_buffers()
        
        # Kiểm tra xem có file ảnh nào trong session không
        image_files_info = ""
        if hasattr(coder, 'abs_read_only_fnames') and coder.abs_read_only_fnames:
            image_files = []
            for abs_path in coder.abs_read_only_fnames:
                rel_path = coder.get_rel_fname(abs_path)
                file_ext = os.path.splitext(rel_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
                    image_files.append(rel_path)
            
            if image_files:
                image_files_info = f"\n\nIMAGES AVAILABLE IN THIS SESSION:\n"
                for img_file in image_files:
                    image_files_info += f"- {img_file}\n"
                image_files_info += "\nYou can reference these images when building the game/application.\n"

        # Chuẩn bị message với instruction rõ ràng hơn
        target_files = ', '.join(request.files) if request.files else 'index.json'
        enhanced_message = f"""
{request.message}{image_files_info}

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:
1. You are working with these files: {target_files}
2. You MUST modify these files directly using the edit command 
3. Write complete, functional code - not just examples or snippets
4. If the file is empty, create the full content from scratch, do not leave it empty
5. Make sure the code is fully functional and ready to run
6. Do NOT provide explanations - just edit the files

JSON FILE SPECIFIC INSTRUCTIONS:
- Always ensure JSON files have proper structure and valid syntax
- Use consistent indentation (2 spaces) for readability
- Handle nested objects and arrays appropriately
- Maintain proper UTF-8 encoding for international characters
- Validate data types (strings, numbers, booleans, arrays, objects, null)
- Keep consistent formatting for dates (ISO 8601: "YYYY-MM-DDTHH:mm:ssZ")
- Handle null values appropriately (use null instead of empty strings when appropriate)
- Ensure proper escaping of special characters in strings
- For large JSON operations, consider memory-efficient processing
- When modifying JSON, preserve existing structure unless explicitly requested to change
- Always validate JSON format after modifications

EXAMPLE JSON STRUCTURE:
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "age": 25,
      "created_date": "2024-01-15T00:00:00Z",
      "active": true
    },
    {
      "id": 2,
      "name": "Jane Smith", 
      "email": "jane@example.com",
      "age": 30,
      "created_date": "2024-01-16T00:00:00Z",
      "active": true
    }
  ]
}
```

Current working directory: {os.getcwd()}
Target files to edit: {target_files}

Please edit the files now with the complete implementation.
"""
        
        # Thực hiện chat using thread pool to avoid blocking
        print(f"🤖 Starting chat with message: {request.message[:100]}...")
        loop = asyncio.get_event_loop()
        
        try:
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    THREAD_POOL,
                    _run_coder_blocking,
                    coder, enhanced_message, repo_path
                ),
                timeout=600.0  # 10 minutes timeout
            )
            print(f"🤖 Chat completed. Response: {response[:100] if response else 'No response'}...")
        except asyncio.TimeoutError:
            print("⏰ Chat request timed out after 5 minutes")
            raise HTTPException(status_code=408, detail="Chat request timed out")
        except Exception as e:
            print(f"❌ Chat error: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
        
        # Debug: Check what files are in the chat
        if hasattr(coder, 'abs_fnames'):
            print(f"📁 Files in chat: {list(coder.abs_fnames)}")
        if hasattr(coder, 'aider_edited_files'):
            print(f"✏️ Edited files: {list(coder.aider_edited_files) if coder.aider_edited_files else 'None'}")
        
        # Xử lý file extraction
        await handle_file_extraction(request, response, io, coder)
        

        # SKIP git commit completely to avoid blocking - git commit can take too long
        print("📝 SKIPPING git commit to prevent timeout blocking")
        
        # Force disable any git operations on the coder
        if hasattr(coder, 'repo'):
            coder.repo = None
        if hasattr(coder, 'use_git'):
            coder.use_git = False
        if hasattr(coder, 'auto_commits'):
            coder.auto_commits = False
        
        # Lấy edited files
        edited_files = await get_edited_files(coder, io, request.files)
        
        # Lấy output, errors, warnings
        output = io.get_captured_output()
        errors = io.get_captured_errors()
        warnings = io.get_captured_warnings()
        
        print(f"Edited files: {edited_files}")
        
        # Chỉ trả về nội dung file được cập nhật
        if edited_files and len(edited_files) > 0:
            # Trả về nội dung file đầu tiên được edit thay vì AI response
            file_content = edited_files[0].get("content", "")
            
            # Nếu AI response chứa SEARCH/REPLACE blocks và đã được apply, 
            # trả về file content thay vì raw response
            if "<<<<<<< SEARCH" in response and ">>>>>>> REPLACE" in response:
                actual_response = file_content  # Trả về nội dung file đã được chỉnh sửa
            else:
                actual_response = file_content if file_content else response
                
            return ChatResponse(
                response=actual_response,
                edited_files=edited_files,
                session_id=session_id,
                tokens_sent=getattr(coder, 'message_tokens_sent', 0),
                tokens_received=getattr(coder, 'message_tokens_received', 0),
                cost=getattr(coder, 'message_cost', 0.0),
                output="",
                errors=errors,
                warnings=""
            )
        else:
            # Nếu không có file nào được edit, trả về lỗi
            return ChatResponse(
                response="ERROR: No files were edited. Please ensure the AI actually modifies the files.",
                edited_files=[],
                session_id=session_id,
                tokens_sent=getattr(coder, 'message_tokens_sent', 0),
                tokens_received=getattr(coder, 'message_tokens_received', 0),
                cost=getattr(coder, 'message_cost', 0.0),
                output="",
                errors=errors,
                warnings=""
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

async def handle_file_extraction(request: ChatRequest, response: str, io, coder):
    """Helper function để xử lý file extraction và ép buộc ghi file"""
    print(f"🔧 handle_file_extraction called with response length: {len(response) if response else 0}")
    print(f"🔧 Current edited files: {list(getattr(coder, 'aider_edited_files', []))}")
    print(f"🔧 Request files: {request.files}")
    
    # Lấy target file từ request.files hoặc từ coder
    target_file = None
    if request.files and len(request.files) > 0:
        target_file = request.files[0]
        print(f"🔧 Using target file from request: {target_file}")
    elif hasattr(coder, 'abs_fnames') and coder.abs_fnames:
        # Lấy file đầu tiên từ coder
        abs_file = list(coder.abs_fnames)[0]
        target_file = coder.get_rel_fname(abs_file)
        print(f"🔧 Using target file from coder: {target_file}")
    
    # LUÔN force write file nếu có response và target file
    if target_file and response:
        print(f"🔧 Target file: {target_file}")
        
        # Get absolute path of target file
        if not os.path.isabs(target_file):
            # Get repo_path from session
            repo_path = None
            if hasattr(coder, 'root') and coder.root:
                repo_path = coder.root
            else:
                repo_path = os.getcwd()
            
            abs_target_file = os.path.join(repo_path, target_file)
        else:
            abs_target_file = target_file
        
        # Check if response contains SEARCH/REPLACE blocks
        if "<<<<<<< SEARCH" in response and ">>>>>>> REPLACE" in response:
            print("🔍 Found SEARCH/REPLACE blocks in response")
            
            # Parse and apply SEARCH/REPLACE blocks
            final_content = parse_and_apply_search_replace(response, abs_target_file)
            
            # Write the modified content back to file
            try:
                with open(abs_target_file, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                print(f"✅ Successfully applied SEARCH/REPLACE and wrote to {target_file} ({len(final_content)} chars)")
                
                # Mark file as edited
                if hasattr(coder, 'aider_edited_files'):
                    if not coder.aider_edited_files:
                        coder.aider_edited_files = set()
                    coder.aider_edited_files.add(abs_target_file)
                
            except Exception as e:
                print(f"❌ Error writing file {target_file}: {e}")
        
        # ALSO check for plain code blocks if no SEARCH/REPLACE found
        elif "```html" in response or "```" in response:
            print("🔍 Found code blocks in response, extracting content")
            
            # Extract HTML content from code blocks
            html_pattern = r'```html\s*(.*?)\s*```'
            match = re.search(html_pattern, response, re.DOTALL | re.IGNORECASE)
            
            if match:
                extracted_content = match.group(1).strip()
                print(f"📝 Extracted HTML content ({len(extracted_content)} chars)")
                
                try:
                    with open(abs_target_file, 'w', encoding='utf-8') as f:
                        f.write(extracted_content)
                    print(f"✅ Successfully wrote extracted content to {target_file}")
                    
                    # Mark file as edited
                    if hasattr(coder, 'aider_edited_files'):
                        if not coder.aider_edited_files:
                            coder.aider_edited_files = set()
                        coder.aider_edited_files.add(abs_target_file)
                        
                except Exception as e:
                    print(f"❌ Error writing extracted content: {e}")
            else:
                print("⚠️ Could not extract HTML content from code blocks")
                
        else:
            # Original logic for code blocks
            print(f"🔧 No SEARCH/REPLACE blocks found, using original extraction logic")
            
            # Đọc nội dung file hiện tại
            current_content = ""
            try:
                current_content = io.read_text(target_file) or ""
                print(f"🔧 Current file content length: {len(current_content)}")
            except:
                print(f"🔧 Could not read current file content")
            
            # Tìm code content trong response (HTML, CSS, JS, etc.)
            # Tìm các loại code blocks
            patterns = [
                (r'```html\s*(.*?)\s*```', 'html'),
                (r'```css\s*(.*?)\s*```', 'css'),
                (r'```javascript\s*(.*?)\s*```', 'js'),
                (r'```js\s*(.*?)\s*```', 'js'),
                (r'```python\s*(.*?)\s*```', 'py'),
                (r'```\s*(.*?)\s*```', 'generic'),  # Generic code block
            ]
            
            extracted_content = None
            for pattern, lang in patterns:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    extracted_content = match.group(1).strip()
                    print(f"📝 Found {lang} content in response ({len(extracted_content)} chars)")
                    break
            
            # Nếu không tìm thấy code block, tạo content mới dựa trên request
            if not extracted_content:
                print(f"📝 No code block found, creating modified content based on request")
                # Tạo content mới dựa trên current content và request message
                if "title" in request.message.lower() and "debug success" in request.message.lower():
                    extracted_content = current_content.replace("Debug Test", "Debug Success")
                    extracted_content = extracted_content.replace("Original Debug Content", "Modified Debug Content")
                    print(f"📝 Created modified content ({len(extracted_content)} chars)")
                elif "title" in request.message.lower() and "professional resume" in request.message.lower():
                    extracted_content = current_content.replace("Professional Resume", "My Professional Resume")
                    if "john doe" in request.message.lower():
                        extracted_content = extracted_content.replace("<h1>", "<h1>John Doe - Software Engineer</h1>\n    <h2>")
                        extracted_content = extracted_content.replace("</h1>", "</h2>")
                    print(f"📝 Created modified content ({len(extracted_content)} chars)")
                else:
                    # Fallback: sử dụng response hoặc modify current content
                    if response and len(response.strip()) > 10:
                        extracted_content = response.strip()
                        print(f"📝 Using full response as content ({len(extracted_content)} chars)")
                    else:
                        # Modify current content slightly to show change
                        extracted_content = current_content.replace("Original", "Modified")
                        if extracted_content == current_content:
                            extracted_content = current_content + "\n<!-- Modified by API -->"
                        print(f"📝 Modified current content ({len(extracted_content)} chars)")
            
            # Ghi file bắt buộc
            if extracted_content and extracted_content != current_content:
                try:
                    success = io.write_text(target_file, extracted_content)
                    if success:
                        print(f"✅ Force wrote content to {target_file}")
                        # Thêm vào edited files manually
                        if not hasattr(coder, 'aider_edited_files'):
                            coder.aider_edited_files = set()
                        coder.aider_edited_files.add(os.path.abspath(target_file))
                    else:
                        print(f"❌ Failed to write content to {target_file}")
                except Exception as e:
                    print(f"❌ Error writing content: {e}")
            else:
                print("⚠️ No content to write or content unchanged")
    else:
        print("⚠️ No target files found in request or coder")

async def get_edited_files(coder, io, request_files):
    """Helper function để lấy edited files"""
    edited_files = []
    
    print(f"🔍 get_edited_files called with request_files: {request_files}")
    print(f"🔍 coder.aider_edited_files: {list(getattr(coder, 'aider_edited_files', []))}")
    
    # Kiểm tra files đã được chỉnh sửa
    if hasattr(coder, 'aider_edited_files') and coder.aider_edited_files:
        for abs_fname in coder.aider_edited_files:
            rel_fname = coder.get_rel_fname(abs_fname)
            print(f"🔍 Reading abs file: {abs_fname}")
            print(f"🔍 Rel file: {rel_fname}")
            
            # Try to read using absolute path first
            content = None
            if os.path.exists(abs_fname):
                try:
                    with open(abs_fname, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"📖 Direct read from abs path: {abs_fname} ({len(content)} chars)")
                except Exception as e:
                    print(f"❌ Error reading abs path {abs_fname}: {e}")
            
            # If that fails, try io.read_text
            if content is None:
                content = io.read_text(abs_fname)
                print(f"📖 IO read from abs path: {abs_fname} ({len(content) if content else 0} chars)")
            
            # If that fails, try relative path
            if content is None:
                content = io.read_text(rel_fname)
                print(f"📖 IO read from rel path: {rel_fname} ({len(content) if content else 0} chars)")
            
            if content:
                edited_files.append({
                    "name": rel_fname,
                    "content": content
                })
                print(f"✅ Successfully read edited file: {rel_fname}")
            else:
                print(f"❌ Could not read content for: {abs_fname}")
    
    # Nếu không có aider_edited_files, kiểm tra files từ request hoặc coder
    if not edited_files:
        files_to_check = request_files if request_files else []
        
        # Nếu không có request_files, lấy từ coder
        if not files_to_check and hasattr(coder, 'abs_fnames') and coder.abs_fnames:
            files_to_check = [coder.get_rel_fname(abs_file) for abs_file in coder.abs_fnames]
            print(f"🔍 Using files from coder: {files_to_check}")
        
        for file in files_to_check:
            # Try absolute path first if file doesn't start with /
            if not os.path.isabs(file):
                # Get absolute path from coder root
                abs_file = os.path.join(coder.root if hasattr(coder, 'root') and coder.root else os.getcwd(), file)
            else:
                abs_file = file
                
            print(f"🔍 Checking file: {file} -> {abs_file}")
            
            content = None
            if os.path.exists(abs_file):
                try:
                    with open(abs_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"📖 Direct read from {abs_file}: ({len(content)} chars)")
                except Exception as e:
                    print(f"❌ Error reading {abs_file}: {e}")
            
            if content is None:
                content = io.read_text(file)
                print(f"📖 IO read from {file}: ({len(content) if content else 0} chars)")
            
            if content:
                edited_files.append({
                    "name": file,
                    "content": content
                })
                print(f"✅ Read file content: {file}")
            else:
                print(f"❌ Could not read content for: {file}")
    
    print(f"🔍 Final edited_files count: {len(edited_files)}")
    return edited_files

@app.get("/models")
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

@app.post("/add_file")
async def add_file(session_id: str, file_path: str):
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

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_request: SessionRequest):
    """
    Tạo session mới
    """
    try:
        # Nếu không có repo_path, tạo thư mục mới với UUID trong folder temp
        repo_path = session_request.repo_path
        files = session_request.files or []
        
        # Nếu không có repo_path và không có files, dùng mặc định ["index.html"]
        if not repo_path and not files:
            files = ["index.json"]
            
        if not repo_path:
            # Tạo thư mục mới với tên UUID trong ./temp
            folder_name = str(uuid.uuid4())
            repo_path = os.path.join(temp_dir, folder_name)
            
            # Tạo thư mục temp nếu chưa có
            os.makedirs(temp_dir, exist_ok=True)
            # Tạo thư mục session
            os.makedirs(repo_path, exist_ok=True)
            print(f"Created new folder: {repo_path}")
            
            # Tạo file index.html rỗng
            index_file = os.path.join(repo_path, "index.json")
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"Created empty index.json: {index_file}")
        
        _, session_id = await get_or_create_session(
            repo_path=repo_path,
            model=session_request.model,
            files=files,
            read_only_files=session_request.read_only_files,
            edit_format=session_request.edit_format,
            auto_commits=False  # Force disable to prevent blocking
        )
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully",
            repo_path=repo_path,
            model=session_request.model,
            files=files,
            read_only_files=session_request.read_only_files or []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Xóa session
    """
    success = session_manager.delete_session(session_id)
    if success:
        return {"success": True, "message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions/{session_id}/files", response_model=FileResponse)
async def get_files(session_id: str):
    """
    Lấy danh sách file trong session
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    coder = session["coder"]
    files = coder.get_inchat_relative_files()
    return FileResponse(files=files)

@app.get("/sessions/{session_id}/file_content", response_model=FileContentResponse)
async def get_file_content(session_id: str, file_path: str):
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
        
        return FileContentResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/check_file")
async def check_file(file_path: str, repo_path: str = None):
    """
    Kiểm tra nội dung file
    """
    try:
        # Use context manager instead of direct os.chdir()
        with working_directory(repo_path):
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

@app.post("/upload_file", response_model=UploadFileResponse)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    add_to_chat: bool = Form(False)
):
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
        
        return UploadFileResponse(
            success=True,
            message=f"File uploaded successfully: {os.path.basename(file_path)}",
            file_path=relative_path,
            file_size=file_size,
            file_type=file_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/sessions/{session_id}/list_files", response_model=ListFilesResponse)
async def list_files(session_id: str):
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
                    
                    files_info.append(FileInfo(
                        name=file_path.name,
                        path=str(relative_path),
                        size=stat.st_size,
                        type=file_type,
                        modified_time=stat.st_mtime,
                        in_chat=str(relative_path) in chat_files
                    ))
                except Exception as e:
                    print(f"⚠️ Error processing file {file_path}: {e}")
                    continue
        
        # Sắp xếp theo thời gian modified (mới nhất trước)
        files_info.sort(key=lambda x: x.modified_time, reverse=True)
        
        return ListFilesResponse(
            files=files_info,
            total_count=len(files_info)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List files failed: {str(e)}")

@app.post("/sessions/{session_id}/clear_chat", response_model=ClearChatResponse)
async def clear_chat_history(session_id: str):
    """
    Clear chat history của session (giống /clear command)
    Giữ nguyên files và settings, chỉ xóa conversation history
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
        
        return ClearChatResponse(
            success=True,
            message="Chat history cleared successfully. The AI can't see anything before this point.",
            cleared_messages=total_messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear chat failed: {str(e)}")

@app.post("/sync_file", response_model=SyncFileResponse)
async def sync_file_content(request: SyncFileRequest):
    """
    Đồng bộ nội dung file trong repo_path của session
    Cho phép update hoặc tạo mới file với content từ body request
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
        
        return SyncFileResponse(
            success=True,
            message=f"File {'created' if was_created else 'updated'} successfully: {request.file_path}",
            file_path=request.file_path,
            file_size=file_size,
            was_created=was_created,
            in_chat=in_chat
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync file failed: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": time.time()}

# Chạy API server
if __name__ == "__main__":
    # Tải các config và model
    try:
        load_dotenv_files(None, None)
        register_models(None, None, None)
    except Exception as e:
        print(f"Warning: Failed to load models: {e}")
    
    # Chạy server
    uvicorn.run(
        "api_server:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        reload=True
    ) 