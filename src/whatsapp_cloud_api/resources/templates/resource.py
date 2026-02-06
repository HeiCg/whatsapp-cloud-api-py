"""Templates resource — list, create, delete message templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...types import TemplateCreateResponse, TemplateDeleteResponse, TemplateListResponse
from .models import TemplateCreateInput, TemplateDeleteInput, TemplateListInput

if TYPE_CHECKING:
    from ...client import WhatsAppClient


class TemplatesResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

    async def list(self, input: TemplateListInput) -> TemplateListResponse:
        params: dict[str, Any] = {}
        if input.limit is not None:
            params["limit"] = input.limit
        if input.before:
            params["before"] = input.before
        if input.after:
            params["after"] = input.after
        if input.order:
            params["order"] = input.order
        if input.status:
            params["status"] = input.status
        if input.name:
            params["name"] = input.name
        if input.category:
            params["category"] = input.category
        if input.language:
            params["language"] = input.language

        resp = await self._client.get(
            f"{input.business_account_id}/message_templates",
            params=params or None,
        )
        return TemplateListResponse.model_validate(resp)

    async def create(self, input: TemplateCreateInput) -> TemplateCreateResponse:
        body: dict[str, Any] = {
            "name": input.name,
            "language": input.language,
            "category": input.category,
            "components": input.components,
        }
        if input.parameter_format:
            body["parameter_format"] = input.parameter_format
        if input.allow_category_change is not None:
            body["allow_category_change"] = input.allow_category_change

        resp = await self._client.post(
            f"{input.business_account_id}/message_templates",
            json=body,
        )
        return TemplateCreateResponse.model_validate(resp)

    async def delete(self, input: TemplateDeleteInput) -> TemplateDeleteResponse:
        params: dict[str, Any] = {"name": input.name}
        if input.language:
            params["hsm_id"] = input.language

        resp = await self._client.delete(
            f"{input.business_account_id}/message_templates",
            params=params,
        )
        return TemplateDeleteResponse.model_validate(resp)
