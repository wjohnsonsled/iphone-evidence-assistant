"""Structured API exceptions and handlers."""

from __future__ import annotations

import logging
import re
from enum import Enum
from http import HTTPStatus
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import log_event

logger = logging.getLogger(__name__)
ERROR_CODE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


class ErrorCategory(str, Enum):
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    DEPENDENCY = "DEPENDENCY"
    INTERNAL = "INTERNAL"


class ApiError(Exception):
    """Application error safe to expose through the API."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        category: ErrorCategory | None = None,
        retryable: bool = False,
    ) -> None:
        if status_code < 400 or status_code > 599:
            raise ValueError("API error status must be between 400 and 599")
        if not ERROR_CODE.fullmatch(code):
            raise ValueError("API error code must be stable lower_snake_case")
        if not message.strip():
            raise ValueError("API error message must not be empty")
        self.status_code = status_code
        self.code = code
        self.message = message.strip()
        self.category = category or _category_for_status(status_code)
        self.retryable = retryable
        super().__init__(message)


def _category_for_status(status_code: int) -> ErrorCategory:
    if status_code == 401:
        return ErrorCategory.AUTHENTICATION
    if status_code == 403:
        return ErrorCategory.AUTHORIZATION
    if status_code == 404:
        return ErrorCategory.NOT_FOUND
    if status_code == 409:
        return ErrorCategory.CONFLICT
    if status_code in {413, 429}:
        return ErrorCategory.RESOURCE_LIMIT
    if status_code in {502, 503, 504}:
        return ErrorCategory.DEPENDENCY
    if status_code >= 500:
        return ErrorCategory.INTERNAL
    return ErrorCategory.VALIDATION


def _response(
    *,
    status_code: int,
    category: ErrorCategory,
    code: str,
    message: str,
    request_id: str,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "category": category.value,
                "code": code,
                "message": message,
                "retryable": retryable,
                "request_id": request_id,
            }
        },
    )


def add_exception_handlers(app: FastAPI) -> None:
    """Register API error handlers."""

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        request_id = str(uuid4())
        log_event(
            logger,
            logging.WARNING,
            "api_error",
            request_id=request_id,
            code=exc.code,
            status=exc.status_code,
            path=request.url.path,
        )
        return _response(
            status_code=exc.status_code,
            category=exc.category,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = str(uuid4())
        log_event(
            logger,
            logging.WARNING,
            "request_validation_error",
            request_id=request_id,
            path=request.url.path,
            status=422,
            error_count=len(exc.errors()),
        )
        return _response(
            status_code=422,
            category=ErrorCategory.VALIDATION,
            code="request_validation_failed",
            message="The request did not satisfy the required contract.",
            request_id=request_id,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = str(uuid4())
        status_code = exc.status_code
        try:
            phrase = HTTPStatus(status_code).phrase
        except ValueError:
            phrase = "Request failed"
        log_event(
            logger,
            logging.WARNING,
            "http_error",
            request_id=request_id,
            status=status_code,
            path=request.url.path,
        )
        return _response(
            status_code=status_code,
            category=_category_for_status(status_code),
            code="route_not_found" if status_code == 404 else "http_request_failed",
            message=phrase + ".",
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = str(uuid4())
        log_event(
            logger,
            logging.ERROR,
            "unexpected_error",
            request_id=request_id,
            status=500,
            path=request.url.path,
        )
        return _response(
            status_code=500,
            category=ErrorCategory.INTERNAL,
            code="internal_server_error",
            message="An internal error occurred.",
            request_id=request_id,
        )
