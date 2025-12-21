"""
FastAPI application entry point for Audit Agent API.

AI-powered fraud, waste, and abuse detection system for public expenditure.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.routes import health, audit, document, upload
from app.utils.logger import setup_logging, get_logger

# Initialize logging
setup_logging(level="DEBUG" if settings.debug else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events with:
    - Configuration validation
    - Graceful degradation for missing credentials
    - Clear status logging
    """
    # ========================================
    # STARTUP
    # ========================================
    logger.info("=" * 80)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("=" * 80)
    
    # Validate configuration
    logger.info("Validating configuration...")
    config_status = settings.validate_startup_config()
    
    # ========================================
    # Groq Integration Status
    # ========================================
    if config_status["groq_enabled"]:
        logger.info("✅ Groq AI integration enabled")
        logger.info(f"   API Key: {settings.get_groq_key_masked()}")
    else:
        logger.warning("⚠️  Groq AI integration disabled")
        logger.warning("   Reason: Groq API key not configured")
        logger.warning("   Impact: AI fraud analysis features will not work")
        logger.warning("   Action: Set GROQ_API_KEY in .env file to enable")
    
    # ========================================
    # Gmail SMTP Status
    # ========================================
    if config_status["gmail_enabled"]:
        logger.info("✅ Gmail email sending enabled")
        logger.info(f"   Gmail User: {settings.get_gmail_user_safe()}")
    else:
        logger.warning("ℹ️  Gmail email sending disabled")
        logger.warning("   Reason: Gmail credentials not configured")
        logger.warning("   Impact: Email reports will not be sent")
        logger.warning("   Action: Set GMAIL_USER and GMAIL_APP_PASSWORD to enable (optional)")
    
    # ========================================
    # Warnings and Errors
    # ========================================
    if config_status["warnings"]:
        logger.info("-" * 80)
        logger.info("Configuration Warnings:")
        for warning in config_status["warnings"]:
            logger.warning(f"  • {warning}")
    
    if config_status["errors"]:
        logger.error("=" * 80)
        logger.error("CRITICAL CONFIGURATION ERRORS:")
        for error in config_status["errors"]:
            logger.error(f"  • {error}")
        logger.error("=" * 80)
        raise RuntimeError("Critical configuration errors - cannot start application")
    
    # ========================================
    # Directories
    # ========================================
    logger.info("-" * 80)
    logger.info("Application Directories:")
    logger.info(f"  📊 Logs: ./logs/")
    logger.info(f"  📂 Uploads: ./uploads/")
    logger.info(f"  📈 Visualizations: ./visualizations/")
    
    # ========================================
    # Ready
    # ========================================
    logger.info("-" * 80)
    logger.info("✅ Application startup complete!")
    logger.info("🎯 Server ready to accept requests")
    logger.info("📚 API documentation: http://localhost:8000/docs")
    logger.info("=" * 80)
    
    yield
    
    # ========================================
    # SHUTDOWN
    # ========================================
    logger.info("=" * 80)
    logger.info("🛑 Shutting down application...")
    logger.info("✅ Cleanup completed")
    logger.info("=" * 80)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered audit agent for detecting fraud, waste, and abuse in public expenditure",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files for visualizations
from fastapi.staticfiles import StaticFiles
import os

# Create visualizations directory if it doesn't exist
os.makedirs("visualizations", exist_ok=True)
app.mount("/visualizations", StaticFiles(directory="visualizations"), name="visualizations")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(audit.router)
app.include_router(document.router)
app.include_router(upload.router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "apis": {
            "transaction_audit": "/api/v1/audit",
            "document_analysis": "/api/v1/document",
            "file_upload": "/api/v1/upload"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
