# Aider REST API

REST API cho Aider AI coding assistant, cho phép tích hợp Aider vào các ứng dụng khác.

## Cài đặt và Chạy

### 1. Cài đặt dependencies

```bash
# Cài đặt FastAPI và các dependencies
pip install -r requirements_api.txt

# Đảm bảo Aider đã được cài đặt
pip install -e .
```

### 2. Cấu hình API Keys

Tạo file `.env` trong thư mục gốc:

```bash
# OpenAI API Key (cho GPT models)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (cho Claude models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# DeepSeek API Key (cho DeepSeek models)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 3. Chạy API Server

```bash
python api_server.py
```

API sẽ chạy tại `http://localhost:8000`

## API Documentation

### Swagger UI
Truy cập `http://localhost:8000/docs` để xem tài liệu API tương tác.

### ReDoc
Truy cập `http://localhost:8000/redoc` để xem tài liệu API dạng ReDoc.

## Endpoints Chính

### 1. Health Check
```http
GET /health
```
Kiểm tra trạng thái API.

### 2. Tạo Session
```http
POST /sessions
```
Tạo session mới để chat với Aider.

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "Session created successfully"
}
```

### 3. Chat với Aider (Hỗ trợ Streaming)
```http
POST /chat
```

**Request Body:**
```json
{
  "message": "Your message to Aider",
  "session_id": "optional-session-id",
  "model": "gpt-4o",
  "files": ["file1.py", "file2.js"],
  "read_only_files": ["readme.md"],
  "edit_format": "whole",
  "stream": false
}
```

**Parameters:**
- `stream`: `true` để enable Server-Sent Events (SSE) streaming, `false` cho response thông thường

**Response (Non-streaming):**
```json
{
  "response": "Aider's response",
  "edited_files": [
    {
      "name": "file1.py",
      "content": "updated file content"
    }
  ],
  "session_id": "session-uuid",
  "tokens_sent": 150,
  "tokens_received": 200,
  "cost": 0.0045,
  "output": "Tool output messages",
  "errors": "Error messages if any",
  "warnings": "Warning messages if any"
}
```

**Response (Streaming - SSE Format):**
```
event: start
data: {"message": "Starting chat...", "timestamp": "2024-01-15T10:30:00Z"}

event: processing
data: {"message": "Processing request...", "session_id": "uuid-string"}

event: tool_output
data: {"message": "Reading file: example.py", "tool": "read_file", "status": "success"}

event: ai_output
data: {"message": "I'll help you add error handling to your function...", "chunk_id": 1}

event: file_write
data: {"filename": "example.py", "content_length": 1234, "success": true, "operation": "update"}

event: tool_error
data: {"message": "File not found: nonexistent.py", "error_code": "FILE_NOT_FOUND", "severity": "error"}

event: tool_warning
data: {"message": "Large file detected, this may take longer", "warning_code": "LARGE_FILE", "severity": "warning"}

event: heartbeat
data: {"timestamp": "2024-01-15T10:30:30Z", "connection_id": "conn-123"}

event: complete
data: {
  "response": "Successfully added error handling to your function. The code now includes try-catch blocks and proper exception handling.",
  "edited_files": [
    {
      "name": "example.py",
      "content": "def example_function():\n    try:\n        # Your code here\n        pass\n    except Exception as e:\n        print(f'Error: {e}')"
    }
  ],
  "session_id": "uuid-string",
  "tokens_sent": 150,
  "tokens_received": 200,
  "cost": 0.0045,
  "duration_ms": 2350,
  "timestamp": "2024-01-15T10:30:45Z"
}

