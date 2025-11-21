# Help Center Backend

A help center backend with clean, separated architecture, built with FastAPI, GraphQL, and PostgreSQL. CI/CD pipeline with Docker, GitHub Actions, Cloud Run deployment, and UV dependency management.

**Complete Refactoring:**
- **Clean Structure**: Migrated from `helpcenter-*` to clean `common/`, `graphql_api/`, `editor_api/`
- **UV Integration**: Dependency management with `pyproject.toml` and lock files
- **Test Optimization**: Two testing strategy (fast unit tests + comprehensive integration tests)
- **CI/CD**: GitHub Actions with path-based triggering and UV caching
- **Code Quality**: Automated linting, formatting, and import sorting
- **Production Ready**: All tests passing with proper alembic migrations

## Architecture

### Project Structure

```
helpcenter-backend/
├── common/                   # Shared components
│   ├── core/                 # Database, logging, settings, validation
│   ├── domain/               # Models, DTOs, resolvers, REST endpoints
│   ├── services/             # Business logic
│   ├── repositories/         # Data access layer
│   ├── utils/                # Utility functions
│   └── pyproject.toml        # Common package dependencies
├── graphql_api/              # Public GraphQL API (Cloud Run)
│   ├── main.py               # FastAPI app with GraphQL
│   ├── migrations/           # Database migrations
│   ├── pyproject.toml        # GraphQL API dependencies
│   └── Dockerfile.uv         # UV-optimized container
├── editor_api/               # Private REST API (Cloud Function)
│   ├── main.py               # FastAPI app with REST endpoints
│   ├── pyproject.toml        # Editor API dependencies
│   └── Dockerfile.uv         # UV-optimized container
├── tests/                    # Test suite
│   ├── unit/                 # Fast unit tests (isolated, no database)
│   └── integration/          # Integration tests (with database)
├── scripts/                  # Utility scripts
├── cloudbuild/               # Google Cloud Build configurations
├── .github/                  # GitHub Actions workflows and actions
├── pyproject.toml            # Root project configuration with UV
├── uv.lock                   # UV dependency lock file
├── .python-version           # Python version specification
└── docker-compose.yaml       # Development environment
```

### Services

#### 1. GraphQL API (Public)
- **Purpose**: Public API for frontend consumption
- **Deployment**: Google Cloud Run
- **Endpoints**: `/graphql`, `/health`
- **Authentication**: None (public)

#### 2. Editor API (Private)
- **Purpose**: Content management operations
- **Deployment**: Google Cloud Function
- **Endpoints**: `/dev-editor/*`
- **Authentication**: API key (`x-dev-editor-key` header)

#### 3. Common Package
- **Purpose**: Shared code between services
- **Contains**: Models, DTOs, services, repositories, core utilities
- **Usage**: Imported by both APIs

## Technology Stack

- **Backend**: FastAPI + GraphQL (Strawberry)
- **Database**: Neon DB (PostgreSQL) with connection pooling
- **Cache**: Redis for rate limiting and session management
- **Media Storage**: Google Cloud Storage
- **Deployment**: Google Cloud Run + Cloud Functions with automated CI/CD
- **CI/CD**: GitHub Actions with environment-specific deployments and UV setup
- **Dependency Management**: UV (fast, modern Python package manager with lock files)
- **Testing**: pytest with proper unit/integration test separation
- **Code Quality**: flake8, black, autoflake, isort with automated fixing

## Features

- **GraphQL API**: Type-safe queries and mutations with Strawberry
- **REST API**: Developer editor endpoints for content management
- **Rich Text Support**: JSON-based content blocks for guides
- **Media Management**: Guide-coupled media with file upload and GCS integration
- **Rate Limiting**: Redis-based rate limiting with different limits per endpoint
- **Structured Logging**: JSON logs with correlation IDs and request tracking
- **Input Validation**: Comprehensive Pydantic validation with custom validators
- **Test Coverage**: Full test suite with async support and database isolation
- **Docker Support**: Multi-stage builds for development and production

## Quick Start

Ensure Docker Desktop or Colima is running.

### Prerequisites

- Python 3.11+
- Docker
- Neon DB account
- Google Cloud account

### 1. Setup

```bash
git clone <repo>
cd helpcenter-backend
cp env.example .env.local
# Edit .env.local with actual values
```

### 2. Configure Environment

The `env.example` file contains all required environment variables with placeholder values. Copy it to `.env.local` and update with actual values:

