"""
Structured JSON logging utility per constitution
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict
import traceback


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging

    Outputs logs in JSON format for easier parsing and analysis
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON string representation of log record
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup structured JSON logging for the application

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("ddms")
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "ddms") -> logging.Logger:
    """
    Get a logger instance with the given name

    Args:
        name: Logger name (defaults to "ddms")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create default logger instance
logger = setup_logging()
