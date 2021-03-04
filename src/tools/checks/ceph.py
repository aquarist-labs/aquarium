# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.


from gravel.controllers.orch.ceph import Mon


if __name__ == "__main__":
    mon = Mon()
    print(mon.get_osdmap())
    print(mon.get_pools())
    pass
