#!/bin/bash

usage() {
  cat << EOF
usage: $0 [options]

options:
  -n NAME | --name NAME     Specify build name (default: aquarium).
  -h | --help               This message.
EOF

}

build_name="aquarium"

while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--name)
      build_name=$2
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

if ! which kiwi-ng &>/dev/null ; then
  echo "error: missing kiwi-ng"
  exit 1
fi

build=build/${build_name}

if [[ -e "${build}" ]]; then
  echo "error: build with name '${build_name}' already exists"
  exit 1
fi

set -xe

mkdir -p ${build}

cp microOS/config.{sh,xml} ${build}/

mkdir ${build}/{_out,_logs}
sudo kiwi-ng --debug --profile=Ceph-Vagrant --type oem \
  system build --description $(pwd)/${build} \
  --target-dir $(pwd)/${build}/_out |\
  tee $(pwd)/${build}/_logs/${build_name}-build.log

