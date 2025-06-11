from fastapi import FastAPI, Depends, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
import time
import uuid
import json
import threading

from aider.coders import Coder
from aider.io import InputOutput
from aider import models
from aider.models import Model
from aider.main import register_models, load_dotenv_files
from api_io import ApiInputOutput
from session_manager import SessionManager
from config import settings

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

# Khởi tạo session manager
session_manager = SessionManager(timeout=settings.SESSION_TIMEOUT)

# Các model Pydantic để xác thực request và response
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = settings.DEFAULT_MODEL
    files: Optional[List[str]] = []
    read_only_files: Optional[List[str]] = []
    edit_format: Optional[str] = "auto"
    session_id: Optional[str] = None
    repo_path: Optional[str] = None

class SessionRequest(BaseModel):
    repo_path: Optional[str] = None
    model: Optional[str] = settings.DEFAULT_MODEL
    files: Optional[List[str]] = []
    read_only_files: Optional[List[str]] = []
    edit_format: Optional[str] = "auto"
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

# Hàm tiện ích để tạo và lấy session Aider
def get_or_create_session(session_id: str = None, repo_path: str = None, model: str = None, files: List[str] = None, read_only_files: List[str] = None, edit_format: str = "auto", auto_commits: bool = True):
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            return session, session_id
    
    # Tạo session mới
    try:
        # Lưu thư mục hiện tại
        original_cwd = os.getcwd()
        
        # Thiết lập working directory
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"Changed working directory to: {repo_path}")
        
        # Tạo IO instance không tương tác
        io = ApiInputOutput()
        
        # Tạo model
        model_name = model or settings.DEFAULT_MODEL
        main_model = Model(model_name)

        print(f"Model: {model_name}")
        
        # Tạo coder instance
        coder = Coder.create(
            main_model=main_model,
            io=io,
            auto_commits=auto_commits,
            use_git=True,  # Luôn enable git để track changes
            fnames=[],  # Sẽ thêm files sau
            edit_format=edit_format
        )
        
        # Thiết lập root path cho coder nếu có repo_path
        if repo_path:
            coder.root = repo_path
        
        # Thêm files vào coder nếu có
        if files:
            for file in files:
                # Sử dụng relative path từ repo_path
                if os.path.exists(file):
                    coder.add_rel_fname(file)
                    print(f"Added file to chat: {file}")
                else:
                    print(f"Warning: File {file} not found in {os.getcwd()}")
        
        # Thêm read-only files nếu có
        if read_only_files:
            for file in read_only_files:
                if os.path.exists(file):
                    abs_path = os.path.abspath(file)
                    coder.abs_read_only_fnames.add(abs_path)
                    print(f"Added read-only file: {file}")
                else:
                    print(f"Warning: Read-only file {file} not found")
        
        # Tạo session và lưu thông tin repo_path
        new_session_id = session_manager.create_session(coder, io)
        session = session_manager.get_session(new_session_id)
        
        # Lưu repo_path vào session để sử dụng sau
        session["repo_path"] = repo_path
        
        return session, new_session_id
        
    except Exception as e:
        # Trở về thư mục gốc nếu có lỗi
        os.chdir(original_cwd)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    finally:
        # Không trở về thư mục gốc ở đây vì coder cần working directory đúng
        pass

# Định nghĩa các endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Gửi tin nhắn tới Aider và nhận phản hồi
    """
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
        original_cwd = os.getcwd()
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"Chat: Working in directory: {repo_path}")
        
        # Clear buffers trước khi xử lý
        io.clear_buffers()
        
        # Chuẩn bị message với instruction rõ ràng
        enhanced_message = f"""
{request.message}

