#!/bin/bash
#
# Aquarium image kiwi scripts
# Copyright (C) 2021 SUSE LLC
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

set -euxo pipefail

if ! /usr/bin/podman --version >/dev/null ; then
  echo "ERROR: can't find podman"
  exit 1
fi

if ! /usr/sbin/cephadm --help >/dev/null ; then
  echo "ERROR: can't find cephadm"
  exit 1
fi


mkdir /var/lib/containers
# we need nameservers to resolve the names for podman
echo "nameserver 1.1.1.1" > /etc/resolv.conf

# and we need a basic running system too
mount -t sysfs none /sys
mount -t devtmpfs none /dev
mount -t tmpfs none /dev/shm
mount -t proc none /proc
mount -t tmpfs none /run

# setting "--events-backend none" means podman doesn't try
# (and fail) to log a "system refresh" event to the journal
/usr/bin/podman --events-backend none pull quay.io/coreos/etcd:latest
# we don't get to use cephadm directly because it will
# try running a container inside the chroot, and that
# fails with a bang.
/usr/bin/podman --events-backend none pull docker.io/ceph/ceph:v16

# cleanup
umount /run
umount /proc
umount /dev/shm
umount /dev
umount /sys
rm /etc/resolv.conf

exit 0
