#!/bin/bash

rootdir=

find_root() {
  cwd=$(pwd)
  while true; do
    if [[ "${cwd}" == "/" ]]; then
      echo "error: unable to find root git repository"
      return 1
    fi
    if [[ -d "${cwd}/.git" ]]; then
      rootdir=${cwd}
      return 0
    fi
    cwd=$(realpath ${cwd}/..)
  done
}

find_root || exit 1
[[ -z "${rootdir}" ]] && \
  echo "error: unable to find repository's root dir" && \
  exit 1

imgdir=${rootdir}/images
srcdir=${rootdir}/src

[[ ! -d "${imgdir}" ]] && \
  echo "error: unable to find 'images' directory at ${rootdir}" && \
  exit 1

[[ ! -d "${srcdir}" ]] && \
  echo "error: unable to find 'src' directory at ${rootdir}" && \
  exit 1

usage() {
  cat << EOF
usage: $0 [options]

options:
  -n NAME | --name NAME     Specify build name (default: aquarium).
  -c | --clean              Cleanup an existing build directory before building.
  -h | --help               This message.
EOF

}

build_name="aquarium"
clean=0

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--name)
      build_name=$2
      shift 1
      ;;
    -c|--clean)
      clean=1
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unrecognized option: '$1'"
      usage
      exit 1
      ;;
  esac
  shift 1
done

[[ -z "${build_name}" ]] && \
  echo "error: missing build name" && \
  usage && \
  exit 1

if ! kiwi-ng --version &>/dev/null ; then
  echo "error: missing kiwi-ng"
  exit 1
fi

if ! sudo mkfs.btrfs --version &>/dev/null ; then
  echo "error: missing btrfstools"
  exit 1
fi

build=${imgdir}/build/${build_name}

if [[ -e "${build}" ]]; then
  if [[ "${clean}" -eq "1" ]]; then
    echo "warning: removing existing build '${build_name}'"
    rm -rf ${build}
  else
    echo "error: build with name '${build_name}' already exists"
    exit 1
  fi
fi

set -xe

glassdir=${srcdir}/glass
graveldir=${srcdir}/gravel

[[ ! -d "${glassdir}" ]] && \
  echo "error: missing frontend directory at '${glassdir}" && \
  exit 1

[[ ! -e "${glassdir}/angular.json" ]] && \
  echo "error: directory at '${glassdir}' is not an angular application" && \
  exit 1

[[ ! -d "${graveldir}" ]] && \
  echo "error: missing backend directory at '${graveldir}" && \
  exit 1


build_glass() {
  pushd ${glassdir}
  npm install || exit 1
  npx ng build --prod --output-hashing=all || exit 1
  [[ ! -d "${glassdir}/dist" ]] && \
    echo "error: missing 'dist' directory for frontend" && \
    exit 1
  popd
}

bundle() {
  local bundledir=${build}/bundle
  local bundle_usr=${bundledir}/usr/share/aquarium
  local bundle_unit=${bundledir}/usr/lib/systemd/system
  local bundle_sbin=${bundledir}/usr/sbin

  mkdir -p ${bundle_usr} ${bundle_unit} ${bundle_sbin} || true
  build_glass || exit 1

  pushd ${rootdir}
  git submodule update --init || exit 1
  popd

  pushd ${srcdir}
  find ./gravel -iname '*ceph.git*' -prune -false -o -iname '*.py' | \
    xargs cp --parents --target-directory=${bundle_usr} || exit 1
  cp --target-directory=${bundle_usr} ./aquarium.py || exit 1
  cp -R --parents --target-directory=${bundle_usr} glass/dist || exit 1

  cp --target-directory=${bundle_sbin} \
    ./gravel/ceph.git/src/cephadm/cephadm || exit 1
  popd

  cp ${rootdir}/systemd/aquarium.service ${bundle_unit} || exit 1

  pushd ${build}
  tar -C ${bundledir} usr -cf aquarium.tar || exit 1
  popd
}


mkdir -p ${build}

cp ${imgdir}/microOS/config.{sh,xml} ${build}/
bundle || exit 1

mkdir ${build}/{_out,_logs}
(set -o pipefail
sudo kiwi-ng --debug --profile=Ceph-Vagrant --type oem \
  system build --description ${build} \
  --target-dir ${build}/_out |\
  tee ${build}/_logs/${build_name}-build.log)

exit $?

