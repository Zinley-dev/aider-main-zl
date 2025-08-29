"""
Custom prompt components for dynamic system reminder generation
"""

from typing import List, Dict, Optional

from prompt_service import get_prompt

class PromptComponents:
    """
    Centralized prompt components for dynamic system reminder generation
    """
    
    # Base SEARCH/REPLACE rules that are always included
    BASE_RULES = get_prompt('AIDER_API', 'BASE_RULES')
    # Critical behavioral instructions that are always included
    CRITICAL_INSTRUCTIONS = get_prompt('AIDER_API', 'CRITICAL_INSTRUCTIONS')
    # File type specific instructions
    FILE_TYPE_INSTRUCTIONS = {
        '.py': "For Python files: Follow PEP 8 style guide, maintain proper imports, and use type hints where appropriate.",
        '.html': "For HTML files: Maintain proper DOCTYPE, semantic structure, and accessibility standards.",
        '.css': "For CSS files: Use consistent naming conventions, responsive design principles, and modern CSS features.",
        '.js': "For JavaScript/TypeScript: Use modern ES6+ syntax, proper error handling, and consistent formatting.",
        '.ts': "For JavaScript/TypeScript: Use modern ES6+ syntax, proper error handling, and consistent formatting.",
        '.jsx': "For React JSX: Follow React best practices, use hooks appropriately, and maintain component structure.",
        '.tsx': "For React TypeScript: Follow React best practices, use hooks appropriately, and maintain component structure with proper typing.",
        '.json': "For JSON files: Maintain proper JSON syntax and structure.",
        '.xml': "For XML files: Maintain proper XML syntax and structure.",
        '.yaml': "For YAML files: Maintain proper YAML syntax and indentation.",
        '.yml': "For YAML files: Maintain proper YAML syntax and indentation.",
        '.md': "For Markdown files: Follow proper Markdown syntax and structure.",
        '.sql': "For SQL files: Use proper SQL syntax, consistent formatting, and appropriate naming conventions.",
        '.dockerfile': "For Dockerfile: Follow Docker best practices, use official base images, and optimize for size.",
        '.sh': "For shell scripts: Use proper shell syntax, error handling, and follow shell scripting best practices.",
        '.bat': "For batch files: Use proper batch syntax and error handling.",
        '.ps1': "For PowerShell: Use proper PowerShell syntax and follow PowerShell best practices."
    }

    # Request type specific instructions
    REQUEST_TYPE_INSTRUCTIONS = {
        'create_new': "Creating new files: Use empty SEARCH section and full content in REPLACE section.",
        'debug': "Debugging: Focus on identifying and fixing the specific issue mentioned. Test your changes.",
        'refactor': "Refactoring: Maintain functionality while improving code structure, readability, and performance.",
        'update': "Updating: Make precise changes while preserving existing functionality and code style.",
        'add_feature': "Adding features: Integrate new functionality seamlessly with existing code patterns.",
        'general': "General task: Analyze the request carefully and apply appropriate coding practices."
    }

    # Urgency level instructions
    URGENCY_INSTRUCTIONS = {
        'high': "URGENT REQUEST: Prioritize speed and accuracy. Focus on core functionality first.",
        'normal': "Standard request: Take time to ensure quality and follow best practices."
    }

    # Complexity level instructions
    COMPLEXITY_INSTRUCTIONS = {
        'low': "Simple task: Focus on clean, straightforward implementation.",
        'medium': "Moderate complexity: Ensure all changes work together cohesively.",
        'high': "Complex request: Break down into smaller, manageable changes. Test each part."
    }

    # Image context instructions
    IMAGE_INSTRUCTIONS = {
        'has_images': "Images available for reference: {image_list}",
        'use_images': "Use these images as visual reference when building UI components or implementing designs."
    }

    # Ending instruction
    ENDING_INSTRUCTION = "\n\nONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!"

