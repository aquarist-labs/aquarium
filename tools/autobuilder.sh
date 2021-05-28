#!/bin/bash
#
# project aquarium's container builder
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

build_prefix_name=${BUILDNAME}
outdir=${OUTDIR:-"/builder/out"}
srcdir=${SRCDIR:-"/builder/src"}
bindir=${BINDIR:-"/builder/bin"}
cachedir=${CACHEDIR:-"/builder/cache"}


[[ ! -d "${outdir}" ]] && \
  echo "error: outdir does not exist at '${outdir}'" >/dev/stderr && \
  exit 1

[[ ! -d "${srcdir}" ]] && \
  echo "error: srcdir does not exist at '${srcdir}'" >/dev/stderr && \
  exit 1

[[ ! -d "${bindir}" ]] && \
  echo "error: bindir does not exist at '${bindir}'" >/dev/stderr && \
  exit 1

[[ ! -d "${cachedir}" ]] && \
  echo "error: cachedir does not exist at '${cachedir}'" >/dev/stderr && \
  exit 1

[[ -z "${build_prefix_name}" ]] && \
  build_prefix_name=$(git -C ${srcdir} rev-parse --abbrev-ref HEAD)

[[ -z "${build_prefix_name}" ]] && build_prefix_name="noname"

build_prefix="aqr-${build_prefix_name}-"
build_date=$(date +%Y%m%d)
existing_builds=$((ls -d ${outdir}/${build_prefix}${build_date}.*) 2>/dev/null)

lowest_n=0
res=( $(echo $(for i in ${existing_builds} ; do
        n=$(basename $i)
        echo $i | cut -f2 -d'.' ;
      done) | sort -n) )
for i in ${res[*]}; do
  j=$(( i + 0))
  [[ $j -gt $lowest_n ]] && lowest_n=$j
done

echo $lowest_n
next_n=$((lowest_n + 1))
[[ $next_n -lt 10 ]] && next_n="0${next_n}"
build_name="${build_prefix}${build_date}.${next_n}"

[[ -n "${DRY}" ]] && \
  echo "build_name: ${build_name}" && \
  exit 0

${bindir}/build-image.sh -n ${build_name} \
  --rootdir ${srcdir} \
  --buildsdir ${outdir} \
  --cachedir ${cachedir} || exit 1
