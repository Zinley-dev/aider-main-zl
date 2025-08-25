from fastapi import FastAPI, Depends, HTTPException, Body, Request, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio
import functools
import os
import re
import json
from contextlib import contextmanager
import logging

from aider.main import register_models, load_dotenv_files
from config import settings
from firebase_util import get_firebase_util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase utility
firebase_util = get_firebase_util()

# Authentication and quota checking functions
class UserInfo(BaseModel):
    uid: str
    email: str
    name: Optional[str] = None
    quota_info: Dict[str, Any]

def extract_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Access token string
        
    Raises:
        HTTPException: If token is missing or invalid format
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must be in format: Bearer <token>"
        )
    
    token = authorization.replace("Bearer ", "", 1).strip()
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Access token is required"
        )
    
    return token

async def verify_user_and_quota(authorization: Optional[str] = Header(None)) -> UserInfo:
    """
    Verify user access token and check quota limits.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        UserInfo object with user data and quota info
        
    Raises:
        HTTPException: If token is invalid or quota exceeded
    """
    try:
        # Extract token from header
        access_token = extract_token_from_header(authorization)
        
        # Verify token with Firebase
        user_info = firebase_util.verify_access_token(access_token)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token"
            )
        
        # Get user quota information
        quota_info = firebase_util.get_user_quota(access_token)
        if not quota_info:
            raise HTTPException(
                status_code=500,
                detail="Unable to retrieve user quota information"
            )
        
        # Check if user has exceeded quota
        used = quota_info.get('used', 0)
        limit = quota_info.get('limit', 0)
        
        if used >= limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Quota exceeded",
                    "message": f"You have exceeded your usage limit ({used}/{limit})",
                    "quota_info": {
                        "used": used,
                        "limit": limit,
                        "plan": quota_info.get('plan', 'unknown'),
                        "usage_breakdown": quota_info.get('usage_breakdown', {})
                    }
                }
            )
        
        logger.info(f"User authenticated: {user_info['uid']} - Usage: {used}/{limit}")
        
        return UserInfo(
            uid=user_info['uid'],
            email=user_info['email'],
            name=user_info.get('name'),
            quota_info=quota_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user verification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )

async def increment_user_usage(user_uid: str, usage_type: str = "prompt") -> bool:
    """
    Increment user usage after successful API call.
    
    Args:
        user_uid: User ID
        usage_type: Type of usage to increment
        
    Returns:
        True if successful, False otherwise
    """
    try:
        return firebase_util.update_user_usage(user_uid, usage_type, 1)
    except Exception as e:
        logger.error(f"Error incrementing usage for user {user_uid}: {str(e)}")
        return False
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
async def chat(request: ChatRequest, user: UserInfo = Depends(verify_user_and_quota)):
    """
    Gửi tin nhắn tới Aider và nhận phản hồi
    Hỗ trợ cả streaming (SSE) và non-streaming
    Requires authentication via Authorization: Bearer <token> header
    """
    try:
        if request.stream:
            # For streaming, we need to increment usage before starting
            await increment_user_usage(user.uid, "prompt")
            
            # Trả về streaming response
            return StreamingResponse(
                chat_stream(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                    "X-User-ID": user.uid,
                    "X-Quota-Used": str(user.quota_info.get('used', 0)),
                    "X-Quota-Limit": str(user.quota_info.get('limit', 0)),
                }
            )
        else:
            # Trả về response thông thường
            result = await chat_non_stream(request)
            
            # Increment usage after successful chat
            await increment_user_usage(user.uid, "prompt")
            
            # Add user info to response
            response_data = ChatResponse(**result)
            
            return response_data
            
    except Exception as e:
        logger.error(f"Error in chat endpoint for user {user.uid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/quota")
async def get_user_quota(user: UserInfo = Depends(verify_user_and_quota)):
    """
    Get current user quota information
    """
    return {
        "user": {
            "uid": user.uid,
            "email": user.email,
            "name": user.name
        },
        "quota": user.quota_info
    }

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