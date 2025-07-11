from fastapi import FastAPI, Depends, HTTPException, Body, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

from aider.main import register_models, load_dotenv_files
from config import settings
from api_controller import (
    chat_stream,
    chat_non_stream,
    list_models,
    add_file_to_session,
    create_session_controller,
    delete_session_controller,
    get_session_files,
    get_file_content_controller,
    check_file_controller,
    upload_file_controller,
    list_files_controller,
    clear_chat_history_controller,
    sync_file_controller,
    health_check
)

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
        result = await chat_non_stream(request)
        return ChatResponse(**result)

@app.get("/models")
async def get_models():
    """
    Lấy danh sách model được hỗ trợ
    """
    return await list_models()

@app.post("/add_file")
async def add_file(session_id: str, file_path: str):
    """
    Thêm file vào session chat
    """
    return await add_file_to_session(session_id, file_path)

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_request: SessionRequest):
    """
    Tạo session mới
    """
    result = await create_session_controller(session_request)
    return SessionResponse(**result)

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Xóa session
    """
    return await delete_session_controller(session_id)

@app.get("/sessions/{session_id}/files", response_model=FileResponse)
async def get_files(session_id: str):
    """
    Lấy danh sách file trong session
    """
    result = await get_session_files(session_id)
    return FileResponse(**result)

@app.get("/sessions/{session_id}/file_content", response_model=FileContentResponse)
async def get_file_content(session_id: str, file_path: str):
    """
    Lấy nội dung file
    """
    result = await get_file_content_controller(session_id, file_path)
    return FileContentResponse(**result)

@app.get("/check_file")
async def check_file(file_path: str, repo_path: str = None):
    """
    Kiểm tra nội dung file
    """
    return await check_file_controller(file_path, repo_path)

@app.post("/upload_file", response_model=UploadFileResponse)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    add_to_chat: bool = Form(False)
):
    """
    Upload file vào repo_path của session
    """
    result = await upload_file_controller(session_id, file, add_to_chat)
    return UploadFileResponse(**result)

@app.get("/sessions/{session_id}/list_files", response_model=ListFilesResponse)
async def list_files(session_id: str):
    """
    Lấy danh sách tất cả file trong repo_path của session
    """
    result = await list_files_controller(session_id)
    return ListFilesResponse(**result)

@app.post("/sessions/{session_id}/clear_chat", response_model=ClearChatResponse)
async def clear_chat_history(session_id: str):
    """
    Clear chat history của session (giống /clear command)
    """
    result = await clear_chat_history_controller(session_id)
    return ClearChatResponse(**result)

@app.post("/sync_file", response_model=SyncFileResponse)
async def sync_file_content(request: SyncFileRequest):
    """
    Đồng bộ nội dung file trong repo_path của session
    """
    result = await sync_file_controller(request)
    return SyncFileResponse(**result)

@app.get("/health")
async def health_check_endpoint():
    """
    Health check endpoint
    """
    return await health_check()

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