- **Database**: Set Neon DB connection details
- **Redis**: For rate limiting (use `redis://redis:6379` for local development)
- **Google Cloud**: Set GCS bucket and service accounts
- **Security**: Generate strong secret keys
- **CORS**: Add frontend domains

### 3. Run with Docker

```bash
# Start development environment
make dev

# Run tests
make test

# Run quick tests (no cleanup)
make test-quick
```

### 4. UV

For local development with UV:

```bash
# Setup UV (one-time)
make uv-setup

# Run GraphQL API with UV
make uv-run

# Add dependencies
make uv-add pkg=requests

# Update lock file
make uv-lock
```

## Development

### Available Commands

```bash
make help              # Show all commands
make dev               # Start development environment
make dev-stop          # Stop development environment
make test              # Run all tests (unit + integration)
make test-unit         # Run unit tests (fast, no database)
make test-integration  # Run integration tests (with database)
make test-common       # Run common package unit tests only
make test-graphql      # Run GraphQL API integration tests only
make test-editor       # Run Editor API integration tests only
make test-quick        # Run tests without cleanup
make migrate           # Run database migrations
make build             # Build Docker images
make build-prod        # Build production Docker image
make logs              # View logs
make shell             # Open container shell
make health            # Check API health
make lint              # Run code linting
make format            # Format code with black
make fix-lint          # Fix linting issues automatically

# UV commands
make uv-setup          # Initial UV setup
make uv-install        # Install dependencies with UV
make uv-run            # Run GraphQL API with UV
make uv-add            # Add new dependency
make uv-remove         # Remove dependency
make uv-lock           # Update lock file
make uv-sync           # Sync dependencies
```

### Production Safety

The Makefile includes production safety checks that prevent certain commands from running in production environments:

- **Test-only targets**: `test`, `test-quick`, `ci-test` - Always use test databases and are blocked in production
- **Development-only targets**: `build`, `clean`, `prune`, `logs`, `shell`, `editor`, `db-shell`, `db-list`, `dev-stop`, `lint`, `format` - Blocked in production for security
- **Production targets**: `prod-up`, `prod-down`, `prod-clean`, `prod-migrate` - Specifically designed for production use

### Environment-Specific Usage

```bash
# Development (uses .env.local)
make dev
make test
make build

# Production (requires environment variables to be set)
ENVIRONMENT=production make prod-up
ENVIRONMENT=production make prod-migrate
```

## API Endpoints

### GraphQL API (Public)

- `POST /graphql` - GraphQL endpoint with rate limiting
  - **Queries**:
    - `categories` - List all categories
    - `category(slug)` - Get category by slug
    - `guides(categorySlug?)` - List guides (optionally filtered by category)
    - `guide(slug)` - Get guide by slug with media
  - **Mutations**:
    - `submitFeedback` - Submit user feedback

**Note**: Media is accessed through guide queries. Guides include a `media` field that returns associated media items.

### REST API (Editor - Private)

**Authentication**: Requires `x-editor-key` header

#### Categories
- `POST /editor/categories` - Create category
- `GET /editor/categories` - List categories
- `GET /editor/categories/{id}` - Get category by ID
- `PUT /editor/categories/{id}` - Update category
- `DELETE /editor/categories/{id}` - Delete category

#### Guides
- `POST /editor/guides` - Create guide (supports `media_ids` field)
- `GET /editor/guides` - List guides
- `GET /editor/guides/{id}` - Get guide by ID
- `GET /editor/guides/slug/{slug}` - Get guide by slug
- `PUT /editor/guides/{id}` - Update guide (supports `media_ids` field)
- `DELETE /editor/guides/{id}` - Delete guide

#### Media (Guide-Coupled)
- `POST /editor/guides/{guide_id}/media/upload` - Upload media to guide
- `GET /editor/guides/{guide_id}/media` - List media for guide
- `DELETE /editor/guides/{guide_id}/media/{media_id}` - Delete media from guide

**Note**: All media operations are coupled with guides. Media cannot be created or accessed independently.

#### Feedback
- `GET /editor/feedback` - List all feedback
- `GET /editor/feedback/{id}` - Get feedback by ID
- `DELETE /editor/feedback/{id}` - Delete feedback

**Note**: Feedback can only be created via GraphQL mutation (public), managed via REST (private).

## Testing

The project uses a two-tier testing strategy for optimal performance and reliability:

