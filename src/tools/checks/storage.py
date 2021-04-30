# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
from gravel.controllers.resources import storage
from gravel.controllers.orch.ceph import Mon


# TODO(jhesketh): This is probably broken from a previous ticker refactor

async def main():

    await storage.tick()
    print(await storage.usage())
    print(storage.available)
    print(storage.used)
    print(storage.total)
    assert storage.total == storage.used + storage.available

    mon = Mon()
    print(mon.df().json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
