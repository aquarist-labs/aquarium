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

from logging import Logger
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from fastapi import HTTPException, Request, Response, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from gravel.api import jwt_auth_scheme
from gravel.controllers.auth import JWTDenyList, JWTMgr, JWT, UserMgr


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(prefix="/auth", tags=["auth"])


class LoginReplyModel(BaseModel):
    access_token: str = Field(title="The access token")
    token_type: str = Field("bearer")


@router.post("/login", response_model=LoginReplyModel)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> LoginReplyModel:
    user_mgr = UserMgr(request.app.state.gstate.store)
    authenticated = await user_mgr.authenticate(
        form_data.username, form_data.password
    )
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad username or password",
        )
    jwt_mgr = JWTMgr(request.app.state.gstate.config.options.auth)
    access_token = jwt_mgr.create_access_token(subject=form_data.username)
    jwt_mgr.set_token_cookie(response, access_token)
    return LoginReplyModel(access_token=access_token)


@router.post("/logout")
async def logout(
    request: Request, token: JWT = Depends(jwt_auth_scheme)
) -> None:
    deny_list = JWTDenyList(request.app.state.gstate.store)
    await deny_list.load()
    deny_list.add(token)
    await deny_list.save()
