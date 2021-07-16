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

# pyright: reportUnknownMemberType=false, reportPrivateUsage=false

import pytest

from gravel.controllers.auth import JWT, JWTDenyList, JWTMgr, UserModel, UserMgr
from gravel.controllers.config import AuthOptionsModel
from gravel.controllers.gstate import GlobalState


def test_user_model_hash_password():
    user = UserModel(password="bar")
    assert user.password == "bar"
    user.hash_password()
    assert user.password != "bar"


def test_user_model_verify_password():
    user = UserModel(password="foo")
    user.hash_password()
    assert user.verify_password("foo")
    assert not user.verify_password("bar")


@pytest.mark.asyncio
async def test_user_mgr(gstate: GlobalState):
    await gstate.store.ensure_connection()
    user_mgr = UserMgr(gstate.store)
    user1 = UserModel(username="foo", password="test1", full_name="foo loo")
    user1.hash_password()
    user2 = UserModel(username="bar", password="test2", full_name="bar baz")
    user2.hash_password()
    await user_mgr.put(user1)
    await user_mgr.put(user2)
    assert await user_mgr.exists("foo")
    assert not await user_mgr.exists("xyz")
    assert len(await user_mgr.enumerate()) == 2
    user = await user_mgr.get("bar")
    assert user is not None
    assert user.username == "bar"
    await user_mgr.remove("bar")
    assert len(await user_mgr.enumerate()) == 1
    assert await user_mgr.authenticate("foo", "test1")
    assert not await user_mgr.authenticate("foo", "abc")


def test_jwt_mgr_create_access_token():
    config = AuthOptionsModel()
    jwt_mgr = JWTMgr(config)
    assert type(jwt_mgr.create_access_token("foo")) is str


def test_jwt_mgr_get_raw_access_token():
    config = AuthOptionsModel(jwt_secret="m[>\\Ura3,C`<NV^m\ryG0-^ik")
    jwt_mgr = JWTMgr(config)
    token = (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJBcXVhcml1b"
        "SIsInN1YiI6ImZvbyIsImlhdCI6MTYyNTE1MjQ4OSwibmJmIjoxNjI1MTU"
        "yNDg5LCJleHAiOjE2MjUxODg0ODksImp0aSI6Ijg3YmYzMWJjLWI5Y2MtN"
        "DNlOC05MDFmLWU2MDdlNWU5ODY5MiJ9.PsNLQLfMTW5QT5GPS2sam_ReIt"
        "erTZ_NKTO4rBhLcdI"
    )
    raw_token = jwt_mgr.get_raw_access_token(token, verify=False)
    assert isinstance(raw_token, JWT)
    assert raw_token.sub == "foo"


@pytest.mark.asyncio
async def test_jwt_deny_list(gstate: GlobalState):
    await gstate.store.ensure_connection()
    jwt_deny_list = JWTDenyList(gstate.store)
    await jwt_deny_list.load()
    assert not len(jwt_deny_list._jti_dict)
    jwt = JWT(
        iss="Aquarium",
        sub="foo",
        iat=1625152489,
        nbf=1625152489,
        exp=1625188489,
        jti="87bf31bc-b9cc-43e8-901f-e607e5e98692",
    )
    jwt_deny_list.add(jwt)
    assert jwt_deny_list.includes(jwt)
    # Cleanup expired tokens.
    jwt_deny_list._cleanup(1625188489)
    assert not jwt_deny_list.includes(jwt)