IMPORTANT: Please edit the file(s) directly. Do not just provide code examples. 
I need you to actually modify the file content and save the changes.
The files are: {', '.join(request.files) if request.files else 'the files in this chat'}
"""
        
        # Thực hiện chat
        print(f"🤖 Starting chat with message: {request.message[:100]}...")
        response = coder.run(with_message=enhanced_message, preproc=True)
        print(f"🤖 Chat completed. Response: {response[:100] if response else 'No response'}...")
        
        # Debug: Check what files are in the chat
        if hasattr(coder, 'abs_fnames'):
            print(f"📁 Files in chat: {list(coder.abs_fnames)}")
        if hasattr(coder, 'aider_edited_files'):
            print(f"✏️ Edited files: {list(coder.aider_edited_files) if coder.aider_edited_files else 'None'}")
        
        # Nếu response chứa HTML/code và không có edited files, thử extract và ghi file
        if response and not (hasattr(coder, 'aider_edited_files') and coder.aider_edited_files):
            print("🔧 No edited files detected, trying to extract content from response...")
            
            # Tìm HTML content trong response
            import re
            html_match = re.search(r'```html\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
            if html_match:
                html_content = html_match.group(1).strip()
                print(f"📝 Found HTML content in response ({len(html_content)} chars)")
                
                # Ghi vào file đầu tiên trong files list
                if request.files and len(request.files) > 0:
                    target_file = request.files[0]
                    try:
                        success = io.write_text(target_file, html_content)
                        if success:
                            print(f"✅ Successfully wrote extracted content to {target_file}")
                            # Thêm vào edited files manually
                            if not hasattr(coder, 'aider_edited_files'):
                                coder.aider_edited_files = set()
                            coder.aider_edited_files.add(os.path.abspath(target_file))
                        else:
                            print(f"❌ Failed to write extracted content to {target_file}")
                    except Exception as e:
                        print(f"❌ Error writing extracted content: {e}")
            else:
                print("⚠️ No HTML content found in response")
        
        # Force flush any pending file writes
        if hasattr(coder, 'repo') and coder.repo:
            try:
                coder.repo.commit_if_dirty("API chat changes")
                print("📝 Committed changes to git")
            except Exception as e:
                print(f"⚠️ Git commit failed: {e}")
        
        # Lấy thông tin về file đã sửa
        edited_files = []
        
        # Kiểm tra files đã được chỉnh sửa
        if hasattr(coder, 'aider_edited_files') and coder.aider_edited_files:
            for fname in coder.aider_edited_files:
                rel_fname = coder.get_rel_fname(fname)
                content = io.read_text(fname)
                if content:
                    edited_files.append({
                        "name": rel_fname,
                        "content": content
                    })
                    print(f"Successfully read edited file: {fname}")
        
        # Nếu không có aider_edited_files, kiểm tra tất cả files trong chat
        if not edited_files and request.files:
            for file in request.files:
                content = io.read_text(file)
                if content:
                    edited_files.append({
                        "name": file,
                        "content": content
                    })
                    print(f"Read file content: {file}")
        
        # Lấy output, errors, warnings
        output = io.get_captured_output()
        errors = io.get_captured_errors()
        warnings = io.get_captured_warnings()
        
        print(f"Edited files: {edited_files}")

        return ChatResponse(
            response=response or "",
            edited_files=edited_files,
            session_id=session_id,
            tokens_sent=getattr(coder, 'message_tokens_sent', 0),
            tokens_received=getattr(coder, 'message_tokens_received', 0),
            cost=getattr(coder, 'message_cost', 0.0),
            output=output,
            errors=errors,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
    finally:
        # Trở về thư mục gốc
        try:
            os.chdir(original_cwd)
        except:
            pass

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
        _, session_id = get_or_create_session(
            repo_path=session_request.repo_path,
            model=session_request.model,
            files=session_request.files,
            read_only_files=session_request.read_only_files,
            edit_format=session_request.edit_format,
            auto_commits=session_request.auto_commits
        )
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully",
            repo_path=session_request.repo_path,
            model=session_request.model,
            files=session_request.files or [],
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