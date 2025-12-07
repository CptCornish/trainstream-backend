import datetime as dt
from typing import Any, Dict

import jwt  # from pyjwt

from .config import settings


def create_access_token(data: Dict[str, Any], expires_minutes: int = 60) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=expires_minutes)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
