# Aider API Test UI

A simple HTML/JavaScript interface for testing the Aider API endpoints.

## Files

- `api_test_ui.html` - Main test interface
- `api_test_utils.js` - Utility functions and API client class
- `README_API_TEST_UI.md` - This documentation

## Features

### 🔧 API Configuration
- Configure the API base URL (defaults to `http://localhost:8000`)
- Test API health and connectivity

### 📁 Session Management
- Create new sessions with customizable options:
  - Model selection (GPT-4o, Claude, etc.)
  - Repository path (optional, creates temp folder if not specified)
  - File list (comma-separated)
  - Edit format (diff, whole, udiff)
- View current session information
- Delete sessions

### 💬 Chat Interface
- Send messages to the AI coder
- Support for both streaming and non-streaming responses
- Real-time streaming events display
- Predefined test scenarios

### 📄 File Management
- View files in the current session
- Get file content
- Auto-refresh file list after operations

### 🔍 API Status
- Health check endpoint
- List available models

## How to Use

### 1. Start the API Server

First, make sure your Aider API server is running:

```bash
python api_server.py
```

The server should start on `http://localhost:8000` by default.

### 2. Open the Test UI

Open `api_test_ui.html` in your web browser. You can do this by:

- Double-clicking the file
- Or serving it via a local web server:
  ```bash
  python -m http.server 8080
  # Then open http://localhost:8080/api_test_ui.html
  ```

### 3. Test the API

#### Basic Workflow:

1. **Check API Status**: Click "Check Health" to verify the API is running
2. **Create Session**: 
   - Select a model
   - Optionally specify files (defaults to `index.html`)
   - Click "Create Session"
3. **Send Messages**:
   - Enter a message (e.g., "Create a simple HTML page with a button")
   - Choose streaming or non-streaming mode
   - Click "Send Message"
4. **View Results**:
   - Check the response in the chat section
   - View files in the "File Management" section
   - Click on files to see their content

#### Example Test Messages:

- **Simple HTML**: "Create a simple HTML page with a header, some content, and a button that shows an alert when clicked"
- **Todo App**: "Create a todo application with HTML, CSS, and JavaScript. Include add, delete, and mark complete functionality."
- **Calculator**: "Create a calculator web app with HTML, CSS, and JavaScript that can perform basic arithmetic operations."

## API Client Class

The `api_test_utils.js` file includes an `AiderApiClient` class that you can use programmatically:

```javascript
const client = new AiderApiClient('http://localhost:8000');

// Create a session
const sessionResult = await client.createSession({
    model: 'gpt-4o-mini',
    files: ['index.html', 'style.css']
});

// Send a message
const chatResult = await client.sendMessage('Create a simple web page');

// Stream a message
await client.streamMessage('Create a todo app', (eventType, data) => {
    console.log(`${eventType}: ${data}`);
});

// Get files
const filesResult = await client.getFiles();

// Get file content
const contentResult = await client.getFileContent('index.html');
```

## Troubleshooting

### Common Issues:

1. **CORS Errors**: Make sure your API server has CORS properly configured for your domain
2. **Connection Refused**: Verify the API server is running and the URL is correct
3. **Streaming Issues**: EventSource may have limitations in some browsers - try non-streaming mode
4. **Session Not Found**: Sessions may expire - create a new session if you get 404 errors

### API Server CORS Configuration:

Make sure your `api_server.py` has CORS middleware configured:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Endpoints Tested

- `POST /sessions` - Create session
- `DELETE /sessions/{session_id}` - Delete session
- `POST /chat` - Send chat message (streaming and non-streaming)
- `GET /sessions/{session_id}/files` - Get session files
- `GET /sessions/{session_id}/file_content` - Get file content
- `GET /health` - Health check
- `GET /models` - List available models

## Browser Compatibility

- Modern browsers with Fetch API support
- EventSource support for streaming (most modern browsers)
- ES6+ features used (arrow functions, async/await, classes)

## Security Notes

- This is a development/testing tool - not recommended for production use
- The API client doesn't include authentication mechanisms
- CORS is set to allow all origins for testing purposes 