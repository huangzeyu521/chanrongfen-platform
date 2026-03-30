from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union

class Settings(BaseSettings):
    APP_NAME: str = "产融分平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./chanrongfen.db"

    # Security
    SECRET_KEY: str = "changeme-in-production-use-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20

    # CORS — supports comma-separated string from env: ALLOWED_ORIGINS="https://a.com,https://b.com"
    # Set ALLOWED_ORIGINS="*" to allow all (use for Render when Vercel URL is unknown)
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"

settings = Settings()
