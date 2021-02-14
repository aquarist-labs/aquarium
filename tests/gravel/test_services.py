# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
from gravel.controllers.services import ServiceTypeEnum, Services
from gravel.controllers.resources import storage


async def main():
    await storage.tick()
    services = Services()
    services.create("test-svc", ServiceTypeEnum.CEPHFS, 1000, 2)


if __name__ == "__main__":
    asyncio.run(main())
