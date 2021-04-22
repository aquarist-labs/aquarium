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
  -t | --type IMGTYPE       Specify image type (default: vagrant)
  -h | --help               This message.

allowed image types:
  vagrant                   Builds a vagrant image
  vagrant-virtualbox        Builds a vagrant virtualbox image
  self-install              Builds an image to be run on bare metal.
  live-iso		    Builds an live iso with persistent storage on bare metal.
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

imgtype="vagrant"
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
      ;;
    -t|--type)
      imgtype=$2
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

[[ -z "${imgtype}" ]] && \
  usage_error_exit "image type must be provided"

profile=""
case ${imgtype} in
  vagrant) profile="Ceph-Vagrant" type="oem";;
  vagrant-virtualbox) profile="Ceph-Vagrant-VirtualBox" type="oem";;
  self-install) profile="Ceph" type="oem";;
  live-iso) profile="Ceph" type="iso";;
  *)
    usage_error_exit "unknown image type: '${imgtype}'"
    ;;
esac

[[ -z "${profile}" ]] && \
  usage_error_exit "bad image type: '${imgtype}"

if ! kiwi-ng --version &>/dev/null ; then
  error_exit "missing kiwi-ng"
fi

if ! [[ -f /sbin/mkfs.btrfs || -f /bin/mkfs.btrfs ]]; then
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

set -x

mkdir -p ${build}

rm -f ${rootdir}/aquarium*.tar.gz
make dist
# At this point, we have a dist tarball (aquarium-$version.tar.gz), which
# has paths prefixed with aquarium-$version.  When using the tarball inside
# kiwi though, we need it to have bare /usr/... paths, so it's extracted
# to the right place, so *sigh*, let's extract the dist tarball and
# recompress it.  Bonus: this removes the version from the name, so we can
# just keep using <archive name="aquarium.tar.gz"/> in config.xml
tmpdir=$(mktemp -d)
pushd ${tmpdir}
tar --strip-components=1 -xzf ${rootdir}/aquarium*.tar.gz
sudo cp -r ${imgdir}/microOS/root/* ./
tar -czf ${build}/aquarium.tar.gz .
popd
rm -rf ${tmpdir}

tmpdir=$(mktemp -d)
pushd ${tmpdir}
sudo cp -r ${imgdir}/microOS/aquarium_root/* ./
tar -czf ${build}/aquarium_user.tar.gz .
popd
rm -rf ${tmpdir}


cp ${imgdir}/microOS/config.{sh,xml} ${build}/

mkdir ${build}/{_out,_logs}

osid=$(grep '^ID=' /etc/os-release | sed -e 's/\(ID=["]*\)\(.\+\)/\2/' | tr -d '"')
case $osid in
  opensuse-tumbleweed | opensuse-leap)
    (set -o pipefail
    sudo kiwi-ng --debug --profile=${profile} --type ${type}\
      system build --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    [ $? -eq 0 ] || error_exit "Kiwi build failed"
    ;;
  debian | ubuntu)
    (set -o pipefail
    sudo kiwi-ng --debug --profile=${profile} --type ${type}\
      system boxbuild --box tumbleweed --no-update-check -- --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    [ $? -eq 0 ] || error_exit "Kiwi build failed"
    ;;
  *)
    error_exit "unsupported distribution ($osid) kiwi-ng may not work"
      ;;
esac

