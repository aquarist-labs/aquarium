from typing import Any, List

class Member:

    id: int
    name: str
    peer_urls: List[str]
    client_urls: List[str]
    _etcd_client: Any
    def __init__(
        self,
        id: int,
        name: str,
        peer_urls: List[str],
        client_urls: List[str],
        etcd_client: Any = ...,
    ) -> None: ...
