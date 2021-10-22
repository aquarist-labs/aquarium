#!/bin/bash

SCRIPT_NAME=$(basename ${BASH_SOURCE[0]})
AQUARIUM_DIR=${AQUARIUM_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." ; echo $PWD)}
VENV_DIR=${AQUARIUM_DIR}/venv

usage() {
  cat <<EOF
usage: ${SCRIPT_NAME} [options]

options:
  -d|--debug          Enable debug logging to stdout
  -c|--config PATH    Set config directory to PATH
  -n|--new            Run as new deployment; blows config path if it exists
  -p|--port           Bind to a socket with this port
  --use-venv          Run inside a python virtualenv
  -h|--help           This message

EOF
}

is_debug=false
has_config=false
config_path=""
is_new=false
with_systemdeps=true
port=80

while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--debug) is_debug=true ;;
    -c|--config) has_config=true ; config_path=$2 ; shift 1 ;;
    -n|--new) is_new=true ;;
    -p|--port) port=$2 ; shift 1 ;;
    --use-venv) with_systemdeps=false ;;
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

if [ -n "${config_path}" ]; then
  config_path=$(realpath ${config_path})
fi

$has_config && $is_new && [[ -e "${config_path}" ]] && \
  ( rm -fr ${config_path} || exit 1 )

if [ -z "${port}" ]; then
  echo "error: must specify a port with '--port'" && \
  exit 1
fi

if ! $with_systemdeps ; then
  # We need system site packages because librados python bindings are only
  # available as a package, they're not on pypi (and Tim thinks they probably
  # never will be).
  # However, if we set --system-site-packages on creation, the required
  # dependencies may not be installed properly if they already exist in the
  # developers environment.
  # Instead, first create an isolated venv, install the requirements, then
  # enable system packages for future venv activations.
  # This will ensure if someone uses it inside the image, they will be able
  # to fall back to system packages to get librados.
  python3 -m venv ${VENV_DIR} || exit 1
  source ${VENV_DIR}/bin/activate || exit $?
  pip install -r ${AQUARIUM_DIR}/src/requirements.txt || exit $?
  deactivate
  sed -i 's/include-system-site-packages = false/include-system-site-packages = true/g' venv/pyvenv.cfg
  source ${VENV_DIR}/bin/activate || exit $?
fi

pushd ${AQUARIUM_DIR}/src &>/dev/null

$is_debug && export AQUARIUM_DEBUG=1
$has_config && export AQUARIUM_CONFIG_DIR=${config_path}

uvicorn aquarium:app_factory --factory --host 0.0.0.0 --port ${port}

popd &>/dev/null

if ! $with_systemdeps ; then
  deactivate
fi
