from contextlib import asynccontextmanager

import strawberry
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from strawberry.fastapi import GraphQLRouter

from common.core.db import get_session
from common.core.logger import get_correlation_id, get_logger, setup_logging
from common.core.middleware import RequestLoggingMiddleware
from common.core.rate_limiting import limiter, setup_rate_limiting
from common.core.security import (
    SecurityHeadersMiddleware,
    StrictOriginValidationMiddleware,
)
from common.core.settings import ALLOWED_ORIGINS, ENVIRONMENT, LOG_LEVEL
from common.core.validation import create_error_response, handle_validation_error
from common.domain.resolvers import Mutation, Query

setup_logging(LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(LOG_LEVEL)
    logger = get_logger("startup")
    logger.info("Application starting up", extra={"environment": ENVIRONMENT})
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Help Center Backend",
    description="A production-ready help center backend with GraphQL and REST APIs",
    version="1.0.0",
    lifespan=lifespan,
)

# Security: Strict origin validation (must be before CORS)
app.add_middleware(StrictOriginValidationMiddleware, allowed_origins=ALLOWED_ORIGINS)

# Security: Security headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging + Rate limiting
app.add_middleware(RequestLoggingMiddleware)
setup_rate_limiting(app)

# ------------------------------
# Exception handlers
# ------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = get_correlation_id()
    request_id = getattr(request.state, "request_id", None)
    details = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "value": err.get("input"),
            "code": err["type"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Input validation failed",
            "details": details,
            "correlation_id": correlation_id,
            "request_id": request_id,
        },
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    correlation_id = get_correlation_id()
    request_id = getattr(request.state, "request_id", None)
    return create_error_response(
        handle_validation_error(exc, correlation_id, request_id),
        correlation_id,
        request_id,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id()
    request_id = getattr(request.state, "request_id", None)
    return create_error_response(exc, correlation_id, request_id)


# ------------------------------
# GraphQL setup
# ------------------------------

schema = strawberry.Schema(query=Query, mutation=Mutation)


async def get_context():
    return {"get_session": get_session}


graphql_app = GraphQLRouter(
    schema,
    allow_queries_via_get=True,
    context_getter=get_context,
)


@app.options("/graphql")
async def graphql_options():
    return {"message": "OK"}


app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
@limiter.limit("1000/hour")
async def health_check(request: Request):
    return {"status": "healthy", "environment": ENVIRONMENT}