### Unit Tests (Fast, Isolated)
```bash
# Run all unit tests (no database required)
make test-unit

# Run specific unit test
make test-common

```

### Integration Tests (Database Required)
```bash
# Run all integration tests (with database)
make test-integration

# Run specific API integration tests
make test-graphql      # GraphQL API tests
make test-editor       # Editor API tests

# Run full test suite (unit + integration)
make test

# Quick tests without cleanup (faster for development)
make test-quick
```

### Test Structure
```
tests/
├── unit/                   # Fast unit tests
│   └── common/core/        # Mock-based validation tests
└── integration/            # Database-required tests
    ├── graphql_api/        # GraphQL endpoint tests
    ├── editor_api/         # REST API endpoint tests
    └── test_integration.py # Full workflow tests
```

### Test Coverage

- **Categories**: REST and GraphQL endpoints with full CRUD operations
- **Guides**: REST and GraphQL endpoints with rich text and media associations
- **Media**: Guide-coupled file upload, listing, and deletion
- **GraphQL**: Query and mutation integration tests
- **Health**: Health check endpoint verification
- **Rate Limiting**: Rate limit enforcement across all endpoints
- **Database**: Test isolation with proper cleanup and transaction management
- **Validation**: Comprehensive input validation tests

## Deployment

### Automated CI/CD

The project includes a CI/CD pipeline with GitHub Actions and UV optimization:

1. **Smart Change Detection**: Only runs tests for changed components
2. **Parallel Testing**: Separate jobs for common, GraphQL API, Editor API, and integration tests
3. **UV Setup**: Reusable composite action for consistent dependency management
4. **Security Scanning**: Bandit and Trivy vulnerability scanning with SARIF upload
5. **Hybrid Deployment**: GitHub Actions for testing, Cloud Build for deployment (optional)
6. **Environment-Specific**: Staging (develop branch) and production (main branch) deployments

#### CI/CD Features

- **Path-based Triggering**: Only runs when relevant code changes
- **Matrix Strategy**: Parallel execution for faster CI
- **UV Caching**: Optimized dependency installation and caching
- **Test Isolation**: Separate unit tests (fast) and integration tests (comprehensive)
- **Production Safety**: Validates environment variables and prevents dangerous operations

### Manual Deployment

1. **Setup GCS Bucket**:
   ```bash
   gsutil mb gs://helpcenter-bucket
   gsutil iam ch allUsers:objectViewer gs://helpcenter-bucket
   ```

