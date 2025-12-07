from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.security import create_access_token
from ..core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


# TEMP: hard-coded dev user
DEV_USERNAME = "ross"
DEV_PASSWORD = "trainstream"  # dev only!


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest) -> TokenResponse:
    if not (data.username == DEV_USERNAME and data.password == DEV_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {"sub": data.username},
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return TokenResponse(access_token=token, username=data.username)
