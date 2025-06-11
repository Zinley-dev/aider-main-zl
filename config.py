import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Cấu hình cho Aider REST API
    """
    
    # API Settings
    API_TITLE: str = "Aider REST API"
    API_VERSION: str = "0.1.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Session Settings
    SESSION_TIMEOUT: int = 3600  # 1 giờ (3600 giây)
    
    # Model Settings
    DEFAULT_MODEL: str = "snowx/gpt-4o"
    
    # API Keys - sẽ được load từ environment variables
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    
    # Security Settings
    CORS_ORIGINS: list = ["*"]  # Trong production nên hạn chế
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    
    # File Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: list = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt", ".scala",
        ".html", ".css", ".scss", ".sass", ".less", ".xml", ".json",
        ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".md", ".txt",
        ".sql", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd"
    ]
    
    # Git Settings
    AUTO_COMMIT: bool = True
    COMMIT_MESSAGE_PREFIX: str = "aider: "
    
    # Performance Settings
    MAX_CONCURRENT_SESSIONS: int = 100
    REQUEST_TIMEOUT: int = 300  # 5 phút
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Tạo instance settings global
settings = Settings()

# Validation functions
def validate_api_key(model_name: str) -> bool:
    """
    Kiểm tra xem API key có được cấu hình cho model không
    """
    if model_name.startswith("gpt-") or model_name.startswith("o1-") or model_name.startswith("o3-"):
        return bool(settings.OPENAI_API_KEY)
    elif model_name.startswith("claude-"):
        return bool(settings.ANTHROPIC_API_KEY)
    elif model_name.startswith("deepseek"):
        return bool(settings.DEEPSEEK_API_KEY)
    else:
        # Cho các model khác, giả sử đã được cấu hình
        return True

def get_required_env_vars() -> dict:
    """
    Lấy danh sách các environment variables cần thiết
    """
    return {
        "OPENAI_API_KEY": "Required for OpenAI models (GPT-4, etc.)",
        "ANTHROPIC_API_KEY": "Required for Anthropic models (Claude, etc.)",
        "DEEPSEEK_API_KEY": "Required for DeepSeek models"
    }

def check_configuration() -> dict:
    """
    Kiểm tra cấu hình và trả về status
    """
    status = {
        "api_configured": True,
        "models_available": [],
        "missing_keys": [],
        "warnings": []
    }
    
    # Kiểm tra API keys
    if settings.OPENAI_API_KEY:
        status["models_available"].extend(["gpt-4o", "gpt-4", "gpt-3.5-turbo"])
    else:
        status["missing_keys"].append("OPENAI_API_KEY")
    
    if settings.ANTHROPIC_API_KEY:
        status["models_available"].extend(["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"])
    else:
        status["missing_keys"].append("ANTHROPIC_API_KEY")
    
    if settings.DEEPSEEK_API_KEY:
        status["models_available"].extend(["deepseek-chat", "deepseek-coder"])
    else:
        status["missing_keys"].append("DEEPSEEK_API_KEY")
    
    # Warnings
    if not status["models_available"]:
        status["warnings"].append("No API keys configured - API will not work")
    
    if settings.CORS_ORIGINS == ["*"]:
        status["warnings"].append("CORS is set to allow all origins - consider restricting in production")
    
    return status 