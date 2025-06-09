from aider.io import InputOutput

class ApiInputOutput(InputOutput):
    """
    Lớp InputOutput đặc biệt cho REST API
    Không yêu cầu đầu vào từ người dùng và capture tất cả output
    """
    
    def __init__(self):
        super().__init__(yes=True, pretty=False)
        self.output_buffer = []
        self.error_buffer = []
        self.warning_buffer = []
    
    def tool_output(self, msg, log_only=False):
        """Capture tool output"""
        if not log_only:
            self.output_buffer.append(str(msg))
        super().tool_output(msg, log_only=log_only)
    
    def tool_error(self, msg):
        """Capture tool errors"""
        self.error_buffer.append(str(msg))
        super().tool_error(msg)
    
    def tool_warning(self, msg):
        """Capture tool warnings"""
        self.warning_buffer.append(str(msg))
        super().tool_warning(msg)
    
    def user_input(self, msg):
        """Override user input - không cần input từ user trong API"""
        self.output_buffer.append(f"User: {msg}")
        super().user_input(msg)
    
    def ai_output(self, msg, pretty=None):
        """Capture AI output"""
        self.output_buffer.append(f"AI: {msg}")
        super().ai_output(msg, pretty)
    
    def assistant_output(self, msg, pretty=None):
        """Capture assistant output"""
        self.output_buffer.append(f"Assistant: {msg}")
        super().assistant_output(msg, pretty)
    
    def get_input(self, root, files, addable_files, commands, read_only_files, edit_format=None):
        """
        Override get_input - không gọi input từ người dùng trong API
        Trả về None để báo hiệu không có input
        """
        return None
    
    def confirm_ask(self, question, default="y", subject=None, group=None, allow_never=False):
        """
        Override confirm_ask - tự động trả về True cho tất cả xác nhận
        """
        self.output_buffer.append(f"Auto-confirmed: {question}")
        return True
    
    def get_captured_output(self):
        """Lấy tất cả output đã capture và clear buffer"""
        output = "\n".join(self.output_buffer)
        self.output_buffer = []
        return output
    
    def get_captured_errors(self):
        """Lấy tất cả errors đã capture và clear buffer"""
        errors = "\n".join(self.error_buffer)
        self.error_buffer = []
        return errors
    
    def get_captured_warnings(self):
        """Lấy tất cả warnings đã capture và clear buffer"""
        warnings = "\n".join(self.warning_buffer)
        self.warning_buffer = []
        return warnings
    
    def clear_buffers(self):
        """Clear tất cả buffers"""
        self.output_buffer = []
        self.error_buffer = []
        self.warning_buffer = []
    
    def get_all_captured(self):
        """Lấy tất cả captured content"""
        return {
            "output": self.get_captured_output(),
            "errors": self.get_captured_errors(),
            "warnings": self.get_captured_warnings()
        } 