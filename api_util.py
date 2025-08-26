import os
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator

from aider.coders import Coder
from aider.models import Model
from aider.repo import GitRepo
from aider.main import register_models, load_dotenv_files
from api_io import ApiInputOutput, StreamingApiInputOutput
from session_manager import SessionManager
from config import settings

# Khởi tạo session manager
session_manager = SessionManager(timeout=settings.SESSION_TIMEOUT)

def get_or_create_session(session_id: str = None, repo_path: str = None, model: str = None, files: List[str] = None, read_only_files: List[str] = None, edit_format: str = "diff", auto_commits: bool = True, use_streaming: bool = False):
    """
    Tạo hoặc lấy session Aider
    """
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            # Check if model has changed
            current_coder = session["coder"]
            current_model_name = current_coder.main_model.name if current_coder.main_model else None
            
            # For streaming requests, always create a new StreamingApiInputOutput instance
            if use_streaming:
                print(f"Creating new StreamingApiInputOutput for concurrent request on session {session_id}")
                new_io = StreamingApiInputOutput()
                
                # Check if model has changed for streaming requests
                current_model_name = current_coder.main_model.name if current_coder.main_model else None
                if current_model_name and model and current_model_name != model:
                    # Use the new model for streaming requests
                    print(f"Model changed from {current_model_name} to {model} for streaming request")
                    main_model = Model(model)
                else:
                    # Use existing model
                    main_model = current_coder.main_model
                
                # Create a new coder instance with the new IO but preserve state
                new_coder = Coder.create(
                    main_model=main_model,
                    io=new_io,
                    from_coder=current_coder,
                    edit_format=edit_format,
                    auto_commits=auto_commits,
                    stream=True,
                    cache_prompts=True,
                    use_git=True,
                    repo=current_coder.repo if hasattr(current_coder, 'repo') else None
                )
                
                # Return a modified session dict with the new IO
                # We don't update the actual session to avoid affecting other requests
                return {
                    "coder": new_coder,
                    "io": new_io,
                    "repo_path": session.get("repo_path")
                }, session_id
            
            if current_model_name and model and current_model_name != model:
                # Model has changed, create new coder with new model
                print(f"Model changed from {current_model_name} to {model}. Updating session...")
                
                # Create Model object for the new model
                new_model = Model(model)
                
                # Create new coder with new model, preserving chat history and files
                new_coder = Coder.create(
                    main_model=new_model,
                    io=session["io"],
                    from_coder=current_coder,
                    edit_format=edit_format,
                    auto_commits=auto_commits,
                    stream=True,
                    cache_prompts=True,
                    use_git=True,
                    repo=current_coder.repo if hasattr(current_coder, 'repo') else None
                )
                
                # Update session with new coder
                session["coder"] = new_coder
                session_manager.update_session_activity(session_id)
                
                print(f"Session updated with new model: {model}")
            
            return session, session_id
    
    # Tạo session mới
    try:
        # Lưu thư mục hiện tại
        original_cwd = os.getcwd()
        print(f"Original working directory: {original_cwd}")
        
        # Thiết lập working directory
        if repo_path and os.path.exists(repo_path):
            os.chdir(repo_path)
            print(f"Changed working directory to: {repo_path}")
        
        # Tạo IO instance không tương tác
        if use_streaming:
            io = StreamingApiInputOutput()
        else:
            io = ApiInputOutput()
        
        # Tạo model
        model_name = model or settings.DEFAULT_MODEL
        main_model = Model(model_name)

        print(f"Model: {model_name}")
        print(f"Edit format: {edit_format}")
        
        # Khởi tạo repository cho repo_path
        repo = None
        if repo_path:
            try:
                repo = GitRepo(
                    io=io,
                    fnames=[],
                    git_dname=repo_path,
                    attribute_author=False,
                    attribute_committer=False
                )
                print(f"Initialized GitRepo for path: {repo_path}")
            except Exception as e:
                print(f"Failed to initialize GitRepo: {e}")
                # Fallback: create a basic repo object
                repo = None
        
        coder = Coder.create(
            main_model=main_model,
            io=io,
            auto_commits=auto_commits,
            use_git=True,  # Luôn enable git để track changes
            fnames=[],  # Sẽ thêm files sau
            edit_format=edit_format,
            stream=True,
            cache_prompts=True,
            repo=repo  # Pass the correct repository
        )
        
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
        raise Exception(f"Failed to create session: {str(e)}")
    finally:
        # Không trở về thư mục gốc ở đây vì coder cần working directory đúng
        pass

