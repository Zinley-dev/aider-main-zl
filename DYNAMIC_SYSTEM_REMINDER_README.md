# Dynamic System Reminder Implementation

## Overview

This implementation adds a **Dynamic System Reminder** feature to the aider API that automatically generates contextual system prompts based on:
- Request analysis (type, urgency, complexity)
- File types being edited
- Available image files
- Session context

## Key Features

### 1. **Request Analysis**
- **Type Detection**: Automatically identifies request types (create_new, debug, refactor, update, add_feature)
- **Urgency Detection**: Recognizes urgent requests based on keywords
- **Complexity Assessment**: Estimates complexity based on file count, message length, and keywords

### 2. **File Type-Specific Instructions**
- **Python**: PEP 8 style guide, imports, type hints
- **HTML**: DOCTYPE, semantic structure, accessibility
- **CSS**: Consistent naming, responsive design, modern features
- **JavaScript/TypeScript**: ES6+ syntax, error handling
- **JSON**: Proper syntax and structure

### 3. **Context-Aware Guidance**
- **Create New**: Instructions for new file creation
- **Debug**: Focus on identifying and fixing issues
- **Refactor**: Maintain functionality while improving structure
- **Urgent**: Prioritize speed and accuracy
- **Complex**: Break down into manageable parts

### 4. **Image Integration**
- Automatically detects available image files
- Provides context for UI development
- References images in system prompts

## Implementation Details

### Core Functions

#### `create_dynamic_system_reminder(files, request_context, image_files, conversation_history)`
Creates a comprehensive system reminder with:
- Base SEARCH/REPLACE rules
- Context-specific instructions
- File type guidance
- Critical behavioral instructions

#### `apply_dynamic_system_reminder(coder, files, request_context, image_files)`
Applies the dynamic reminder to an existing coder instance.

#### `create_enhanced_coder_with_dynamic_reminder(...)`
Creates a new coder session with dynamic reminder already applied.

### Request Analysis Functions

#### `detect_request_type(message)`
Returns one of: `create_new`, `debug`, `refactor`, `update`, `add_feature`, `general`

#### `detect_urgency(message)`
Returns: `high` or `normal` based on urgent keywords

#### `estimate_complexity(message, files)`
Returns: `low`, `medium`, or `high` based on file count, message length, and keywords

## Integration

### Updated Functions

#### `chat_stream(request)`
- Uses `create_enhanced_coder_with_dynamic_reminder()` instead of `get_or_create_session()`
- Adds request context analysis and streaming
- Logs dynamic reminder information

#### `chat_non_stream(request)`
- Uses `create_enhanced_coder_with_dynamic_reminder()` instead of `get_or_create_session()`
- Adds debug logging for system reminder

#### `create_session_controller(session_request)`
- Uses dynamic reminder for session initialization

### API Changes

The API now automatically:
1. Analyzes incoming requests
2. Generates appropriate system reminders
3. Applies them to coder instances
4. Provides context-aware guidance

## Usage Examples

### Basic Usage
```python
from api_util import create_enhanced_coder_with_dynamic_reminder

# Create coder with dynamic reminder
session, session_id = create_enhanced_coder_with_dynamic_reminder(
    files=['index.html', 'style.css'],
    request_message='Create a responsive navigation menu',
    session_context={'user_preferences': {}}
)
```

### Advanced Usage
```python
from api_util import apply_dynamic_system_reminder

# Apply to existing coder
request_context = {
    'type': 'debug',
    'urgency': 'high',
    'complexity': 'medium'
}

apply_dynamic_system_reminder(
    coder=existing_coder,
    files=['main.py'],
    request_context=request_context,
    image_files=['error_screenshot.png']
)
```

## Testing

### Test Files
- `test_dynamic_reminder.py`: Core functionality tests
- `test_integration.py`: Integration tests
- `usage_example.py`: Usage examples

### Test Results
All tests pass successfully, demonstrating:
- Correct request type detection
- Proper urgency assessment
- Accurate complexity estimation
- Context-appropriate system reminder generation
- Successful integration with existing API

## Benefits

### For Developers
- **Consistent Behavior**: AI receives appropriate instructions for each request type
- **Better Code Quality**: File type-specific guidance ensures proper standards
- **Reduced Tokens**: Only relevant instructions are included
- **Easier Maintenance**: Centralized prompt management

### For Users
- **Improved Responses**: More targeted and relevant AI behavior
- **Context Awareness**: AI understands request urgency and complexity
- **Better File Handling**: Appropriate treatment of different file types
- **Enhanced UI Development**: Automatic image reference integration

## Configuration

### File Type Extensions
The system recognizes these file types:
- **Python**: `.py`
- **HTML**: `.html`
- **CSS**: `.css`
- **JavaScript**: `.js`, `.ts`
- **JSON**: `.json`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`

### Request Keywords
- **Create**: create, new, build, make, generate
- **Debug**: fix, debug, error, bug, issue
- **Refactor**: refactor, improve, optimize, clean
- **Update**: update, modify, change, edit
- **Add Feature**: add + feature, insert, include
- **Urgent**: urgent, asap, quickly, fast, immediately, now, critical

## Backward Compatibility

The implementation maintains full backward compatibility:
- Legacy `get_or_create_session()` still works
- Existing API endpoints unchanged
- Static system prompts still supported
- No breaking changes to existing functionality

## Future Enhancements

Potential improvements:
1. **User Preferences**: Persistent user coding style preferences
2. **Project Context**: Learn from project patterns over time
3. **Language Detection**: Better natural language processing
4. **Custom Rules**: User-defined system reminder rules
5. **Analytics**: Track effectiveness of different prompt strategies

## Conclusion

The Dynamic System Reminder implementation successfully provides:
- **Contextual Intelligence**: AI understands what type of work is being requested
- **Flexible Guidance**: Appropriate instructions for different scenarios
- **Seamless Integration**: Works with existing aider architecture
- **Improved User Experience**: More relevant and helpful AI responses

This enhancement makes the aider API more intelligent and user-friendly while maintaining its core functionality and performance.