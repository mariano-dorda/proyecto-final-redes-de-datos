import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config import API_BASIC_PASSWORD, API_BASIC_USER


security = HTTPBasic()


def require_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    is_valid_user = secrets.compare_digest(credentials.username, API_BASIC_USER)
    is_valid_password = secrets.compare_digest(credentials.password, API_BASIC_PASSWORD)
    if not (is_valid_user and is_valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