async def create_sse_response(events: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """
    Tạo SSE response từ events
    """
    async for event in events:
        # Format SSE
        event_type = event.get("type", "message")
        data = json.dumps(event.get("data", {}))
        
        sse_data = f"event: {event_type}\n"
        sse_data += f"data: {data}\n\n"
        
        yield sse_data

def get_image_files_info(coder):
    """
    Lấy thông tin về các file ảnh trong session
    """
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
    
    return image_files_info

def create_enhanced_message(message: str, files: List[str], image_files_info: str) -> str:
    """
    Tạo enhanced message - now returns clean user message without embedded instructions
    """
    return f"{message}{image_files_info}"

def get_system_prompt(files: List[str]) -> str:
    """
    Tạo system prompt với critical instructions - Legacy function, use create_dynamic_system_reminder instead
    """
    return f"""You are a code editor that MUST follow these critical instructions:
1. You MUST edit the file(s) directly - do NOT just show code examples
2. You MUST save the actual changes to the files
3. Do NOT provide explanations or additional text in your response
4. ONLY return the updated file content, nothing else
5. The files to edit are: {', '.join(files) if files else 'the files in this chat'}
6. If there are images available in the session, use them as reference for building the game/application
7. Build upon the conversation history - you can see what was discussed before

Be direct and edit files immediately without explanations."""

def detect_request_type(message: str) -> str:
    """Detect the type of request from message content"""
    message_lower = message.lower()
    # Check for add_feature first since it's more specific
    if any(word in message_lower for word in ['add', 'insert', 'include']) and 'feature' in message_lower:
        return 'add_feature'
    elif any(word in message_lower for word in ['create', 'new', 'build', 'make', 'generate']):
        return 'create_new'
    elif any(word in message_lower for word in ['fix', 'debug', 'error', 'bug', 'issue']):
        return 'debug'
    elif any(word in message_lower for word in ['refactor', 'improve', 'optimize', 'clean']):
        return 'refactor'
    elif any(word in message_lower for word in ['update', 'modify', 'change', 'edit']):
        return 'update'
    elif any(word in message_lower for word in ['add', 'insert', 'include']):
        return 'add_feature'
    return 'general'

def detect_urgency(message: str) -> str:
    """Detect urgency level from message"""
    urgent_words = ['urgent', 'asap', 'quickly', 'fast', 'immediately', 'now', 'critical']
    return 'high' if any(word in message.lower() for word in urgent_words) else 'normal'

def estimate_complexity(message: str, files: List[str]) -> str:
    """Estimate complexity of the request"""
    file_count = len(files) if files else 0
    message_length = len(message)
    
    # Check for complex keywords
    complex_keywords = ['algorithm', 'database', 'api', 'framework', 'architecture', 'system', 'integration']
    has_complex_keywords = any(keyword in message.lower() for keyword in complex_keywords)
    
    if file_count > 3 or message_length > 500 or has_complex_keywords:
        return 'high'
    elif file_count > 1 or message_length > 200:
        return 'medium'
    return 'low'

def create_dynamic_system_reminder(
    files: List[str], 
    request_context: dict,
    image_files: List[str] = None,
    conversation_history: List[dict] = None
) -> str:
    """
    Create contextual system reminder based on request context using custom prompt system
    """
    from custom_prompt import create_custom_dynamic_system_reminder
    
    return create_custom_dynamic_system_reminder(
        files=files,
        request_context=request_context,
        image_files=image_files,
        conversation_history=conversation_history
    )

def create_optimized_system_reminder(
    files: List[str], 
    request_context: dict,
    image_files: List[str] = None,
    conversation_history: List[dict] = None
) -> str:
    """
    Create optimized system reminder using specialized templates based on file types and request context
    """
    from custom_prompt import (
        create_web_prompt, 
        create_python_prompt, 
        create_debug_prompt, 
        create_refactor_prompt,
        create_custom_dynamic_system_reminder
    )
    
    # Determine the best template based on context
    request_type = request_context.get('type', 'general')
    
    # Check for specific request types first
    if request_type == 'debug':
        return create_debug_prompt(files, request_context)
    elif request_type == 'refactor':
        return create_refactor_prompt(files, request_context)
    
    # Check for file type patterns
    if files:
        file_extensions = {os.path.splitext(f)[1].lower() for f in files}
        
        # Web development files
        web_extensions = {'.html', '.css', '.js', '.ts', '.jsx', '.tsx'}
        if web_extensions.intersection(file_extensions):
            return create_web_prompt(files, request_context, image_files)
        
        # Python files
        if '.py' in file_extensions:
            return create_python_prompt(files, request_context)
    
    # Default to general template
    return create_custom_dynamic_system_reminder(
        files=files,
        request_context=request_context,
        image_files=image_files,
        conversation_history=conversation_history
    )

async def handle_file_extraction(request, response: str, io, coder):
    """
    Helper function để xử lý file extraction và ép buộc ghi file
    """
    print(f"🔧 handle_file_extraction called with response length: {len(response) if response else 0}")
    print(f"🔧 Current edited files: {list(getattr(coder, 'aider_edited_files', []))}")
    print(f"🔧 Request files: {request.files}")
    
    if not response:
        print("⚠️ No response to process")
        return
    
    # Check if response contains SEARCH/REPLACE blocks
    if "<<<<<<< SEARCH" in response and ">>>>>>> REPLACE" in response:
        print("🔍 Found SEARCH/REPLACE blocks in response, processing with Aider's editblock logic")
        
        # Import the necessary functions from editblock_coder
        from aider.coders.editblock_coder import find_original_update_blocks, do_replace, DEFAULT_FENCE
        
        try:
            # Get all files in the chat for processing
            valid_fnames = None
            if hasattr(coder, 'abs_fnames') and coder.abs_fnames:
                valid_fnames = [coder.get_rel_fname(abs_file) for abs_file in coder.abs_fnames]
            
            # Find and process all SEARCH/REPLACE blocks
            edits = list(find_original_update_blocks(response, valid_fnames=valid_fnames))
            print(f"🔍 Found {len(edits)} SEARCH/REPLACE blocks to process")
            
            if edits:
                # Process each edit
                for edit in edits:
                    path, original, updated = edit
                    print(f"🔧 Processing edit for file: {path}")
                    
                    # Get the full path
                    full_path = coder.abs_root_path(path) if hasattr(coder, 'abs_root_path') else os.path.abspath(path)
                    
                    # Read current content
                    current_content = ""
                    if os.path.exists(full_path):
                        current_content = io.read_text(full_path) or ""
                    
                    # Apply the search/replace
                    new_content = do_replace(full_path, current_content, original, updated, fence=DEFAULT_FENCE)
                    
                    if new_content is not None:
                        # Write the updated content
                        success = io.write_text(full_path, new_content)
                        if success:
                            print(f"✅ Successfully applied SEARCH/REPLACE to {path}")
                            # Add to edited files
                            if not hasattr(coder, 'aider_edited_files'):
                                coder.aider_edited_files = set()
                            coder.aider_edited_files.add(os.path.abspath(full_path))
                        else:
                            print(f"❌ Failed to write updated content to {path}")
                    else:
                        print(f"❌ SEARCH/REPLACE failed for {path} - no match found")
                        
                return  # Successfully processed SEARCH/REPLACE blocks
                
        except Exception as e:
            print(f"❌ Error processing SEARCH/REPLACE blocks: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to original logic if SEARCH/REPLACE processing fails
    
    # No SEARCH/REPLACE blocks found - return original content without modifications
    print("🔍 No SEARCH/REPLACE blocks found, keeping original file content unchanged")

async def get_edited_files(coder, io, request_files):
    """
    Helper function để lấy edited files
    """
    edited_files = []
    
    print(f"🔍 get_edited_files called with request_files: {request_files}")
    print(f"🔍 coder.aider_edited_files: {list(getattr(coder, 'aider_edited_files', []))}")
    
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
    
    # Nếu không có aider_edited_files, kiểm tra files từ request hoặc coder
    if not edited_files:
        files_to_check = request_files if request_files else []
        
        # Nếu không có request_files, lấy từ coder
        if not files_to_check and hasattr(coder, 'abs_fnames') and coder.abs_fnames:
            files_to_check = [coder.get_rel_fname(abs_file) for abs_file in coder.abs_fnames]
            print(f"🔍 Using files from coder: {files_to_check}")
        
        for file in files_to_check:
            content = io.read_text(file)
            if content:
                edited_files.append({
                    "name": file,
                    "content": content
                })
                print(f"Read file content: {file}")
    
    print(f"🔍 Final edited_files count: {len(edited_files)}")
    return edited_files

def create_temp_repo(files: List[str] = None) -> str:
    """
    Tạo temporary repo directory
    """
    # temp_dir = os.path.join("/Users/hoangnm/Desktop/test", "temp")
    temp_dir = os.path.join("/app", "temp")
    
    # Nếu không có files, dùng mặc định ["index.html"]
    if not files:
        files = ["index.html"]
    
    # Tạo thư mục mới với tên UUID trong ./temp
    folder_name = str(uuid.uuid4())
    repo_path = os.path.join(temp_dir, folder_name)
    
    # Tạo thư mục temp nếu chưa có
    os.makedirs(temp_dir, exist_ok=True)
    # Tạo thư mục session
    os.makedirs(repo_path, exist_ok=True)
    print(f"Created new folder: {repo_path}")
    
    # Tạo file index.html rỗng
    index_file = os.path.join(repo_path, "index.html")
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("")
    print(f"Created empty index.html: {index_file}")
    
    return repo_path

def apply_dynamic_system_reminder(coder, files: List[str], request_context: dict, image_files: List[str] = None):
    """
    Apply dynamic system reminder to an existing coder instance
    """
    # Get image files from coder if not provided
    if image_files is None:
        image_files = []
        if hasattr(coder, 'abs_read_only_fnames') and coder.abs_read_only_fnames:
            for abs_path in coder.abs_read_only_fnames:
                rel_path = coder.get_rel_fname(abs_path)
                file_ext = os.path.splitext(rel_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
                    image_files.append(rel_path)
    
    # Create dynamic reminder
    dynamic_reminder = create_dynamic_system_reminder(
        files=files,
        request_context=request_context,
        image_files=image_files,
        conversation_history=getattr(coder, 'cur_messages', [])
    )
    
    # Apply to coder
    coder.gpt_prompts.system_reminder = dynamic_reminder
    
    # Log the dynamic reminder for debugging
    print(f"🔧 Applied dynamic system reminder: {len(dynamic_reminder)} chars")
    print(f"🔧 Request context: {request_context}")
    print(f"🔧 Image files: {image_files}")
    
    return coder

def create_enhanced_coder_with_dynamic_reminder(
    session_id: str = None,
    repo_path: str = None,
    model: str = None,
    files: List[str] = None,
    read_only_files: List[str] = None,
    edit_format: str = "diff",
    auto_commits: bool = True,
    use_streaming: bool = False,
    request_message: str = "",
    session_context: dict = None
) -> tuple:
    """
    Create or get coder with dynamically generated system reminder
    """
    # Get or create base session
    session, session_id = get_or_create_session(
        session_id=session_id,
        repo_path=repo_path,
        model=model,
        files=files,
        read_only_files=read_only_files,
        edit_format=edit_format,
        auto_commits=auto_commits,
        use_streaming=use_streaming
    )
    
    coder = session["coder"]
    
    # Analyze request context
    request_context = {
        'type': detect_request_type(request_message),
        'urgency': detect_urgency(request_message),
        'complexity': estimate_complexity(request_message, files or []),
        'user_preferences': (session_context or {}).get('user_preferences', {})
    }
    
    # Apply dynamic system reminder
    apply_dynamic_system_reminder(coder, files or [], request_context)
    
    return session, session_id

def get_session_context(session_id: str) -> dict:
    """
    Get session context for enhanced coder creation
    """
    session = session_manager.get_session(session_id)
    if not session:
        return {}
    
    # Extract context from session
    context = {
        'repo_path': session.get('repo_path'),
        'user_preferences': session.get('user_preferences', {}),
        'session_history': session.get('session_history', []),
        'last_activity': session.get('last_activity')
    }
    
    return context

def update_session_context(session_id: str, context_updates: dict):
    """
    Update session context with new information
    """
    session = session_manager.get_session(session_id)
    if session:
        for key, value in context_updates.items():
            session[key] = value
        print(f"🔧 Updated session context: {context_updates}")

def get_session_manager():
    """
    Trả về session manager instance
    """
    return session_manager 