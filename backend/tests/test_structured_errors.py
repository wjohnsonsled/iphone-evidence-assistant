from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import ApiError, ErrorCategory, add_exception_handlers


def app() -> FastAPI:
    instance = FastAPI()
    add_exception_handlers(instance)

    @instance.get("/application")
    def application_error():
        raise ApiError(409, "synthetic_conflict", "A synthetic conflict occurred.")

    @instance.get("/validated")
    def validated(value: int):
        return {"value": value}

    @instance.get("/unexpected")
    def unexpected():
        raise RuntimeError("secret synthetic exception content")

    return instance


@pytest.mark.parametrize(
    "arguments",
    [
        (200, "bad_code", "message"),
        (400, "Bad-Code", "message"),
        (400, "ok_code", " "),
    ],
)
def test_api_error_rejects_invalid_contract(arguments):
    with pytest.raises(ValueError):
        ApiError(*arguments)


def test_application_error_uses_stable_safe_envelope():
    response = TestClient(app()).get("/application")
    assert response.status_code == 409
    error = response.json()["error"]
    assert error | {
        "category": "CONFLICT",
        "code": "synthetic_conflict",
        "message": "A synthetic conflict occurred.",
        "retryable": False,
    } == error
    UUID(error["request_id"])


def test_validation_error_does_not_echo_input_or_internals():
    response = TestClient(app()).get("/validated", params={"value": "private-input"})
    assert response.status_code == 422
    rendered = response.text
    assert "private-input" not in rendered
    assert "integer_parsing" not in rendered
    assert response.json()["error"]["code"] == "request_validation_failed"


def test_missing_route_uses_common_envelope():
    response = TestClient(app()).get("/missing")
    error = response.json()["error"]
    assert response.status_code == 404
    assert error["category"] == ErrorCategory.NOT_FOUND.value
    assert error["code"] == "route_not_found"
    UUID(error["request_id"])


def test_unexpected_exception_content_is_hidden():
    with TestClient(app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected")
    assert response.status_code == 500
    assert "secret synthetic exception content" not in response.text
    assert response.json()["error"]["code"] == "internal_server_error"
