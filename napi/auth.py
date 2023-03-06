import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from napi.logger import core_logger as logger

auth_file = Path("napi/auth.yml")
auth_database: dict[str, Any] = {}


def init_auth_database():
    global auth_database

    if not auth_file.exists():
        logger.critical("Auth file does not exist")
        sys.exit(1)

    with auth_file.open() as f:
        auth_database = yaml.safe_load(f)


@dataclass
class User:
    name: str
    permissions: list[str]


def _get_user(token: str) -> User | None:
    token_hash = hashlib.sha256(token.encode("UTF-8")).hexdigest()
    user = auth_database["users"].get(token_hash)

    if user is None:
        return None

    return User(**user)


def get_user_from_request(request: Request) -> User | None:
    authorization: str = request.headers.get("Authorization")
    _, token = get_authorization_scheme_param(authorization)

    return _get_user(token)


class Bearer(HTTPBearer):
    def __init__(self, app_name: str, auto_error: bool = True) -> None:
        self.app_name = app_name
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> User:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        user = _get_user(credentials.credentials)
        if user is None:
            logger.critical(f"{request.client.host} tried to access {self.app_name}")

            raise HTTPException(status_code=403, detail="Invalid token or expired token")

        if self.app_name not in user.permissions:
            logger.critical(
                f"{user.name} authenticated " f"but has no permissions to access {self.app_name}"
            )

            raise HTTPException(
                status_code=403, detail="You are not allowed to work with this endpoint"
            )

        logger.debug(
            f"User {user.name} ({request.client.host}) is authenticated "
            f"to work with {self.app_name}"
        )

        return user