event: error
data: {"message": "API rate limit exceeded", "error_code": "RATE_LIMIT", "retry_after": 60}
```

**SSE Event Types:**
- `start`: Bắt đầu xử lý request
  - `message`: Thông báo bắt đầu
  - `timestamp`: Thời gian bắt đầu
- `info`: Thông tin chung trong quá trình xử lý
  - `message`: Nội dung thông tin
- `processing`: Đang xử lý request
  - `message`: Mô tả bước đang xử lý
  - `session_id`: ID của session
- `tool_output`: Output thành công từ tools
  - `message`: Nội dung output
  - `tool`: Tên tool được sử dụng
  - `status`: Trạng thái (success/info)
- `tool_error`: Lỗi từ tools
  - `message`: Thông báo lỗi
  - `error_code`: Mã lỗi
  - `severity`: Mức độ (error)
- `tool_warning`: Cảnh báo từ tools
  - `message`: Thông báo cảnh báo
  - `warning_code`: Mã cảnh báo
  - `severity`: Mức độ (warning)
- `ai_output`: Output từ AI model (streaming chunks)
  - `message`: Nội dung text từ AI
  - `chunk_id`: ID của chunk (tuần tự)
- `assistant_output`: Output từ assistant
  - `message`: Nội dung từ assistant
- `file_write`: Thông báo ghi/cập nhật file
  - `filename`: Tên file
  - `content_length`: Độ dài nội dung (bytes)
  - `success`: Trạng thái thành công
  - `operation`: Loại thao tác (create/update/delete)
- `response`: Response trung gian từ AI
  - `message`: Nội dung response
- `complete`: Hoàn thành với kết quả cuối cùng
  - `response`: Response cuối cùng từ AI
  - `edited_files`: Danh sách file đã chỉnh sửa
  - `session_id`: ID session
  - `tokens_sent`: Số token gửi đi
  - `tokens_received`: Số token nhận về
  - `cost`: Chi phí API call
  - `duration_ms`: Thời gian xử lý (milliseconds)
  - `timestamp`: Thời gian hoàn thành
- `heartbeat`: Heartbeat để duy trì connection
  - `timestamp`: Thời gian heartbeat
  - `connection_id`: ID connection
- `error`: Lỗi xảy ra trong quá trình xử lý
  - `message`: Thông báo lỗi
  - `error_code`: Mã lỗi
  - `retry_after`: Thời gian chờ trước khi retry (seconds)

### 4. Lấy danh sách Models
```http
GET /models
```

### 5. Quản lý Files trong Session
```http
GET /sessions/{session_id}/files
GET /sessions/{session_id}/file_content?file_path=example.py
POST /add_file?session_id={session_id}&file_path=example.py
```

### 6. Xóa Session
```http
DELETE /sessions/{session_id}
```

## Ví dụ sử dụng

### Python Client Example (Non-streaming)

```python
import requests

# Tạo session
response = requests.post("http://localhost:8000/sessions")
session_id = response.json()["session_id"]

# Chat với Aider
chat_request = {
    "message": "Create a simple Python function to calculate fibonacci numbers",
    "session_id": session_id,
    "files": ["math_utils.py"],
    "model": "gpt-4o"
}

response = requests.post(
    "http://localhost:8000/chat",
    json=chat_request
)

result = response.json()
print(f"Response: {result['response']}")
print(f"Files edited: {len(result['edited_files'])}")
```

### Python Client Example (Streaming)

```python
import requests
import json

def handle_streaming_chat():
    # Tạo session
    response = requests.post("http://localhost:8000/sessions")
    session_id = response.json()["session_id"]
    
    # Streaming chat request
    chat_request = {
        "message": "Create a beautiful resume webpage with modern CSS",
        "session_id": session_id,
        "files": ["index.html"],
        "model": "deepseek/deepseek-coder",
        "stream": True  # Enable streaming
    }
    
    # Gửi streaming request
    response = requests.post(
        "http://localhost:8000/chat",
        json=chat_request,
        stream=True,
        headers={
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }
    )
    
    # Xử lý streaming response
    for line in response.iter_lines(decode_unicode=True):
        if line:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    
                    if event_type == "start":
                        print(f"🟢 {data.get('message', '')}")
                    elif event_type == "tool_output":
                        print(f"🔧 {data.get('message', '')}")
                    elif event_type == "ai_output":
                        print(f"🤖 {data.get('message', '')}")
                    elif event_type == "file_write":
                        print(f"📝 File: {data.get('filename')} ({data.get('content_length')} chars)")
                    elif event_type == "complete":
                        print(f"🎉 Complete! Edited {len(data.get('edited_files', []))} files")
                        break
                        
                except json.JSONDecodeError:
                    pass

