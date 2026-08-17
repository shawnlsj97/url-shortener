from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

CUSTOM_ALIAS_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{1,30}[a-z0-9])?$"
RESERVED_CODES = {
    "api",
    "dashboard",
    "docs",
    "expired",
    "healthz",
    "login",
    "not-found",
    "openapi.json",
    "redoc",
    "register",
    "static",
}


class CreateLinkRequest(BaseModel):
    original_url: AnyHttpUrl = Field(max_length=2048)
    custom_alias: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=CUSTOM_ALIAS_PATTERN
    )
    expires_at: datetime | None = None

    @field_validator("custom_alias")
    @classmethod
    def prevent_reserved_aliases(cls, value: str | None) -> str | None:
        if value in RESERVED_CODES:
            raise ValueError("This custom alias is reserved.")
        return value

    @field_validator("expires_at")
    @classmethod
    def require_future_expiry(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value <= datetime.now(UTC)):
            raise ValueError("Expiry must be a future, timezone-aware date and time.")
        return value


class LinkResponse(BaseModel):
    code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: datetime | None


class ManagedLinkResponse(LinkResponse):
    disabled_at: datetime | None
    total_clicks: int
