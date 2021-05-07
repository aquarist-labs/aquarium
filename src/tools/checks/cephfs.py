# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from gravel.controllers.orch.ceph import Ceph, Mgr, Mon
from gravel.controllers.orch.cephfs import CephFS, CephFSError

if __name__ == "__main__":
    ceph: Ceph = Ceph()
    ceph_mgr: Mgr = Mgr(ceph)
    ceph_mon: Mon = Mon(ceph)
    cephfs: CephFS = CephFS(ceph_mgr, ceph_mon)

    try:
        cephfs.create("foobarbaz")
    except CephFSError as e:
        print(f"error: {str(e)}")
    res = cephfs.volume_ls()
    print(res.json())
    print(cephfs.ls())
