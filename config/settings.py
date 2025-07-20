"""
Configuration settings for the Telegram Shop Bot.
"""
import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Bot Configuration
    telegram_bot_token: str
    webhook_url: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./shopbot.db"
    database_url_dev: str = "sqlite:///./shopbot.db"
    
    # NOWPayments API
    nowpayments_api_key: str
    nowpayments_ipn_secret: str
    nowpayments_sandbox: bool = True
    nowpayments_base_url: str = "https://api-sandbox.nowpayments.io"
    
    # Security
    secret_key: str
    jwt_secret_key: str
    encryption_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Admin Panel
    admin_username: str = "admin"
    admin_password: str
    admin_email: str
    
    # File Storage
    cloudinary_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bucket_name: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    environment: str = "production"
    log_level: str = "INFO"
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: str = "jpg,jpeg,png,gif,pdf,zip,rar"
    
    # Payment Settings
    minimum_order_amount: float = 1.00
    maximum_order_amount: float = 10000.00
    payment_timeout_minutes: int = 30
    
    # Rate Limiting
    rate_limit_per_minute: int = 30
    rate_limit_per_hour: int = 1000
    
    # Backup Settings
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    
    # Analytics
    google_analytics_id: Optional[str] = None
    
    # Multi-language
    default_language: str = "en"
    supported_languages: str = "en,lt"
    
    @validator("supported_languages")
    def validate_languages(cls, v):
        """Validate and convert supported languages to list."""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v
    
    @validator("allowed_file_types")
    def validate_file_types(cls, v):
        """Validate and convert allowed file types to list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @validator("nowpayments_base_url")
    def set_nowpayments_url(cls, v, values):
        """Set NOWPayments URL based on sandbox setting."""
        sandbox = values.get("nowpayments_sandbox", True)
        if sandbox:
            return "https://api-sandbox.nowpayments.io"
        return "https://api.nowpayments.io"
    
    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Validate encryption key length."""
        if len(v) != 32:
            raise ValueError("Encryption key must be exactly 32 characters long")
        return v
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        if self.environment == "development":
            return self.database_url_dev
        return self.database_url
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL."""
        url = self.database_url_sync
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return url


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings