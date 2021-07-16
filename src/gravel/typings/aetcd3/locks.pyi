# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

# pyright: reportMissingTypeStubs=false
from typing import Optional
import aetcd3
from aetcd3.etcdrpc.rpc_pb2 import LeaseKeepAliveResponse

class Lock:
    def __init__(
        self,
        name: str,
        ttl: int = ...,
        etcd_client: Optional[aetcd3.Etcd3Client] = ...,
    ) -> None: ...
    async def acquire(self, timeout: int = ...) -> bool: ...
    async def release(self) -> bool: ...
    async def refresh(self) -> LeaseKeepAliveResponse: ...
    async def is_acquired(self) -> bool: ...
