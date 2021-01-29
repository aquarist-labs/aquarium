#!/bin/bash

# don't recurse into ceph.git unless we explicitly need a submodule.
git submodule update --init || exit 1

[[ ! -e "src/cephadm/cephadm.py" ]] && \
  ln -vfs $(pwd)/ceph.git/src/cephadm/cephadm src/cephadm/cephadm.py
