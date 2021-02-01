# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import asyncio
import os
from typing import List
from io import StringIO
from typing import List, Tuple

class Cephadm:

    def __init__(self):

        if os.path.exists("./cephadm.bin"):
            # dev environment
            self.cephadm = "sudo ./cephadm.bin"
        else:
            # deployment environment
            self.cephadm = "sudo cephadm"

        pass

    async def call(self, cmd: str) -> Tuple[str, str, int]:

        cmdlst: List[str] = f"{self.cephadm} {cmd}".split()

        process = await asyncio.create_subprocess_exec(
            *cmdlst,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        assert process.stdout
        assert process.stderr

        stdout, stderr = await asyncio.gather(
            self._tee(process.stdout), self._tee(process.stderr)
        )
        retcode = await asyncio.wait_for(process.wait(), None)

        return stdout, stderr, retcode 


    async def run_in_background(self, cmd: List[str]) -> None:
        pass


    async def _tee(self, reader: asyncio.StreamReader) -> str:
        collected = StringIO()
        async for line in reader:
            msg = line.decode("utf-8")
            collected.write(msg)
        return collected.getvalue()
