"""Phone numbers resource — registration, verification, business profile, settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ..types import BusinessProfileResponse

if TYPE_CHECKING:
    from ..client import WhatsAppClient


# ── Input models ─────────────────────────────────────────────────────


class RequestCodeInput(BaseModel):
    phone_number_id: str
    code_method: str  # "SMS" | "VOICE"
    language: str = Field(min_length=2)


class VerifyCodeInput(BaseModel):
    phone_number_id: str
    code: str


class RegisterInput(BaseModel):
    phone_number_id: str
    pin: str
    data_localization_region: str | None = None


class DeregisterInput(BaseModel):
    phone_number_id: str


class UpdateBusinessProfileInput(BaseModel):
    phone_number_id: str
    about: str | None = None
    address: str | None = None
    description: str | None = None
    email: str | None = None
    profile_picture_url: str | None = None
    websites: list[str] | None = None
    vertical: str | None = None


# ── Sub-resources ────────────────────────────────────────────────────


class BusinessProfileSubResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

    async def get(self, phone_number_id: str) -> BusinessProfileResponse:
        resp = await self._client.get(
            f"{phone_number_id}/whatsapp_business_profile",
            params={
                "fields": "about,address,description,email,"
                "profile_picture_url,websites,vertical"
            },
        )
        return BusinessProfileResponse.model_validate(resp)

    async def update(self, input: UpdateBusinessProfileInput) -> dict[str, Any]:
        body = input.model_dump(exclude={"phone_number_id"}, exclude_none=True)
        body["messaging_product"] = "whatsapp"
        return await self._client.post(
            f"{input.phone_number_id}/whatsapp_business_profile",
            json=body,
        )


class SettingsSubResource:
    __slots__ = ("_client",)

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client

    async def get(self, phone_number_id: str) -> dict[str, Any]:
        return await self._client.get(f"{phone_number_id}/settings")

    async def update(self, phone_number_id: str, **settings: Any) -> dict[str, Any]:
        return await self._client.post(f"{phone_number_id}/settings", json=settings)


# ── Main resource ────────────────────────────────────────────────────


class PhoneNumbersResource:
    __slots__ = ("_client", "business_profile", "settings")

    def __init__(self, client: WhatsAppClient) -> None:
        self._client = client
        self.business_profile = BusinessProfileSubResource(client)
        self.settings = SettingsSubResource(client)

    async def request_code(self, input: RequestCodeInput) -> dict[str, Any]:
        return await self._client.post(
            f"{input.phone_number_id}/request_code",
            json={"code_method": input.code_method, "language": input.language},
        )

    async def verify_code(self, input: VerifyCodeInput) -> dict[str, Any]:
        return await self._client.post(
            f"{input.phone_number_id}/verify_code",
            json={"code": input.code},
        )

    async def register(self, input: RegisterInput) -> dict[str, Any]:
        body: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "pin": input.pin,
        }
        if input.data_localization_region:
            body["data_localization_region"] = input.data_localization_region
        return await self._client.post(f"{input.phone_number_id}/register", json=body)

    async def deregister(self, input: DeregisterInput) -> dict[str, Any]:
        return await self._client.post(f"{input.phone_number_id}/deregister", json={})
