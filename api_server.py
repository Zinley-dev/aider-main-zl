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

class FileResponse(BaseModel):
    files: List[str]

class FileContentResponse(BaseModel):
    content: str

# Hàm tiện ích để tạo và lấy session Aider
def get_or_create_session(session_id: str = None, repo_path: str = None):
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            return session, session_id
    
    # Tạo session mới
    try:
        # Tạo IO instance không tương tác
        io = ApiInputOutput()
        
        # Tạo model
        main_model = Model(settings.DEFAULT_MODEL)
        
        # Tạo coder instance
        coder = Coder.create(
            main_model=main_model,
            io=io,
            auto_commits=True,
            use_git=(repo_path is not None),
            fnames=[],
            repo=None  # Sẽ được thiết lập sau nếu cần
        )
        
        # Tạo session
        new_session_id = session_manager.create_session(coder, io)
        session = session_manager.get_session(new_session_id)
        
        return session, new_session_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

# Định nghĩa các endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Gửi tin nhắn tới Aider và nhận phản hồi
    """
    try:
        session, session_id = get_or_create_session(request.session_id, request.repo_path)
        coder = session["coder"]
        io = session["io"]
        
        # Clear buffers trước khi xử lý
        io.clear_buffers()
        
        # Thêm các file vào chat
        if request.files:
            for file in request.files:
                if os.path.exists(file):
                    coder.add_rel_fname(file)
        
        # Thêm các file chỉ đọc
        if request.read_only_files:
            for file in request.read_only_files:
                if os.path.exists(file):
                    abs_path = os.path.abspath(file)
                    coder.abs_read_only_fnames.add(abs_path)
        
        # Cấu hình model nếu khác model mặc định
        if request.model and request.model != coder.main_model.name:
            coder.main_model = Model(request.model)
        
        # Cấu hình edit format
        if request.edit_format and request.edit_format != "auto":
            coder = Coder.create(
                main_model=coder.main_model,
                edit_format=request.edit_format,
                from_coder=coder
            )
            session["coder"] = coder
        
        # Thực hiện chat
        response = coder.run(with_message=request.message, preproc=True)
        
        # Lấy thông tin về file đã sửa
        edited_files = []
        if hasattr(coder, 'aider_edited_files') and coder.aider_edited_files:
            for fname in coder.aider_edited_files:
                rel_fname = coder.get_rel_fname(fname)
                content = io.read_text(fname)
                if content:
                    edited_files.append({
                        "name": rel_fname,
                        "content": content
                    })
        
        # Lấy output, errors, warnings
        output = io.get_captured_output()
        errors = io.get_captured_errors()
        warnings = io.get_captured_warnings()
        
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
async def create_session(repo_path: Optional[str] = None):
    """
    Tạo session mới
    """
    try:
        _, session_id = get_or_create_session(repo_path=repo_path)
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully"
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