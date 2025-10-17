from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_file_size_mb: int = 10
    supported_formats: list[str] = [
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp", "image/tiff"
    ]
    rate_limit: str = "10/minute" 
    cache_size: int = 100  
    vision_retry_attempts: int = 3

settings = Settings()