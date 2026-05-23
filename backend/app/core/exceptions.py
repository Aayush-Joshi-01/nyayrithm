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
        "STORAGE_ERROR": 500,
        "AGENT_ERROR": 500,
        "SIMULATION_ERROR": 500,
        "LLM_ERROR": 502,
        "INTERNAL_ERROR": 500,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 500),
        content={"error": exc.code, "message": exc.message},
    )
