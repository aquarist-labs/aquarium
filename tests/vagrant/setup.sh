#!/bin/bash

basedir=$(dirname $(realpath $0))
setupdir=${basedir}/setups

usage() {
  cat << EOF
usage: $(basename $0) [options] <NAME>

options:
  -b NAME|--box NAME        Use box NAME (default: aquarium).
  -s DIR|--setup DIR        Use DIR for setups (default: ${setupdir})
  -h|--help                 This message.
EOF
}

box="aquarium"
setup_name=""

while [[ $# -gt 0 ]]; do

  case $1 in
    -b|--box)
      box="$2"
      shift 1
      ;;
    -s|--setup)
      setupdir="$2"
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "${setup_name}" ]]; then
        setup_name="$1"
      else
        echo "error: unrecognized argument: '$1'"
        usage
        exit 1
      fi
      ;;
  esac
  shift 1
done

[[ -z "${setup_name}" ]] && \
  echo "error: must provide name to setup" && \
  usage && \
  exit 1

[[ -z "${box}" ]] && \
  echo "error: box not specified" && \
  usage && \
  exit 1

[[ -z "${setupdir}" ]] && \
  echo "error: setup directory not specified" && \
  usage && \
  exit 1

[[ -e "${setupdir}/${setup_name}" ]] && \
  echo "error: setup with name '${setup_name} already exists" && \
  exit 1


if ! vagrant box list | grep -q "^${box}[ ]\+" ; then
  echo "=> vagrant box '${box}' not found, searching for existing build"

  imgdir=$(realpath ${basedir}/../../images)

  [[ ! -e "${imgdir}" ]] && \
    echo "error: unable to find images directory" && \
    exit 1

  [[ ! -e "${imgdir}/build" ]] && \
    echo "error: unable to find images build directory" && \
    exit 1

  [[ ! -e "${imgdir}/build/${box}" ]] && \
    echo "error: unable to find build directory for '${box}'" && \
    exit 1

  img=$(ls ${imgdir}/build/${box}/_out/*.vagrant.libvirt.box 2>/dev/null)
  [[ -z "${img}" ]] && \
    echo "error: unable to find vagrant libvirt image for '${box}'" && \
    exit 1

  vagrant box add ${box} ${img} || exit 1
fi

sdir=${setupdir}/${setup_name}
mkdir -p ${sdir} || exit 1
echo "=> writing Vagrantfile to ${sdir}/Vagrantfile"

rootdir="$(realpath ${basedir}/../../)"

cat ${basedir}/Vagrantfile.tmpl | \
  sed "s/{{BOXNAME}}/${box}/" | \
  sed "s|{{ROOTDIR}}|${rootdir}|" > ${sdir}/Vagrantfile

echo "-- You can now head to ${sdir} and run 'vagrant up'"

