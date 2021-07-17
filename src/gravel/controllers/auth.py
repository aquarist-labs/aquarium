# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import bcrypt
import json
import jwt
import uuid

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, NamedTuple

from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel, Field

from gravel.controllers.config import AuthOptionsModel
from gravel.controllers.kv import KV


class UserModel(BaseModel):
    username: str = Field("", title="The user name")
    password: str = Field("", title="The password")
    full_name: str = Field("", title="The full name of the user")
    disabled: bool = Field(False, title="Is the user disabled?")

    def hash_password(self) -> None:
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(
            self.password.encode("utf8"), salt
        ).decode("utf8")

    def verify_password(self, password) -> bool:
        result = bcrypt.checkpw(
            password.encode("utf8"), self.password.encode("utf8")
        )
        return result


class UserMgr:
    def __init__(self, store: KV):
        self._store: KV = store

    async def enumerate(self) -> List[UserModel]:
        values = await self._store.get_prefix("/auth/user/")
        return [UserModel.parse_raw(value) for value in values]

    async def exists(self, username: str) -> bool:
        user = await self.get(username)
        return user is not None

    async def get(self, username: str) -> Optional[UserModel]:
        value: Optional[str] = await self._store.get(f"/auth/user/{username}")
        if value is None:
            return None
        user = UserModel.parse_raw(value)
        return user

    async def put(self, user: UserModel) -> None:
        await self._store.put(f"/auth/user/{user.username}", user.json())

    async def remove(self, username: str) -> None:
        await self._store.rm(f"/auth/user/{username}")

    async def authenticate(self, username: str, password: str) -> bool:
        user: Optional[UserModel] = await self.get(username)
        if user is None:
            return False
        if user.disabled:
            return False
        return user.verify_password(password)


class JWT(NamedTuple):
    iss: str  # Issuer
    sub: Union[str, int]  # Subject
    iat: int  # Issued at
    nbf: int  # Not before
    exp: int  # Expiration time
    jti: str  # JWT ID


class JWTMgr:
    JWT_ISSUER = "Aquarium"
    JWT_ALGORITHM = "HS256"
    COOKIE_KEY = "access_token"

    def __init__(self, config: AuthOptionsModel):
        self._config: AuthOptionsModel = config

    def create_access_token(self, subject: Union[str, int]) -> str:
        now = int(datetime.now(timezone.utc).timestamp())
        payload = JWT(
            iss=self.JWT_ISSUER,
            sub=subject,
            iat=now,
            nbf=now,
            exp=now + self._config.jwt_ttl,
            jti=str(uuid.uuid4()),
        )._asdict()
        encoded_token = jwt.encode(
            payload, self._config.jwt_secret, algorithm=self.JWT_ALGORITHM
        )
        return encoded_token

    def get_raw_access_token(self, token, verify=True) -> JWT:
        options = {}
        if not verify:
            options = {"verify_signature": False}
        raw_token = jwt.decode(
            token,
            self._config.jwt_secret,
            algorithms=[self.JWT_ALGORITHM],
            options=options,
        )
        return JWT(**raw_token)

    @staticmethod
    def set_token_cookie(response: Response, token: str) -> None:
        response.set_cookie(
            key=JWTMgr.COOKIE_KEY,
            value=f"Bearer {token}",
            httponly=True,
            samesite="strict",
        )

    @staticmethod
    def get_token_from_cookie(request: Request) -> Optional[str]:
        value: Optional[str] = request.cookies.get(JWTMgr.COOKIE_KEY)
        if value is None:
            return None
        scheme, token = get_authorization_scheme_param(value)
        if scheme.lower() == "bearer":
            return token
        return None


class JWTDenyList:
    """
    This list contains JWT tokens that are not allowed to use anymore.
    E.g. a token is added when a user logs out of the UI. The list will
    automatically remove expired tokens.
    """

    def __init__(self, store: KV):
        self._store: KV = store
        self._jti_dict: Dict[str, int] = {}

    def _cleanup(self, now: int) -> None:
        self._jti_dict = {
            jti: exp for jti, exp in self._jti_dict.items() if exp > now
        }

    async def load(self) -> None:
        self._jti_dict = {}
        value = await self._store.get("/auth/jwt_deny_list")
        if value is not None:
            self._jti_dict = json.loads(value)
            now = int(datetime.now(timezone.utc).timestamp())
            self._cleanup(now)

    async def save(self) -> None:
        await self._store.put("/auth/jwt_deny_list", json.dumps(self._jti_dict))

    def add(self, token: JWT) -> None:
        self._jti_dict[token.jti] = token.exp

    def includes(self, token: JWT) -> bool:
        return token.jti in self._jti_dict
