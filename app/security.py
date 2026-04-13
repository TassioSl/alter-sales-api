import secrets

from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import settings


security = HTTPBasic(auto_error=False)


def require_basic_auth(credentials: HTTPBasicCredentials | None) -> None:
    if settings.disable_inbound_auth:
        return
    if not settings.inbound_api_username or not settings.inbound_api_password:
        return
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais obrigatórias",
            headers={"WWW-Authenticate": "Basic"},
        )

    valid_username = secrets.compare_digest(credentials.username, settings.inbound_api_username)
    valid_password = secrets.compare_digest(credentials.password, settings.inbound_api_password)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
