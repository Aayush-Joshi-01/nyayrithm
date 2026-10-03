from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class NyayrithmError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(NyayrithmError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} '{id}' not found", "NOT_FOUND")
        self.resource = resource
        self.id = id


class ValidationError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class ConflictError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")


class ForbiddenError(NyayrithmError):
    """The caller is known but not allowed to do this."""

    def __init__(self, message: str, code: str = "FORBIDDEN"):
        super().__init__(message, code)


class NoOrganizationError(ForbiddenError):
    def __init__(self) -> None:
        super().__init__(
            "You are not a member of any firm. Ask your firm administrator for an invitation.",
            "NO_ORGANIZATION",
        )


class OrgSuspendedError(ForbiddenError):
    def __init__(self) -> None:
        super().__init__("This firm's access is suspended. Contact your administrator.",
                         "ORG_SUSPENDED")


class EntitlementError(NyayrithmError):
    """The firm's subscription does not allow this (HTTP 402)."""


class SubscriptionInactiveError(EntitlementError):
    def __init__(self, message: str = "The firm's subscription is not active.") -> None:
        super().__init__(message, "SUBSCRIPTION_INACTIVE")


class SeatLimitError(EntitlementError):
    def __init__(self, seats: int) -> None:
        super().__init__(f"All {seats} seats on the firm's plan are in use.", "SEAT_LIMIT")


class QuotaExceededError(EntitlementError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "QUOTA_EXCEEDED")


class GoneError(NyayrithmError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "GONE")


class PayloadTooLargeError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "PAYLOAD_TOO_LARGE")


class StorageError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class AgentError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "AGENT_ERROR")


class SimulationError(NyayrithmError):
    def __init__(self, message: str):
        super().__init__(message, "SIMULATION_ERROR")


class LLMError(NyayrithmError):
    def __init__(self, message: str, provider: str):
        super().__init__(message, "LLM_ERROR")
        self.provider = provider


async def nyayrithm_exception_handler(request: Request, exc: NyayrithmError) -> JSONResponse:
    status_map = {
        "NOT_FOUND": 404,
        "VALIDATION_ERROR": 422,
        "CONFLICT": 409,
        "FORBIDDEN": 403,
        "NO_ORGANIZATION": 403,
        "ORG_SUSPENDED": 403,
        "INVITE_EMAIL_MISMATCH": 403,
        "SUBSCRIPTION_INACTIVE": 402,
        "SEAT_LIMIT": 402,
        "QUOTA_EXCEEDED": 402,
        "GONE": 410,
        "KEYCLOAK_UNAVAILABLE": 503,
        "PAYLOAD_TOO_LARGE": 413,
        "STORAGE_ERROR": 500,
        "AGENT_ERROR": 500,
        "SIMULATION_ERROR": 500,
        "LLM_ERROR": 502,
        "INTERNAL_ERROR": 500,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 500),
        content={"error": exc.code, "message": exc.message, "detail": exc.message},
    )