class PromptBuilder:
    """
    Builder class for constructing dynamic system reminders
    """
    
    def __init__(self):
        self.components = PromptComponents()
        self.sections = []
    
    def add_base_rules(self) -> 'PromptBuilder':
        """Add the base SEARCH/REPLACE rules"""
        self.sections.append(self.components.BASE_RULES)
        return self
    
    def add_context_instructions(self, 
                               files: List[str],
                               request_context: dict,
                               image_files: List[str] = None) -> 'PromptBuilder':
        """Add context-specific instructions based on files and request context"""
        
        context_instructions = []
        
        # Add file type specific instructions
        if files:
            file_extensions = {self._get_file_extension(f) for f in files}
            for ext in file_extensions:
                if ext in self.components.FILE_TYPE_INSTRUCTIONS:
                    context_instructions.append(f"- {self.components.FILE_TYPE_INSTRUCTIONS[ext]}")
        
        # Add request type instructions
        request_type = request_context.get('type', 'general')
        if request_type in self.components.REQUEST_TYPE_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.REQUEST_TYPE_INSTRUCTIONS[request_type]}")
        
        # Add urgency instructions
        urgency = request_context.get('urgency', 'normal')
        if urgency in self.components.URGENCY_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.URGENCY_INSTRUCTIONS[urgency]}")
        
        # Add complexity instructions
        complexity = request_context.get('complexity', 'low')
        if complexity in self.components.COMPLEXITY_INSTRUCTIONS:
            context_instructions.append(f"- {self.components.COMPLEXITY_INSTRUCTIONS[complexity]}")
        
        # Add image context if available
        if image_files:
            image_list = ', '.join(image_files)
            context_instructions.append(f"- {self.components.IMAGE_INSTRUCTIONS['has_images'].format(image_list=image_list)}")
            context_instructions.append(f"- {self.components.IMAGE_INSTRUCTIONS['use_images']}")
        
        # Add the context section if there are instructions
        if context_instructions:
            context_section = "\n\n# Context-Specific Instructions:\n" + '\n'.join(context_instructions)
            self.sections.append(context_section)
        
        return self
    
    def add_critical_instructions(self) -> 'PromptBuilder':
        """Add critical behavioral instructions"""
        self.sections.append(self.components.CRITICAL_INSTRUCTIONS)
        return self
    
    def add_file_list(self, files: List[str]) -> 'PromptBuilder':
        """Add the list of files to edit"""
        if files:
            file_section = f"\n\nFiles to edit: {', '.join(files)}"
            self.sections.append(file_section)
        return self
    
    def add_ending_instruction(self) -> 'PromptBuilder':
        """Add the final instruction"""
        self.sections.append(self.components.ENDING_INSTRUCTION)
        return self
    
    def build(self) -> str:
        """Build the complete system reminder"""
        return ''.join(self.sections)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get the file extension from filename"""
        import os
        return os.path.splitext(filename)[1].lower()

class CustomPromptTemplates:
    """
    Pre-defined prompt templates for common scenarios
    """
    
    @staticmethod
    def web_development_template(files: List[str], request_context: dict, image_files: List[str] = None) -> str:
        """Template optimized for web development tasks"""
        builder = PromptBuilder()
        
        # Add web-specific context
        web_context = request_context.copy()
        if not web_context.get('type'):
            web_context['type'] = 'create_new'
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, web_context, image_files)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def python_development_template(files: List[str], request_context: dict) -> str:
        """Template optimized for Python development tasks"""
        builder = PromptBuilder()
        
        # Add Python-specific context
        python_context = request_context.copy()
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, python_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def debug_template(files: List[str], request_context: dict) -> str:
        """Template optimized for debugging tasks"""
        builder = PromptBuilder()
        
        # Force debug context with high urgency by default
        debug_context = request_context.copy()
        debug_context['type'] = 'debug'
        debug_context['urgency'] = 'high'  # Always high urgency for debug
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, debug_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())
    
    @staticmethod
    def refactor_template(files: List[str], request_context: dict) -> str:
        """Template optimized for refactoring tasks"""
        builder = PromptBuilder()
        
        # Force refactor context
        refactor_context = request_context.copy()
        refactor_context['type'] = 'refactor'
        refactor_context['complexity'] = request_context.get('complexity', 'medium')
        
        return (builder
                .add_base_rules()
                .add_context_instructions(files, refactor_context)
                .add_critical_instructions()
                .add_file_list(files)
                .add_ending_instruction()
                .build())

def create_custom_dynamic_system_reminder(
    files: List[str], 
    request_context: dict,
    image_files: List[str] = None,
    conversation_history: List[dict] = None,
    use_template: Optional[str] = None
) -> str:
    """
    Create a dynamic system reminder using the custom prompt system
    
    Args:
        files: List of files to edit
        request_context: Context about the request (type, urgency, complexity)
        image_files: List of available image files
        conversation_history: Previous conversation (not used currently)
        use_template: Optional template to use ('web', 'python', 'debug', 'refactor')
    
    Returns:
        Generated system reminder string
    """
    
    # Use specific template if requested
    if use_template:
        templates = CustomPromptTemplates()
        if use_template == 'web':
            return templates.web_development_template(files, request_context, image_files)
        elif use_template == 'python':
            return templates.python_development_template(files, request_context)
        elif use_template == 'debug':
            return templates.debug_template(files, request_context)
        elif use_template == 'refactor':
            return templates.refactor_template(files, request_context)
    
    # Use default builder
    builder = PromptBuilder()
    
    return (builder
            .add_base_rules()
            .add_context_instructions(files, request_context, image_files)
            .add_critical_instructions()
            .add_file_list(files)
            .add_ending_instruction()
            .build())

# Convenience functions for common use cases
def create_web_prompt(files: List[str], request_context: dict, image_files: List[str] = None) -> str:
    """Create a web development optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, image_files, use_template='web')

def create_python_prompt(files: List[str], request_context: dict) -> str:
    """Create a Python development optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='python')

def create_debug_prompt(files: List[str], request_context: dict) -> str:
    """Create a debugging optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='debug')

def create_refactor_prompt(files: List[str], request_context: dict) -> str:
    """Create a refactoring optimized prompt"""
    return create_custom_dynamic_system_reminder(files, request_context, use_template='refactor')
