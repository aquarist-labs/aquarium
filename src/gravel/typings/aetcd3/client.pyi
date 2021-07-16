# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

# pyright: reportMissingTypeStubs=false
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    IO,
    List,
    Optional,
    Tuple,
    Union,
)

from aetcd3.etcdrpc.rpc_pb2 import (
    Compare,
    DeleteRangeResponse,
    LeaseKeepAliveResponse,
    LeaseRevokeResponse,
    LeaseTimeToLiveResponse,
    PutResponse,
    RequestOp,
    ResponseOp,
)
from aetcd3.events import Event
from aetcd3.leases import Lease
from aetcd3.locks import Lock
from aetcd3.members import Member

class Transactions: ...

class KVMetadata:
    key: bytes
    create_revision: int
    mod_revision: int
    version: int
    lease_id: int
    ...

class Status: ...
class Alarm: ...

class Etcd3Client:
    def __init__(
        self,
        host: str = ...,
        port: int = ...,
        ca_cert: Optional[str] = ...,
        cert_key: Optional[str] = ...,
        cert_cert: Optional[str] = ...,
        timeout: Optional[float] = ...,
        user: Optional[str] = ...,
        password: Optional[str] = ...,
        gprc_options: Dict[Any, Any] = ...,
    ) -> None: ...
    async def open(self) -> None: ...
    async def close(self) -> None: ...
    async def __aenter__(self) -> Any: ...
    async def __aexit__(self, *args: Any) -> Any: ...
    async def get(
        self, key: str, serializable: bool = ...
    ) -> Tuple[bytes, KVMetadata]: ...
    async def get_prefix(
        self,
        key_prefix: str,
        sort_order: Optional[str] = ...,
        sort_target: str = ...,
        keys_only: bool = ...,
    ) -> Generator[Tuple[bytes, KVMetadata], None, None]: ...
    async def get_range(
        self,
        range_start: str,
        range_end: str,
        sort_order: Optional[str] = ...,
        sort_target: str = ...,
        **kwargs: Any,
    ) -> Generator[Tuple[bytes, KVMetadata], None, None]: ...
    async def get_all(
        self,
        sort_order: Optional[str] = ...,
        sort_target: Optional[str] = ...,
        keys_only: bool = ...,
    ) -> Generator[Tuple[bytes, KVMetadata], None, None]: ...
    ...
    async def put(
        self,
        key: str,
        value: Union[bytes, str],
        lease: Optional[Union[Lease, int]] = ...,
        prev_kv: bool = ...,
    ) -> PutResponse: ...
    async def replace(
        self,
        key: str,
        initial_value: Union[bytes, str],
        new_value: Union[bytes, str],
    ) -> bool: ...
    async def delete(
        self, key: str, prev_kv: bool = ..., return_response: bool = ...
    ) -> Union[bool, DeleteRangeResponse]: ...
    async def delete_prefix(self, prefix: str) -> DeleteRangeResponse: ...
    async def status(self) -> Status: ...
    async def add_watch_callback(
        self,
        key: str,
        callback: Callable[[Event], Awaitable[None]],
        **kwargs: Any,
    ) -> int: ...
    async def watch(
        self, key: str, **kwargs: Any
    ) -> Tuple[AsyncIterator[Event], Awaitable[None]]: ...
    async def watch_prefix(
        self, key_prefix: str, **kwargs: Any
    ) -> Tuple[AsyncIterator[Event], Awaitable[None]]: ...
    async def watch_once(
        self, key: str, timeout: Optional[float] = ..., **kwargs: Any
    ) -> Any: ...
    async def watch_prefix_once(
        self, key_prefix: str, timeout: Optional[float] = ..., **kwargs: Any
    ) -> Any: ...
    async def cancel_watch(self, watch_id: int) -> None: ...
    async def transaction(
        self,
        compare: List[Compare],
        success: Optional[List[RequestOp]] = ...,
        failure: Optional[List[RequestOp]] = ...,
    ) -> Tuple[bool, List[ResponseOp]]: ...
    async def lease(self, ttl: int, id: int) -> Lease: ...
    async def revoke_lease(self, lease_id: int) -> LeaseRevokeResponse: ...
    async def refresh_lease(self, lease_id: int) -> LeaseKeepAliveResponse: ...
    async def get_lease_info(
        self, lease_id: int, *, keys: bool = ...
    ) -> LeaseTimeToLiveResponse: ...
    def lock(self, name: str, ttl: int = ...) -> Lock: ...
    async def add_member(
        self, urls: List[str]
    ) -> Tuple[Member, List[Member]]: ...
    async def remove_member(self, member_id: int) -> None: ...
    async def update_member(
        self, member_id: int, peer_urls: List[str]
    ) -> None: ...
    async def members(self) -> Generator[Member, None, None]: ...
    async def compact(self, revision: int, physical: bool = ...) -> None: ...
    async def defragment(self) -> None: ...
    async def hash(self) -> int: ...
    async def create_alarm(self, member_id: int = ...) -> List[Alarm]: ...
    async def list_alarms(
        self, member_id: int, alarm_type: str = ...
    ) -> Generator[Alarm, None, None]: ...
    async def disarm_alarm(self, member_id: int = ...) -> List[Alarm]: ...
    async def snapshot(self, file_obj: IO[bytes]) -> None: ...
    ...

def client(
    host: str = ...,
    port: int = ...,
    ca_cert: Optional[str] = ...,
    cert_key: Optional[str] = ...,
    timeout: Optional[float] = ...,
    cert_cert: Optional[str] = ...,
    user: Optional[str] = ...,
    password: Optional[str] = ...,
    **kwargs: Any,
) -> Etcd3Client: ...
