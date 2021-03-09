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


usage() {
  cat << EOF
usage: $0 [options]

options:
  -n NAME | --name NAME     Specify build name (default: aquarium).
  -c | --clean              Cleanup an existing build directory before building.
  -h | --help               This message.
EOF

}

usage_error_exit() {
    echo "error: $1" > /dev/stderr
    usage > /dev/stderr
    exit 1
}

error_exit() {
    echo "error: $1" > /dev/stderr
    exit 1
}

find_root || exit 1
[[ -z "${rootdir}" ]] && \
  error_exit "unable to find repository's root dir"

imgdir=${rootdir}/images
srcdir=${rootdir}/src

[[ ! -d "${imgdir}" ]] && \
  error_exit "unable to find 'images' directory at ${rootdir}"

[[ ! -d "${srcdir}" ]] && \
  error_exit "unable to find 'src' directory at ${rootdir}" 

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
      usage_error_exit "unrecognized option: '$1'"
      ;;
  esac
  shift 1
done

[[ -z "${build_name}" ]] && \
  usage_error_exit "missing build name"

if ! kiwi-ng --version &>/dev/null ; then
  error_exit "missing kiwi-ng"
fi

if ! /sbin/mkfs.btrfs --version &>/dev/null ; then
  echo "error: missing btrfsprogs"
  exit 1
fi

build=${imgdir}/build/${build_name}

if [[ -e "${build}" && "${clean}" -eq "1" ]]; then
  echo "warning: removing existing build '${build_name}'"
  # TODO: Figure out if there's a way of having the build directory not
  # owned by root in the first place.
  sudo rm -rf ${build}
fi

if [[ -e "${build}" ]]; then
  error_exit "build with name '${build_name}' already exists (use --clean if you want to remove it)"
fi

set -xe

glassdir=${srcdir}/glass
graveldir=${srcdir}/gravel

[[ ! -d "${glassdir}" ]] && \
  error_exit "missing frontend directory at '${glassdir}"

[[ ! -e "${glassdir}/angular.json" ]] && \
  error_exit "directory at '${glassdir}' is not an angular application"

[[ ! -d "${graveldir}" ]] && \
  error_exit "missing backend directory at '${graveldir}"


build_glass() {
  pushd ${glassdir}
  npm install || exit 1
  npx ng build --prod --output-hashing=all || exit 1
  [[ ! -d "${glassdir}/dist" ]] && \
    error_exit "missing 'dist' directory for frontend"
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

osid=$(grep '^ID=' /etc/os-release | sed -e 's/\(ID=["]*\)\(.\+\)/\2/' | tr -d '"')
case $osid in
  opensuse-tumbleweed | opensuse-leap)
    (set -o pipefail
    sudo kiwi-ng --debug --profile=Ceph-Vagrant --type oem \
      system build --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    ;;
  debian | ubuntu)
    (set -o pipefail
    sudo kiwi-ng --debug --profile=Ceph-Vagrant --type oem \
      system boxbuild --box tumbleweed --no-update-check -- --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    ;;
  *)
    echo "error: unsupported distribution ($osid) kiwi-ng may not work"
    exit 1
      ;;
esac

exit $?
