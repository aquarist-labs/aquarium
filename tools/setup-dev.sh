#!/bin/bash

if ! ( echo "import rados" | python3 &>/dev/null ); then
  echo "error: missing rados python bindings"
  exit 1
fi

# don't recurse into ceph.git unless we explicitly need a submodule.
git submodule update --init || exit 1

[[ ! -e "src/gravel/cephadm/cephadm.bin" ]] && \
  ln -fs ../ceph.git/src/cephadm/cephadm src/gravel/cephadm/cephadm.bin

if [[ ! -e "venv" ]]; then

  # we need system site packages because librados python bindings appear to only
  # be available as a package. It might be a good idea to compile it from the
  # ceph repo we keep as a submodule, but it might be overkill at the moment?
  python3 -m venv --system-site-packages venv || exit 1
  source venv/bin/activate
  pip install -r requirements.txt || exit 1

fi

