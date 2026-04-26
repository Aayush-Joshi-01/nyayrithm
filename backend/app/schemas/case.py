from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    description: str = ""
    country: str = Field(..., min_length=2)
    jurisdiction: str = ""
    legal_system: str = "common_law"
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    country: str | None = None
    jurisdiction: str | None = None
    legal_system: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class CaseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    country: str
    jurisdiction: str
    legal_system: str
    status: str
    created_by: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int
    page: int
    size: int
