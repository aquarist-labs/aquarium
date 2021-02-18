#!/bin/bash

SCRIPT_NAME=$(basename ${BASH_SOURCE[0]})
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

usage() {
  cat <<EOF
usage: ${SCRIPT_NAME} [options]

options:
  -d|--debug        Enable debug logging to stdout
  -c|--config PATH  Set config directory to PATH
  -n|--new          Run as new deployment; blows config path if it exists
  -h|--help         This message

EOF
}

is_debug=false
has_config=false
config_path=""
is_new=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--debug) is_debug=true ;;
    -c|--config) has_config=true ; config_path=$2 ; shift 1 ;;
    -n|--new) is_new=true ;;
    -h|--help) usage ; exit 0 ;;
    *)
      echo "error: unknown option '${1}'"
      exit 1
      ;;
  esac
  shift 1
done

if ! which uvicorn >&/dev/null ; then
  echo "error: unable to find uvicorn in path"
  exit 1
fi

$has_config && [[ -z "${config_path}" ]] && \
  echo "error: must specify a PATH with '--config'" && \
  exit 1

config_path=$(realpath ${config_path})

$has_config && $is_new && [[ -e "${config_path}" ]] && \
  ( rm -fr ${config_path} || exit 1 )


pushd src &>/dev/null

$is_debug && export AQUARIUM_DEBUG=1
$has_config && export AQUARIUM_CONFIG_DIR=${config_path}

uvicorn aquarium:app --host 0.0.0.0 --port 1337

popd &>/dev/null
