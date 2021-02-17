#!/bin/bash

SCRIPT_NAME=$(basename ${BASH_SOURCE[0]})
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if ! which uvicorn >&/dev/null ; then
  echo "unable to find uvicorn in path"
  exit 1
fi

pushd src &>/dev/null
AQUARIUM_CONFIG_DIR=${SCRIPT_DIR}/conf DEBUG=1 uvicorn aquarium:app --host 0.0.0.0 --port 1337
popd &>/dev/null
