#!/bin/bash

LC_ALL=C.UTF-8

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
  -t | --type IMGTYPE       Specify image type (default: vagrant).
  -b | --base OSTYPE        Specify OS type (default: Tumbleweed).
  --rootdir PATH            Path to repository's root.
  --buildsdir PATH          Path to output builds directory.
  --cachedir PATH           Path to kiwi's shared cache directory.
  -h | --help               This message.

allowed image types:
  vagrant                   Builds a vagrant image.
  virtualbox                Builds a virtualbox image.
  self-install              Builds an image to be run on bare metal.
  live-iso                  Builds an live iso with persistent storage
                            on bare metal.

allowed OS Types:
  Tumbleweed                Builds a Tumbleweed base image.
  MicroOS                   Builds a MicroOS base image.

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

imgtype="vagrant"
ostype="Tumbleweed"
build_name="aquarium"
clean=0

buildsdir=
cachedir=

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
    -b|--base)
      ostype=$2
      shift 1
      ;;
    --rootdir)
      rootdir=$2
      shift 1
      ;;
    --buildsdir)
      buildsdir=$2
      shift 1
      ;;
    --cachedir)
      cachedir=$2
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

if [[ -z "${rootdir}" ]]; then
  find_root || exit 1
fi

[[ -z "${rootdir}" ]] && \
  error_exit "unable to find repository's root dir"

imgdir=${rootdir}/images
srcdir=${rootdir}/src

[[ -z "${buildsdir}" ]] && buildsdir=${imgdir}/build

[[ ! -d "${imgdir}" ]] && \
  error_exit "unable to find 'images' directory at ${rootdir}"

[[ ! -d "${srcdir}" ]] && \
  error_exit "unable to find 'src' directory at ${rootdir}" 


[[ -z "${build_name}" ]] && \
  usage_error_exit "missing build name"

[[ -z "${imgtype}" ]] && \
  usage_error_exit "image type must be provided"

profile=""
case ${ostype} in 
    Tumbleweed)
        kiwi_conf_dir=aquarium
        case ${imgtype} in
            vagrant) profile="Ceph-Vagrant-libvirt" type="oem";;
            virtualbox) profile="Ceph-Vagrant-VirtualBox" type="oem";;
            self-install) profile="Ceph" type="oem";;
            live-iso) profile="Ceph" type="iso";;
            *)
                usage_error_exit "unknown image type: '${imgtype}'"
            ;;
        esac
	;;
    MicroOS)
        kiwi_conf_dir=MicroOS
        case ${imgtype} in
            vagrant) profile="Vagrant" type="oem";;
            virtualbox) profile="VirtualBox" type="oem";;
            self-install) profile="ContainerHost-SelfInstall" type="oem";;
            *)
                usage_error_exit "unknown image type: '${imgtype}'"
            ;;
        esac
    ;;
    *)
        usage_error_exit "unknown OS type: '${ostype}'"
    ;;
esac

[[ -z "${profile}" ]] && \
  usage_error_exit "bad image type: '${imgtype}"



if ! kiwi-ng --version &>/dev/null ; then
  error_exit "missing kiwi-ng"
fi

build=${buildsdir}/${build_name}

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
pushd ${rootdir}
make dist
[ $? -eq 0 ] || error_exit "make dist failed"
popd

# At this point, we have a dist tarball (aquarium-$version.tar.gz), which
# has paths prefixed with aquarium-$version.  When using the tarball inside
# kiwi though, we need it to have bare /usr/... paths, so it's extracted
# to the right place, so *sigh*, let's extract the dist tarball and
# recompress it.  Bonus: this removes the version from the name, so we can
# just keep using <archive name="aquarium.tar.gz"/> in config.xml
tmpdir=$(mktemp -d)
pushd ${tmpdir}
tar --strip-components=1 -xzf ${rootdir}/aquarium*.tar.gz
tar --owner root --group root -czf ${build}/aquarium.tar.gz .
popd
rm -rf ${tmpdir}

# Extra files needed in system root
pushd ${imgdir}/${kiwi_conf_dir}/root
tar --owner root --group root -czf ${build}/root.tar.gz .
popd

# Extra files needed in system root for live image
pushd ${imgdir}/${kiwi_conf_dir}/aquarium_root
tar --owner root --group root -czf ${build}/aquarium_user.tar.gz .
popd


cp ${imgdir}/${kiwi_conf_dir}/config.{sh,xml} \
   ${imgdir}/${kiwi_conf_dir}/disk.sh \
   ${build}/

mkdir ${build}/{_out,_logs}

kiwiargs=
[[ -n "${cachedir}" ]] && kiwiargs="--shared-cache-dir=${cachedir}"
if [ -t 1 ] ; then
	kiwiargs+=" --debug"
elif kiwi-ng --help | grep -q -- '--logfile stdout' ; then
	kiwiargs+=" --logfile stdout"
fi

osid=$(grep '^ID=' /etc/os-release | sed -e 's/\(ID=["]*\)\(.\+\)/\2/' | tr -d '"')
case $osid in
  opensuse-tumbleweed | opensuse-leap)
    (set -o pipefail
    sudo kiwi-ng ${kiwiargs} --profile=${profile} --type ${type}\
      system build --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    [ $? -eq 0 ] || error_exit "Kiwi build failed"
    ;;
  debian | ubuntu)
    (set -o pipefail
    kiwi-ng ${kiwiargs} --profile=${profile} --type ${type}\
      system boxbuild --box tumbleweed -- --description ${build} \
      --target-dir ${build}/_out |\
      tee ${build}/_logs/${build_name}-build.log)
    [ $? -eq 0 ] || error_exit "Kiwi build failed"
    ;;
  *)
    error_exit "unsupported distribution ($osid) kiwi-ng may not work"
      ;;
esac

