"""
Application settings and configuration.

Loads environment variables and provides centralized configuration
for database, logging, CORS, and other application settings.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

if not os.getenv("DOCKER_ENV"):
    load_dotenv(BASE_DIR / ".env.local")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if "pytest" in sys.modules:
    ENVIRONMENT = "test"

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL_ASYNC = os.getenv("DATABASE_URL_ASYNC")
NEON_DB_CONNECTION_STRING = os.getenv("NEON_DB_CONNECTION_STRING")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_DATABASE_URL_ASYNC = os.getenv("TEST_DATABASE_URL_ASYNC")

if ENVIRONMENT == "test":
    if not TEST_DATABASE_URL_ASYNC:
        # Use a default test database URL if not provided
        DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    else:
        DATABASE_URL = TEST_DATABASE_URL_ASYNC
elif NEON_DB_CONNECTION_STRING:
    # Production: Use Neon DB connection string
    DATABASE_URL_ASYNC = NEON_DB_CONNECTION_STRING
    # Convert sync URL to async format if needed
    if DATABASE_URL_ASYNC.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_ASYNC.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL = DATABASE_URL_ASYNC
elif not DATABASE_URL_ASYNC:
    raise ValueError("DATABASE_URL_ASYNC or NEON_DB_CONNECTION_STRING must be set")
else:
    # Local development: Use DATABASE_URL_ASYNC directly
    # Convert sync URL to async format if needed
    if DATABASE_URL_ASYNC.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_ASYNC.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL = DATABASE_URL_ASYNC

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set")

# Alembic uses this for migrations (convert async URL to sync)
ACTIVE_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
EDITOR_KEY = os.getenv("EDITOR_KEY", os.getenv("DEV_EDITOR_KEY", "dev-editor-key"))

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

REDIS_URL = os.getenv("REDIS_URL")