handle_streaming_chat()
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function chatWithAider() {
    // Tạo session
    const sessionResponse = await axios.post('http://localhost:8000/sessions');
    const sessionId = sessionResponse.data.session_id;
    
    // Chat với Aider
    const chatResponse = await axios.post('http://localhost:8000/chat', {
        message: 'Add error handling to this function',
        session_id: sessionId,
        files: ['app.js'],
        model: 'gpt-4o'
    });
    
    console.log('Response:', chatResponse.data.response);
    console.log('Edited files:', chatResponse.data.edited_files);
}

chatWithAider();
```

### cURL Example

```bash
# Tạo session
SESSION_ID=$(curl -s -X POST http://localhost:8000/sessions | jq -r '.session_id')

# Chat với Aider
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add docstrings to all functions in this file",
    "session_id": "'$SESSION_ID'",
    "files": ["example.py"],
    "model": "gpt-4o"
  }'
```

## Testing

### Test Non-streaming API
Chạy test script để kiểm tra API:

```bash
python test_api.py
```

### Test Streaming API
Chạy test script để kiểm tra streaming:

```bash
python test_streaming.py
```

### Test với HTML Demo
Mở file `streaming_demo.html` trong browser để test streaming API với giao diện web.

## Files được tạo

- `api_server.py`: Main FastAPI server
- `api_io.py`: Custom InputOutput classes (bao gồm StreamingApiInputOutput)
- `session_manager.py`: Session management
- `config.py`: Configuration settings
- `requirements_api.txt`: Dependencies
- `test_api.py`: Test script cho non-streaming API
- `test_streaming.py`: Test script cho streaming API
- `streaming_demo.html`: HTML demo client cho streaming
- `README_API.md`: Documentation này

Test script sẽ kiểm tra:
- Health check
- List models
- Create session
- Simple chat
- Chat with files
- Session management

## Cấu hình

Các cấu hình có thể được điều chỉnh trong `config.py`:

- `API_HOST`: Host để bind API (mặc định: "0.0.0.0")
- `API_PORT`: Port để chạy API (mặc định: 8000)
- `SESSION_TIMEOUT`: Thời gian timeout cho session (mặc định: 3600 giây)
- `DEFAULT_MODEL`: Model mặc định (mặc định: "gpt-4o")
- `MAX_CONCURRENT_SESSIONS`: Số session tối đa (mặc định: 100)

## Lưu ý

1. **API Keys**: Đảm bảo bạn đã cấu hình đúng API keys cho các model bạn muốn sử dụng.

2. **Session Management**: Sessions sẽ tự động bị xóa sau khi timeout. Sử dụng endpoint delete để xóa session thủ công.

3. **File Paths**: Tất cả file paths phải là relative paths từ thư mục làm việc hiện tại.

4. **Security**: Trong môi trường production, hãy cấu hình CORS và authentication phù hợp.

5. **Performance**: API hỗ trợ xử lý đồng thời nhiều session, nhưng mỗi session chỉ xử lý một request tại một thời điểm.

## Troubleshooting

### API không khởi động được
- Kiểm tra xem port 8000 có bị chiếm không
- Đảm bảo tất cả dependencies đã được cài đặt
- Kiểm tra file config.py có đúng không

### Chat không hoạt động
- Kiểm tra API keys đã được cấu hình đúng chưa
- Xem logs để biết lỗi cụ thể
- Đảm bảo files tồn tại và có quyền đọc

### Session bị mất
- Sessions có timeout, kiểm tra cấu hình SESSION_TIMEOUT
- Sử dụng endpoint health check để kiểm tra API còn hoạt động không 