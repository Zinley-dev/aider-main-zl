# Custom Prompt System Documentation

## Overview

The Custom Prompt System is a modular, extensible framework for generating dynamic system reminders in the aider API. It provides structured prompt components, specialized templates, and intelligent template selection based on file types and request context.

## Architecture

### Core Components

#### 1. `PromptComponents` Class
Contains all the individual prompt components:
- **Base Rules**: Core SEARCH/REPLACE formatting rules
- **Critical Instructions**: Behavioral requirements
- **File Type Instructions**: Language-specific guidance
- **Request Type Instructions**: Context-specific guidance
- **Urgency Instructions**: Priority-based guidance
- **Complexity Instructions**: Scope-based guidance
- **Image Instructions**: Visual reference guidance

#### 2. `PromptBuilder` Class
Fluent API for building custom prompts:
```python
builder = PromptBuilder()
prompt = (builder
    .add_base_rules()
    .add_context_instructions(files, request_context, image_files)
    .add_critical_instructions()
    .add_file_list(files)
    .add_ending_instruction()
    .build())
```

#### 3. `CustomPromptTemplates` Class
Pre-configured templates for common scenarios:
- **Web Development Template**: HTML, CSS, JavaScript optimization
- **Python Development Template**: PEP 8, typing, best practices
- **Debug Template**: Issue identification and resolution
- **Refactor Template**: Code improvement and restructuring

#### 4. Main Functions
- `create_custom_dynamic_system_reminder()`: Main function with template selection
- `create_web_prompt()`: Web development convenience function
- `create_python_prompt()`: Python development convenience function  
- `create_debug_prompt()`: Debugging convenience function
- `create_refactor_prompt()`: Refactoring convenience function

## Supported File Types

### Programming Languages
- **Python** (`.py`): PEP 8 style guide, imports, type hints
- **JavaScript** (`.js`): ES6+ syntax, error handling, formatting
- **TypeScript** (`.ts`): Modern syntax, typing, error handling
- **React JSX** (`.jsx`): React best practices, hooks, components
- **React TypeScript** (`.tsx`): React + TypeScript best practices

### Web Technologies
- **HTML** (`.html`): DOCTYPE, semantic structure, accessibility
- **CSS** (`.css`): Naming conventions, responsive design, modern features

### Data Formats
- **JSON** (`.json`): Proper syntax and structure
- **XML** (`.xml`): Proper syntax and structure
- **YAML** (`.yaml`, `.yml`): Proper syntax and indentation

### Other Formats
- **Markdown** (`.md`): Proper syntax and structure
- **SQL** (`.sql`): Proper syntax, formatting, naming conventions
- **Dockerfile**: Docker best practices, official images, size optimization
- **Shell Scripts** (`.sh`): Shell syntax, error handling, best practices
- **Batch Files** (`.bat`): Batch syntax and error handling
- **PowerShell** (`.ps1`): PowerShell syntax and best practices

## Request Type Detection

### Supported Request Types
- **create_new**: Creating new files or features
- **debug**: Fixing bugs and issues
- **refactor**: Improving code structure and performance
- **update**: Modifying existing functionality
- **add_feature**: Adding new functionality
- **general**: General tasks

### Keywords for Detection
- **Create**: create, new, build, make, generate
- **Debug**: fix, debug, error, bug, issue
- **Refactor**: refactor, improve, optimize, clean
- **Update**: update, modify, change, edit
- **Add Feature**: add + feature, insert, include
- **Urgent**: urgent, asap, quickly, fast, immediately, now, critical

## Usage Examples

### Basic Usage
```python
from custom_prompt import create_custom_dynamic_system_reminder

# Create a dynamic system reminder
prompt = create_custom_dynamic_system_reminder(
    files=['index.html', 'style.css'],
    request_context={
        'type': 'create_new',
        'urgency': 'normal',
        'complexity': 'medium'
    },
    image_files=['mockup.png']
)
```

### Using Specialized Templates
```python
from custom_prompt import create_web_prompt, create_python_prompt

# Web development template
web_prompt = create_web_prompt(
    files=['app.js', 'index.html'],
    request_context={'type': 'create_new', 'urgency': 'normal', 'complexity': 'low'},
    image_files=['design.png']
)

# Python development template
python_prompt = create_python_prompt(
    files=['main.py', 'utils.py'],
    request_context={'type': 'refactor', 'urgency': 'normal', 'complexity': 'high'}
)
```

### Using the Builder Pattern
```python
from custom_prompt import PromptBuilder

builder = PromptBuilder()
custom_prompt = (builder
    .add_base_rules()
    .add_context_instructions(files, request_context, image_files)
    .add_critical_instructions()
    .add_file_list(files)
    .add_ending_instruction()
    .build())
```

### Template Selection
```python
# Automatic template selection
prompt = create_custom_dynamic_system_reminder(
    files=['index.html', 'app.js'],
    request_context={'type': 'create_new', 'urgency': 'normal', 'complexity': 'medium'},
    image_files=['wireframe.png']
)

# Explicit template selection
prompt = create_custom_dynamic_system_reminder(
    files=['main.py'],
    request_context={'type': 'debug', 'urgency': 'high', 'complexity': 'low'},
    use_template='debug'
)
```

## Integration with API

### Updated Functions
The system integrates seamlessly with the existing API:

