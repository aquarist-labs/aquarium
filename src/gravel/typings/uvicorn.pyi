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

from typing import Any, Dict, Optional


class Config:

    def __init__(
        self,
        app: Any,
        host: str,
        port: int,
        uds: Optional[Any] = ...,
        fd: Optional[Any] = ...,
        loop: str = ...,
        http: str = ...,
        ws: str = ...,
        lifespan: str = ...,
        env_file: Optional[Any] = ...,
        log_config: Dict[str, Any] = ...,
        log_level: Any = ...,
        access_log: bool = ...,
        use_colors: Optional[Any] = ...,
        interface: str = ...,
        debug: bool = ...,
        reload: bool = ...,
        reload_dirs: Optional[Any] = ...,
        reload_delay: Optional[Any] = ...,
        workers: Optional[Any] = ...,
        proxy_headers: bool = ...,
        forwarded_allow_ips: Optional[Any] = ...,
        root_path: str = ...,
        limit_concurrency: Optional[Any] = ...,
        limit_max_requests: Optional[Any] = ...,
        backlog: int = ...,
        timeout_keep_alive: int = ...,
        timeout_notify: int = ...,
        callback_notify: Optional[Any] = ...,
        ssl_keyfile: Optional[Any] = ...,
        ssl_certfile: Optional[Any] = ...,
        ssl_keyfile_password: Optional[Any] = ...,
        ssl_version: str = ...,
        ssl_cert_reqs: Any = ...,
        ssl_ca_certs: Optional[Any] = ...,
        ssl_ciphers: str = ...,
        headers: Optional[Any] = ...,
        factory: bool = ...,
    ) -> None:
        ...

    def setup_event_loop(self) -> None: ...

    ...


class Server:

    should_exit: bool
    force_exit: bool

    def __init__(self, config: Config) -> None: ...

    async def serve(self, sockets: Optional[Any] = ...) -> None: ...
    ...


def run(app: Any, **kwargs: Any) -> None:
    ...
