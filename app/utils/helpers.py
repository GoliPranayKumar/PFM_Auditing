"""Helper utility functions."""

from typing import Any, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_request(endpoint: str, data: Dict[str, Any]) -> None:
    """
    Log incoming API request.
    
    Args:
        endpoint: API endpoint path
        data: Request data
    """
    logger.info(f"Request to {endpoint}: {data}")


def log_response(endpoint: str, status_code: int) -> None:
    """
    Log API response.
    
    Args:
        endpoint: API endpoint path
        status_code: HTTP status code
    """
    logger.info(f"Response from {endpoint}: {status_code}")


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    # Basic sanitization - expand as needed
    return text.strip()
