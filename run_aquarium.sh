#!/bin/bash

if ! which uvicorn >&/dev/null ; then
  echo "unable to find uvicorn in path"
  exit 1
fi

pushd src &>/dev/null
uvicorn aquarium:app --host 0.0.0.0 --port 1337
popd &>/dev/null