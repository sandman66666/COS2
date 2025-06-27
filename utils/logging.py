# utils/logging.py
"""
Structured logging configuration for the Strategic Intelligence System.
Uses loguru for enhanced logging capabilities.
"""
import sys
import json
from pathlib import Path
from loguru import logger

from config.settings import LOG_LEVEL, ENVIRONMENT

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure loguru logger
logger.remove()  # Remove default handler

# Add console handler
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    diagnose=True,
    backtrace=True
)

# Add file handler for JSON logs
logger.add(
    logs_dir / "app.json",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=LOG_LEVEL,
    serialize=True,  # Output logs as JSON
    rotation="500 MB",  # Rotate files when they reach 500MB
    retention="10 days",  # Keep logs for 10 days
)

# Add context to all logs
logger = logger.bind(environment=ENVIRONMENT)

# Custom log formatter for structured logs
class StructuredLogger:
    """
    Wrapper around loguru logger that provides structured logging capabilities
    """
    def __init__(self, context=None):
        self.context = context or {}
        
    def bind(self, **kwargs):
        """Add context to logger"""
        new_context = {**self.context, **kwargs}
        return StructuredLogger(new_context)
        
    def _log(self, level, message, **kwargs):
        """Internal log method with structured data"""
        # Merge context with kwargs
        data = {**self.context, **kwargs}
        # Convert to JSON string for structured logging
        structured_message = f"{message} {json.dumps(data)}"
        getattr(logger, level)(structured_message)
        
    def debug(self, message, **kwargs):
        self._log("debug", message, **kwargs)
        
    def info(self, message, **kwargs):
        self._log("info", message, **kwargs)
        
    def warning(self, message, **kwargs):
        self._log("warning", message, **kwargs)
        
    def error(self, message, **kwargs):
        self._log("error", message, **kwargs)
        
    def critical(self, message, **kwargs):
        self._log("critical", message, **kwargs)
        
    def exception(self, message, **kwargs):
        """Log exception with traceback"""
        exc_info = kwargs.pop("exc_info", True)
        self._log("exception", message, exc_info=exc_info, **kwargs)

# Export singleton instance
structured_logger = StructuredLogger()

# Compatibility function for modules that import get_logger
def get_logger(name=None):
    """
    Compatibility function that returns the structured logger.
    This provides backward compatibility for modules importing get_logger.
    """
    return structured_logger
