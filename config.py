"""Configuration settings for the application."""

from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
DB_NAME = "todos.db"
DB_PATH = str(BASE_DIR / DB_NAME)

# Default project name for new tasks
DEFAULT_PROJECT = "Inbox"

# Date format for due dates
DATE_FORMAT = "%Y-%m-%d"

# Task validation limits
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500


class Priority(str):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def values(cls):
        return [cls.LOW, cls.MEDIUM, cls.HIGH]


# Database schema versions
class SchemaVersion:
    CURRENT = 1
    MIN_SUPPORTED = 1