```python
# In api_util.py
def create_dynamic_system_reminder(files, request_context, image_files=None, conversation_history=None):
    from custom_prompt import create_custom_dynamic_system_reminder
    
    return create_custom_dynamic_system_reminder(
        files=files,
        request_context=request_context,
        image_files=image_files,
        conversation_history=conversation_history
    )

# Enhanced version with automatic template selection
def create_optimized_system_reminder(files, request_context, image_files=None, conversation_history=None):
    from custom_prompt import create_web_prompt, create_python_prompt, create_debug_prompt, create_refactor_prompt
    
    # Intelligent template selection logic
    # ... (see implementation in api_util.py)
```

## Template Specialization

### Web Development Template
Optimized for HTML, CSS, JavaScript development:
- HTML semantic structure guidance
- CSS responsive design principles
- JavaScript ES6+ best practices
- Image reference integration
- Accessibility considerations

### Python Development Template
Optimized for Python development:
- PEP 8 style guide enforcement
- Import organization
- Type hints usage
- Error handling patterns
- Testing considerations

### Debug Template
Optimized for debugging tasks:
- Issue identification focus
- Forced high urgency
- Systematic approach guidance
- Testing requirements
- Error isolation techniques

### Refactor Template
Optimized for code improvement:
- Functionality preservation
- Structure improvement guidance
- Performance considerations
- Testing requirements
- Backward compatibility

## Extensibility

### Adding New File Types
```python
# In custom_prompt.py -> PromptComponents.FILE_TYPE_INSTRUCTIONS
'.go': "For Go files: Follow Go formatting standards, use proper error handling, and maintain package structure.",
'.rust': "For Rust files: Follow Rust conventions, use proper error handling, and leverage the type system.",
```

### Adding New Request Types
```python
# In custom_prompt.py -> PromptComponents.REQUEST_TYPE_INSTRUCTIONS
'optimize': "Optimization: Focus on performance improvements while maintaining functionality.",
'security': "Security: Identify and fix security vulnerabilities with proper validation.",
```

### Creating Custom Templates
```python
@staticmethod
def mobile_development_template(files: List[str], request_context: dict) -> str:
    """Template optimized for mobile development"""
    builder = PromptBuilder()
    
    mobile_context = request_context.copy()
    mobile_context['type'] = mobile_context.get('type', 'create_new')
    
    return (builder
            .add_base_rules()
            .add_context_instructions(files, mobile_context)
            .add_critical_instructions()
            .add_file_list(files)
            .add_ending_instruction()
            .build())
```

## Testing

### Test Files
- `test_custom_prompt.py`: Core functionality tests
- `test_integration.py`: Integration tests
- `custom_prompt_demo.py`: Feature demonstration

### Running Tests
```bash
# Test core functionality
python test_custom_prompt.py

# Test integration
python test_integration.py

# Run demonstration
python custom_prompt_demo.py
```

## Benefits

### For Developers
- **Modular Design**: Easy to extend and modify
- **Type Safety**: Clear interfaces and documentation
- **Consistent Output**: Standardized prompt generation
- **Template Reuse**: Common patterns encapsulated
- **Easy Testing**: Isolated components for unit testing

### For AI Performance
- **Context Awareness**: Appropriate instructions for each scenario
- **File Type Optimization**: Language-specific guidance
- **Urgency Handling**: Priority-based instruction adjustment
- **Complexity Management**: Scope-appropriate guidance
- **Consistency**: Standardized format across all prompts

### For Maintainability
- **Single Source of Truth**: All prompt components in one place
- **Easy Updates**: Centralized modification points
- **Clear Separation**: Components, builders, and templates separated
- **Documentation**: Comprehensive inline documentation
- **Version Control**: Easy to track prompt evolution

## Performance Considerations

### Prompt Length Optimization
- **Contextual Inclusion**: Only relevant instructions included
- **Template Selection**: Specialized templates reduce unnecessary content
- **Efficient Building**: Builder pattern minimizes string concatenation
- **Caching Potential**: Templates can be cached for performance

### Token Efficiency
- **Focused Content**: Only necessary instructions for each scenario
- **Reduced Redundancy**: Shared components prevent duplication
- **Smart Selection**: Automatic template selection optimizes content
- **Length Monitoring**: Built-in length tracking and optimization

## Future Enhancements

### Planned Features
1. **User Preferences**: Persistent user coding style preferences
2. **Project Context**: Learn from project patterns over time
3. **Language Detection**: Better natural language processing
4. **Custom Rules**: User-defined prompt components
5. **Analytics**: Track prompt effectiveness
6. **Caching**: Template and component caching
7. **A/B Testing**: Compare different prompt strategies

### Extension Points
- **New Languages**: Easy addition of new programming languages
- **Custom Templates**: Framework for domain-specific templates
- **Dynamic Components**: Runtime component generation
- **External Integration**: Plugin system for third-party extensions
- **Machine Learning**: Adaptive prompt generation based on success rates

## Conclusion

The Custom Prompt System provides a robust, extensible framework for generating contextually appropriate system reminders. It successfully separates concerns, improves maintainability, and enhances AI performance through intelligent template selection and context-aware instruction generation.

The system is production-ready and fully integrated with the existing aider API, providing immediate benefits while maintaining backward compatibility and offering a clear path for future enhancements.