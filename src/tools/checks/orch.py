# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from gravel.controllers.orch.orchestrator \
    import OrchestratorHosts, OrchestratorDevices

if __name__ == "__main__":
    hosts = OrchestratorHosts()
    res = hosts.ls()
    for host in res:
        print(host.json(indent=2))
    devs = OrchestratorDevices()
    res = devs.ls()
    for dev in res:
        print(dev.json(indent=2))
