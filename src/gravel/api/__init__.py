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

from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from starlette import status as status_codes

from gravel.controllers.auth import JWT, JWTDenyList, JWTMgr, UserMgr, UserModel
from gravel.controllers.deployment.mgr import DeploymentMgr


class JWTAuthSchema(OAuth2PasswordBearer):
    def __init__(self):
        super().__init__(tokenUrl="auth/login")

    async def __call__(self, request: Request) -> Optional[JWT]:  # type: ignore[override]
        state = request.app.state

        # Refuse authenticating while node is not deployed.
        dep: DeploymentMgr = state.deployment
        if not dep.deployed:
            raise HTTPException(
                status_code=status_codes.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method not available before deployment.",
            )

        if (
            state.nodemgr is None
            or state.gstate is None
            or not state.nodemgr.ready
        ):
            raise HTTPException(
                status_code=status_codes.HTTP_425_TOO_EARLY,
                detail="Node is not ready yet.",
            )

        # Get and validate the token.
        token = JWTMgr.get_token_from_cookie(request)
        if token is None:
            # Fallback: Try to get it from the headers.
            token = await super().__call__(request)
        if not token:
            raise HTTPException(
                status_code=400, detail="Token missing from request"
            )
        # Decode token and do the following checks:
        try:
            jwt_mgr = JWTMgr(state.gstate.config.options.auth)
            raw_token: JWT = jwt_mgr.get_raw_access_token(token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
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


class NodeStateGateKeeper:
    def __init__(self):
        pass

    def __call__(self, request: Request) -> None:
        dep: DeploymentMgr = request.app.state.deployment
        if not dep.installed:
            raise HTTPException(
                status_code=status_codes.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Node hasn't been installed.",
            )


jwt_auth_scheme = JWTAuthSchema()
install_gate = NodeStateGateKeeper()
