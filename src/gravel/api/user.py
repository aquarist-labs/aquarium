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
from typing import List

from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from gravel.api import jwt_auth_scheme
from gravel.controllers.auth import JWT, UserMgr, UserModel

logger: Logger = fastapi_logger

router: APIRouter = APIRouter(prefix="/user", tags=["user"])


@router.get("/", name="Get list of users", response_model=List[UserModel])
async def enumerate_users(
    request: Request, _=Depends(jwt_auth_scheme)
) -> List[UserModel]:
    user_mgr = UserMgr(request.app.state.gstate.store)
    return await user_mgr.enumerate()


@router.post("/create", name="Create a new user")
async def create_user(
    user: UserModel, request: Request, _=Depends(jwt_auth_scheme)
) -> None:
    user_mgr = UserMgr(request.app.state.gstate.store)
    if await user_mgr.exists(user.username):
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User already exists"
        )
    user.hash_password()
    await user_mgr.put(user)


@router.get("/{username}", name="Get a user by name", response_model=UserModel)
async def get_user(
    username: str, request: Request, _=Depends(jwt_auth_scheme)
) -> UserModel:
    user_mgr = UserMgr(request.app.state.gstate.store)
    if not await user_mgr.exists(username):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )
    return await user_mgr.get(username)  # type: ignore[return-value]


@router.delete("/{username}", name="Delete a user by name")
async def delete_user(
    username: str, request: Request, token: JWT = Depends(jwt_auth_scheme)
) -> None:
    user_mgr = UserMgr(request.app.state.gstate.store)
    if not await user_mgr.exists(username):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )
    if token.sub == username:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Cannot delete current user"
        )
    await user_mgr.remove(username)


@router.patch(
    "/{username}", name="Update a user by name", response_model=UserModel
)
async def patch_user(
    username: str,
    update_user: UserModel,
    request: Request,
    token: JWT = Depends(jwt_auth_scheme),
) -> UserModel:
    user_mgr = UserMgr(request.app.state.gstate.store)
    user = await user_mgr.get(username)
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )
    if token.sub == username and update_user.disabled:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Cannot disable current user"
        )
    if update_user.password:
        update_user.hash_password()
    update_data = update_user.dict(exclude_unset=True, exclude_none=True)
    if not update_data["password"]:
        update_data.pop("password")
    user = user.copy(update=update_data)
    await user_mgr.put(user)
    return user
