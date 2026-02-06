"""Pydantic models for template management."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TemplateListInput(BaseModel):
    business_account_id: str
    before: str | None = None
    after: str | None = None
    limit: int | None = None
    order: str | None = None
    status: str | None = None
    name: str | None = None
    category: str | None = None
    language: str | None = None


class TemplateCreateInput(BaseModel):
    business_account_id: str
    name: str
    language: str
    category: str
    parameter_format: str | None = None
    allow_category_change: bool | None = None
    components: list[dict[str, Any]]


class TemplateDeleteInput(BaseModel):
    business_account_id: str
    name: str
    language: str | None = None
