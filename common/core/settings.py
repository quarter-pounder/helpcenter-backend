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

# Log environment variable presence (without sensitive data)
# Use print for early debugging since logging may not be configured yet
print(
    f"[settings] Database config - ENVIRONMENT: {ENVIRONMENT}, "
    f"NEON_DB_CONNECTION_STRING set: {bool(NEON_DB_CONNECTION_STRING)}, "
    f"DATABASE_URL_ASYNC set: {bool(DATABASE_URL_ASYNC)}"
)

if ENVIRONMENT == "test":
    if not TEST_DATABASE_URL_ASYNC:
        # Use a default test database URL if not provided
        DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    else:
        DATABASE_URL = TEST_DATABASE_URL_ASYNC
elif NEON_DB_CONNECTION_STRING:
    # Production: Use Neon DB connection string
    DATABASE_URL_ASYNC = NEON_DB_CONNECTION_STRING

    # Ensure Cloud SQL is not used
    if "/cloudsql/" in DATABASE_URL_ASYNC or "unix:" in DATABASE_URL_ASYNC:
        error_msg = (
            "NEON_DB_CONNECTION_STRING appears to be a Cloud SQL connection. "
            "Use Neon DB connection string instead."
        )
        print(f"[settings] ERROR: {error_msg}")
        raise ValueError(error_msg)

    # Convert sync URL to async format if needed
    if DATABASE_URL_ASYNC.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_ASYNC.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL_ASYNC.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL_ASYNC
    else:
        # If it doesn't start with postgresql://, assume it needs the async driver
        if not DATABASE_URL_ASYNC.startswith("postgresql"):
            error_msg = (
                f"Invalid NEON_DB_CONNECTION_STRING format. "
                f"Expected postgresql:// or postgresql+asyncpg://, "
                f"got: {DATABASE_URL_ASYNC[:50]}..."
            )
            print(f"[settings] ERROR: {error_msg}")
            raise ValueError(error_msg)
        DATABASE_URL = DATABASE_URL_ASYNC

    # Log connection string (masked for security)
    if DATABASE_URL:
        masked_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "***"
        print(f"[settings] Using NEON_DB_CONNECTION_STRING, connecting to: {masked_url}")
        conn_format = DATABASE_URL.split("://")[0] if "://" in DATABASE_URL else "unknown"
        print(f"[settings] Connection string format: {conn_format}")

        # Verify connection string structure
        if "@" in DATABASE_URL:
            user_pass_part = DATABASE_URL.split("@")[0]
            if "://" in user_pass_part:
                user_pass = user_pass_part.split("://")[1]
                if ":" in user_pass:
                    username, password = user_pass.split(":", 1)
                    print(f"[settings] Username extracted: {username}")
                    print(f"[settings] Password length: {len(password)} characters")
                    # Check for common issues
                    if password.strip() != password:
                        print("[settings] WARNING: Password has leading/trailing whitespace!")
                    if not password:
                        print("[settings] ERROR: Password is empty!")
elif not DATABASE_URL_ASYNC:
    error_msg = "DATABASE_URL_ASYNC or NEON_DB_CONNECTION_STRING must be set"
    print(f"[settings] ERROR: {error_msg}")
    raise ValueError(error_msg)
else:
    # Local development: Use DATABASE_URL_ASYNC directly
    # Convert sync URL to async format if needed
    if DATABASE_URL_ASYNC.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_ASYNC.replace("postgresql://", "postgresql+asyncpg://")
    else:
        DATABASE_URL = DATABASE_URL_ASYNC

if not DATABASE_URL:
    error_msg = "DATABASE_URL must be set"
    print(f"[settings] ERROR: {error_msg}")
    raise ValueError(error_msg)

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
