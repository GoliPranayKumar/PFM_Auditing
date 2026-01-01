"""
Configuration module for Audit Agent API.

Centralizes all environment variable access and validation.
All configuration must be accessed through this module - DO NOT use os.getenv() directly.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Security Notes:
    - Never log secret values
    - Never expose secrets via API responses
    - Never send secrets to frontend
    """
    
    # ==========================================
    # Application Settings
    # ==========================================
    app_name: str = Field(
        default="Audit Agent API",
        description="Application name"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    
    # ==========================================
    # API Server Settings
    # ==========================================
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    
    # ==========================================
    # Groq Configuration (REQUIRED for AI features)
    # ==========================================
    groq_api_key: Optional[str] = Field(
        default=None,
        description="Groq API key for AI-powered fraud detection"
    )
    
    # ==========================================
    # Resend Configuration (NEW - Preferred over Gmail)
    # ==========================================
    resend_api_key: Optional[str] = Field(
        default=None,
        description="Resend API key for sending reports"
    )
    
    # ==========================================
    # Gmail SMTP Configuration (LEGACY)
    # ==========================================
    gmail_user: Optional[str] = Field(
        default=None,
        description="Gmail email address for sending reports"
    )
    
    gmail_app_password: Optional[str] = Field(
        default=None,
        description="Gmail app password (NOT regular password)"
    )
    
    # ==========================================
    # LangChain Settings (OPTIONAL)
    # ==========================================
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangChain tracing"
    )
    
    langchain_api_key: Optional[str] = Field(
        default=None,
        description="LangChain API key for tracing"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # ==========================================
    # Validation Methods
    # ==========================================
    
    def is_groq_enabled(self) -> bool:
        """
        Check if Groq integration is enabled.
        
        Returns:
            True if Groq API key is configured and valid
        """
        return (
            self.groq_api_key is not None 
            and self.groq_api_key.strip() != "" 
            and self.groq_api_key != "your_groq_api_key_here"
        )
    
    def is_resend_enabled(self) -> bool:
        """
        Check if Resend email sending is enabled.
        
        Returns:
            True if Resend API key is configured
        """
        return (
            self.resend_api_key is not None 
            and self.resend_api_key.strip() != ""
            and self.resend_api_key != "re_123456789"
        )
    
    def is_gmail_enabled(self) -> bool:
        """
        Check if Gmail email sending is enabled.
        
        Returns:
            True if both Gmail credentials are configured
        """
        return (
            self.gmail_user is not None 
            and self.gmail_user.strip() != ""
            and self.gmail_user != "your_email@gmail.com"
            and self.gmail_app_password is not None 
            and self.gmail_app_password.strip() != ""
            and self.gmail_app_password != "your_gmail_app_password_here"
        )
        
    def is_email_enabled(self) -> bool:
        """Check if ANY email service is enabled."""
        return self.is_resend_enabled() or self.is_gmail_enabled()
    
    def get_groq_key_masked(self) -> str:
        """
        Get masked Groq API key for logging (NEVER log full key).
        
        Returns:
            Masked API key string or "Not configured"
        """
        if not self.is_groq_enabled():
            return "Not configured"
        
        key = self.groq_api_key
        if len(key) > 8:
            return f"{key[:4]}...{key[-4:]}"
        return "***"
    
    def get_email_provider(self) -> str:
        """Get the active email provider name."""
        if self.is_resend_enabled():
            return "Resend"
        if self.is_gmail_enabled():
            return "Gmail SMTP"
        return "None"
    
    def validate_startup_config(self) -> dict:
        """
        Validate configuration at startup and return status.
        
        Returns:
            Dict with validation results and warnings
        """
        status = {
            "groq_enabled": self.is_groq_enabled(),
            "email_provider": self.get_email_provider(),
            "warnings": [],
            "errors": []
        }
        
        # Check Groq
        if not self.is_groq_enabled():
            status["warnings"].append(
                "Groq API key not configured - AI analysis features will be disabled"
            )
        
        # Check Email
        if not self.is_email_enabled():
            status["warnings"].append(
                "No email credentials configured (Resend or Gmail) - email reports will be disabled"
            )
        
        return status


# ==========================================
# Global Settings Instance
# ==========================================
settings = Settings()


# ==========================================
# Helper Functions
# ==========================================

def get_groq_api_key() -> Optional[str]:
    """
    Get Groq API key if configured.
    
    Returns:
        Groq API key or None if not configured
    """
    if settings.is_groq_enabled():
        return settings.groq_api_key
    return None


def get_resend_api_key() -> Optional[str]:
    """
    Get Resend API key if configured.
    
    Returns:
        Resend API key or None
    """
    if settings.is_resend_enabled():
        return settings.resend_api_key
    return None


def get_gmail_credentials() -> Optional[tuple[str, str]]:
    """
    Get Gmail credentials if configured.
    
    Returns:
        Tuple of (gmail_user, gmail_app_password) or None if not configured
    """
    if settings.is_gmail_enabled():
        return (settings.gmail_user, settings.gmail_app_password)
    return None


def require_groq() -> str:
    """
    Require Groq API key to be configured.
    
    Returns:
        Groq API key
        
    Raises:
        RuntimeError: If Groq is not configured
    """
    if not settings.is_groq_enabled():
        raise RuntimeError(
            "Groq API key not configured. "
            "Please set GROQ_API_KEY in your .env file or environment variables."
        )
    return settings.groq_api_key


# ==========================================
# Security Note
# ==========================================
# NEVER log the following:
# - settings.groq_api_key (full value)
# - settings.gmail_app_password (full value)
# - Any other secret values
#
# ALWAYS use masked/safe versions:
# - settings.get_groq_key_masked()
# - settings.get_gmail_user_safe()