2. **Deploy with Script**:
   ```bash
   ./scripts/deploy-cloud-run.sh production
   ```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEON_DB_HOST` | Neon DB hostname (preferred) | Yes* |
| `NEON_DB_NAME` | Neon DB database name (preferred) | Yes* |
| `NEON_DB_USER` | Neon DB username (preferred) | Yes* |
| `NEON_DB_PASSWORD` | Neon DB password (preferred) | Yes* |
| `NEON_DB_PORT` | Neon DB port (default: 5432) | No |
| `NEON_DB_CONNECTION_STRING` | Neon DB connection string (fallback) | Yes* |
| `DATABASE_URL_ASYNC` | Legacy async connection string | No |
| `REDIS_URL` | Redis connection string | Yes |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket | Yes |
| `HELPCENTER_GCS` | Secret name containing GCS service account key | Yes |
| `SECRET_KEY` | Application secret key | Yes |
| `EDITOR_KEY` | Editor authentication key | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `ENVIRONMENT` | Environment (development, staging, production) | No |

\* Either all individual `NEON_DB_*` variables OR `NEON_DB_CONNECTION_STRING` must be set.

#### Neon Database Permissions

The database user must have CREATE privileges on the `public` schema to run migrations. If you encounter permission errors, connect to your Neon database as the owner/admin user and run:

```sql
GRANT CREATE ON SCHEMA public TO username;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO username;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO username;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO username;
```

Replace `username` with the actual database username (e.g., `gcloud`).

### Google Cloud Service Accounts

The deployment uses three service accounts for security:

| Service Account | Purpose | Required Roles |
|---|---|---|
| `helpcenter-cicd` | GitHub Actions CI/CD | Cloud Build Editor, Storage Admin, Cloud Run Admin, Secret Manager Secret Accessor, Service Account User |
| `helpcenter-runtime` | Cloud Run runtime | Secret Manager Secret Accessor |
| `helpcenter-gcs` | GCS operations | Storage Object Admin |

### GitHub Secrets

Configure these secrets in GitHub repository settings:

| Secret Name | Description | Required |
|---|---|---|
| `HELPCENTER_CICD` | Full JSON key for `helpcenter-cicd` service account | Yes |
| `HELPCENTER_RUNTIME` | Full JSON key for `helpcenter-runtime` service account | Yes |
| `HELPCENTER_GCS` | Full JSON key for `helpcenter-gcs` service account | Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `GOOGLE_CLOUD_REGION` | GCP region (e.g., us-central1) | Yes |
| `NEON_DB_HOST` | Neon DB hostname (preferred) | Yes* |
| `NEON_DB_NAME` | Neon DB database name (preferred) | Yes* |
| `NEON_DB_USER` | Neon DB username (preferred) | Yes* |
| `NEON_DB_PASSWORD` | Neon DB password (preferred) | Yes* |
| `NEON_DB_PORT` | Neon DB port (default: 5432) | No |
| `NEON_DB_CONNECTION_STRING` | Neon DB connection string (fallback) | Yes* |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | Application secret key | Yes |
| `DEV_EDITOR_KEY` | Editor authentication key | Yes |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket name | Yes |
| `HELPCENTER_GCS` | GCS service account JSON key | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins | Yes |
| `POSTGRES_USER` | Database username for CI tests | Yes |
| `POSTGRES_PASSWORD` | Database password for CI tests | Yes |
| `POSTGRES_DB` | Database name for CI tests | Yes |

\* Either all individual `NEON_DB_*` variables OR `NEON_DB_CONNECTION_STRING` must be set.

## UV Dependency Management

This project uses UV for fast, reliable dependency management with separate dependency groups:

### Benefits

- **Fast**: Faster than pip
- **Reliable**: Lock files ensure reproducible builds
- **Modern**: Similar to Maven/pnpm workflows
- **Container-friendly**: Works great in Docker with multi-stage builds
- **CI-optimized**: Better caching and faster builds
- **Group-based**: Separate dev dependencies for linting and testing

### Usage

```bash
# Setup UV (one-time)
make uv-setup

# Install all dependencies (production + dev)
uv sync

# Install only production dependencies
uv sync --no-dev

# Install specific dependency groups
uv sync --group dev

# Add dependency
make uv-add pkg=requests

# Remove dependency
make uv-remove pkg=requests

# Update lock file
make uv-lock

# Run application
make uv-run
```

### Dependency Groups

- **Production**: Core runtime dependencies
- **Dev**: Testing, linting, and development tools (pytest, flake8, black, etc.)

### Docker with UV

The project includes UV-optimized Dockerfiles for builds:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install uv (small Rust binary, <10 MB)
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy lock + metadata only
COPY pyproject.toml uv.lock ./

# Install directly from lockfile (deterministic)
RUN uv sync --frozen --no-dev --no-editable

# Copy rest of app
COPY . .

CMD ["uv", "run", "uvicorn", "graphql-api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Free Tier Limits

- **Neon DB**: 0.5GB storage, 10GB transfer/month
- **Redis**: 30MB memory, 30 connections (Redis Cloud free tier)
- **Google Cloud Storage**: 5GB storage, 1GB transfer/month
- **Google Cloud Run**: 2M requests/month, 400K GB-seconds compute
- **Vercel**: 100GB bandwidth/month

In layman's terms, this stack should cover a deep exploration without a penny.

## Architecture Decisions

- **Separated Services**: Clear separation between public GraphQL API and private Editor API
- **Domain-Driven Design**: Clear separation of concerns with domain logic in `common/`
- **Media Coupling**: Media resources are coupled with guides for simpler architecture and data consistency
- **UV Integration**: Modern dependency management with lock files and dependency groups
- **Test Strategy**: Two-tier approach with fast unit tests and comprehensive integration tests
- **Connection Pooling**: AsyncAdaptedQueuePool for production, NullPool for tests
- **Rate Limiting**: Redis-based with different limits per endpoint type
- **Structured Logging**: JSON logs with correlation IDs for observability
- **Docker-First**: All operations run in containers with UV-optimized builds
- **Production Safety**: Makefile blocks dangerous commands in production environments
- **Environment Validation**: Explicit validation of required environment variables
- **CI/CD Optimization**: Path-based triggering, parallel execution, and smart caching
- **Code Quality**: Automated linting, formatting, and import sorting with `make fix-lint`

## License

MIT — do what you want, break it if you must, fix it if you're feeling generous.
