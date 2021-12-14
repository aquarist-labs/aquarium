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
from typing import Any, Callable, List, Literal

from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel.api import install_gate, jwt_auth_scheme
from gravel.cephadm.models import VolumeDeviceModel
from gravel.controllers.config import SSLOptionsModel
from gravel.controllers.gstate import GlobalState
from gravel.controllers.inventory.nodeinfo import NodeInfoModel
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.nodes.requirements import (
    RequirementsModel,
    localhost_qualified,
)
from gravel.controllers.resources.network import NetworkConfigModel
from gravel.controllers.utils import aqr_run_cmd

logger: Logger = fastapi_logger

router: APIRouter = APIRouter(prefix="/local", tags=["local"])


class NodeStatusReplyModel(BaseModel):
    localhost_qualified: RequirementsModel = Field(
        title="Validation results of localhost"
    )
    inited: bool = Field("Node has been inited and can be used")


class EventModel(BaseModel):
    ts: int = Field(title="The Unix time stamp")
    severity: Literal["info", "warn", "danger"]
    message: str


class SSLConfigModel(BaseModel):
    use_ssl: bool = Field(False, title="Whether https is enabled.")
    key_contents: str = Field(title="The SSL private key.")
    cert_contents: str = Field(title="The SSL certificate.")


@router.get(
    "/volumes",
    name="Obtain local volumes",
    response_model=List[VolumeDeviceModel],
)
async def get_volumes(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> List[VolumeDeviceModel]:
    """
    List this node's volumes.

    This information is obtained via `cephadm`, periodically, and may not be
    100% up to date between calls to this endpoint.
    """
    inventory = request.app.state.gstate.inventory
    latest = inventory.latest
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail="Volume list not yet available.",
        )
    return latest.disks


@router.get(
    "/nodeinfo",
    name="Obtain local node information",
    response_model=NodeInfoModel,
)
async def get_node_info(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> NodeInfoModel:
    """
    Obtain this node's information and facts.

    Lists the node's volumes (same as `/local/volumes`), and additional host
    information, such as OS metadata, NICs, etc.

    This information is obtained via `cephadm`.

    This is a sync call to `cephadm` and may take a while to return.
    """
    cephadm = request.app.state.gstate.cephadm
    return await cephadm.get_node_info()


@router.get(
    "/inventory",
    name="Obtain local node inventory",
    response_model=NodeInfoModel,
)
async def get_inventory(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> NodeInfoModel:
    """
    Obtain this node's inventory.

    Includes information about the node's devices, OS information, NICs, etc.

    This information is obtained via `cephadm`, periodically, and may not be
    100% up to date between calls to this endpoint.

    This endpoint is preferred over `/local/nodeinfo` because the information
    is cached and puts less strain on the node. If the most up to date
    information is required, and the caller does not have constraints waiting
    for a return, `/local/nodeinfo` should be used.
    """
    inventory = request.app.state.gstate.inventory
    latest = inventory.latest
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail="Inventory not available.",
        )
    return latest


@router.get(
    "/status",
    name="Obtain local node's status",
    response_model=NodeStatusReplyModel,
)
async def get_status(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> NodeStatusReplyModel:
    """
    Obtain this node's current status.

    Includes information on whether the node has been initiated and can be used,
    as well as the node's deployment stage.
    """

    nodemgr: NodeMgr = request.app.state.nodemgr

    return NodeStatusReplyModel(
        localhost_qualified=await localhost_qualified(),
        inited=nodemgr.available,
    )


@router.get(
    "/events",
    name="Obtain events from local node",
    response_model=List[EventModel],
)
async def get_events(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> List[EventModel]:
    # ToDo: Replace mocked data by live data.
    events = [
        {
            "ts": 1633362463,
            "severity": "info",
            "message": "fooo bar asdasdlkasjd aksdjlas dasjdlsakjd asdkasld asdas.",
        },
        {
            "ts": 1633363417,
            "severity": "warn",
            "message": "Lorem ipsum dolor sit amet, sed diam voluptua.",
        },
        {
            "ts": 1633213519,
            "severity": "danger",
            "message": "dasda ffkv dolor sit ametasdha jhdakjsh 4232 asdasd sadasdas.",
        },
    ]
    return [EventModel.parse_obj(event) for event in events]


@router.get(
    "/ssl",
    name="Get current SSL configuration",
    response_model=SSLOptionsModel,
)
async def get_ssl_config(
    request: Request, _: Callable = Depends(jwt_auth_scheme)
) -> SSLOptionsModel:
    return request.app.state.gstate.config.options.ssl


@router.post("/ssl", name="Update SSL configuration")
async def apply_ssl_config(
    request: Request,
    req_params: SSLConfigModel,
    _: Callable = Depends(jwt_auth_scheme),
) -> bool:
    request.app.state.gstate.config.write_ssl_key(req_params.key_contents)
    request.app.state.gstate.config.write_ssl_cert(req_params.cert_contents)
    request.app.state.gstate.config.options.ssl.use_ssl = req_params.use_ssl
    request.app.state.gstate.request_restart_uvicorn()
    return request.app.state.gstate.config.saveConfig()


@router.post("/reboot", name="Reboot the system")
async def reboot(_: Callable = Depends(jwt_auth_scheme)) -> None:
    ret, _, stderr = await aqr_run_cmd(["systemctl", "reboot"])  # type: ignore
    if ret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to reboot the system: {stderr}",
        )


@router.post("/shutdown", name="Shutdown the system")
async def shutdown(_: Callable = Depends(jwt_auth_scheme)) -> None:
    ret, _, stderr = await aqr_run_cmd(["systemctl", "poweroff"])  # type: ignore
    if ret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to shutdown the system: {stderr}",
        )


@router.get(
    "/network/config",
    name="Obtain local node's network configuration",
    response_model=NetworkConfigModel,
)
async def get_network_config(
    request: Request, _=Depends(jwt_auth_scheme)
) -> NetworkConfigModel:
    """
    Obtain this node's network configuration.
    """

    network = request.app.state.gstate.network
    return NetworkConfigModel(
        interfaces=network.interfaces,
        nameservers=network.nameservers,
        routes=network.routes,
    )


@router.post(
    "/network/config",
    name="Apply network config",
    response_model=bool,
)
async def apply_network_config(
    request: Request,
    req_params: NetworkConfigModel,
    _=Depends(jwt_auth_scheme),
) -> bool:

    network = request.app.state.gstate.network
    await network.apply_config(
        req_params.interfaces, req_params.nameservers, req_params.routes
    )

    # TODO: Make this return something sensible on failure
    return True
