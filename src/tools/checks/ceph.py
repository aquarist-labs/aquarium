# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.


from gravel.controllers.orch.ceph import Ceph, Mon


if __name__ == "__main__":
    ceph: Ceph = Ceph()
    ceph_mon: Mon = Mon(ceph)

    print(ceph_mon.get_osdmap())
    print(ceph_mon.get_pools())
    pass
