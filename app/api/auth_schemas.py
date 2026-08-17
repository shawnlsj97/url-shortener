from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CredentialsRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class AuthenticatedUserResponse(BaseModel):
    email: EmailStr
