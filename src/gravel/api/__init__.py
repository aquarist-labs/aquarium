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

from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from gravel.controllers.auth import JWTDenyList, JWTMgr, JWT, UserMgr, UserModel


class JWTAuthSchema(OAuth2PasswordBearer):
    def __init__(self):
        super().__init__(tokenUrl="auth/login")

    async def __call__(self, request: Request) -> Optional[JWT]:  # type: ignore[override]
        state = request.app.state
        # Disable authentication as long as the node is not ready.
        if not state.nodemgr.deployment_state.ready:
            return None
        # Get and validate the token.
        token = JWTMgr.get_token_from_cookie(request)
        if token is None:
            # Fallback: Try to get it from the headers.
            token = await super().__call__(request)
        # Decode token and do the following checks:
        jwt_mgr = JWTMgr(state.gstate.config.options.auth)
        raw_token: JWT = jwt_mgr.get_raw_access_token(token)
        # - Is the token revoked?
        deny_list = JWTDenyList(state.gstate.store)
        await deny_list.load()
        if deny_list.includes(raw_token):
            raise HTTPException(
                status_code=401, detail="Token has been revoked"
            )
        # - Does the user exist?
        user_mgr = UserMgr(state.gstate.store)
        user: Optional[UserModel] = await user_mgr.get(str(raw_token.sub))
        if user is None:
            raise HTTPException(status_code=401, detail="User does not exist")
        # - Is user disabled?
        if user.disabled:
            raise HTTPException(status_code=401, detail="User is disabled")
        return raw_token


jwt_auth_scheme = JWTAuthSchema()
