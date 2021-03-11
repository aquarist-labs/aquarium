# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from gravel.controllers.orch.cephfs import CephFS, CephFSError

if __name__ == "__main__":
    cephfs = CephFS()
    try:
        cephfs.create("foobarbaz")
    except CephFSError as e:
        print(f"error: {str(e)}")
    res = cephfs.volume_ls()
    print(res.json())
    print(cephfs.ls())
