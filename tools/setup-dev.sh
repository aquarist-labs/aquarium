#!/bin/bash

dependencies_opensuse_tumbleweed=(
  "git"
  "python3"
  "python3-rados"
  "python3-kiwi"
  "nodejs-common"
  "vagrant"
  "vagrant-libvirt"
)

usage() {
  cat << EOF
usage: $(basename $0) [options]

options:
  --show-dependencies     Show required dependencies.
  --skip-install-deps     Skip installing dependencies.
  -h|--help               This message.
EOF
}

yes_no() {
    while true; do
        read -p "$1? " yn
        case $yn in
            [Yy]* ) return 0; break;;
            [Nn]* ) return 1; break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

skip_install_deps=false
show_dependencies=false

while [[ $# -gt 0 ]]; do

  case $1 in
    --show-dependencies)
      show_dependencies=true
      ;;
    --skip-install-deps)
      skip_install_deps=true
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "error: unrecognized parameter '$1'"
      usage
      exit 1
      ;;
  esac
  shift 1
done

osid=$(grep '^ID=' /etc/os-release | sed -e 's/^ID="\(.\+\)"/\1/')

if ${show_dependencies} ; then

  case $osid in
    opensuse-tumbleweed | opensuse-leap)
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      ;;
    *)
      echo "error: unsupported distribution"
      echo "These are the packages you might need:"
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      exit 1
      ;;
  esac
  exit 0
fi


if ! ${skip_install_deps} ; then

  case $osid in
    opensuse-tumbleweed | opensuse-leap)
      echo "=> try installing dependencies"
      sudo zypper --non-interactive install ${dependencies_opensuse_tumbleweed[*]} || exit 1
      ;;
    *)
      echo "error: unsupported distribution ($osid)"
      echo "please install the following dependencies if not met:"
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      echo "and then run with '--skip-install-deps'"
      exit 1
      ;;
  esac

fi

if ! python3 --version &>/dev/null ; then
  echo "error: missing python3"
  exit 1
fi

if ! ( echo "import rados" | python3 &>/dev/null ); then
  echo "error: missing rados python bindings"
  exit 1
fi

if ! npm --version &>/dev/null ; then
  echo "error: missing npm"
  exit 1
fi

# don't recurse into ceph.git unless we explicitly need a submodule.
git submodule update --init || exit 1

[[ ! -e "src/gravel/cephadm/cephadm.bin" ]] && \
  ln -fs ../ceph.git/src/cephadm/cephadm src/gravel/cephadm/cephadm.bin

if [ -d venv ] ; then
    echo
    echo "Detected an existing virtual environment:"
    echo "  > $(realpath venv)"
    if yes_no "Blow it away"; then
        rm -rf venv || exit $?
    fi
    echo
fi

# we need system site packages because librados python bindings appear to only
# be available as a package. It might be a good idea to compile it from the
# ceph repo we keep as a submodule, but it might be overkill at the moment?
python3 -m venv --system-site-packages venv || exit 1

source venv/bin/activate
pip install -r src/requirements.txt || exit 1
deactivate

pushd src/glass &>/dev/null
npm install || exit 1
npx ng build || exit 1
popd &>/dev/null

