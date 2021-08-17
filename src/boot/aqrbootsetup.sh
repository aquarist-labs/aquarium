#!/bin/bash
#
# project aquarium's boot setup
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


function overlay() {
  lower=${1}
  upper=${2}

  [[ ! -d "${lower}" ]] && mkdir -p ${lower}

  aqrdir=/aquarium/${upper}
  mount -t overlay \
    -o lowerdir=${lower},upperdir=${aqrdir}/overlay,workdir=${aqrdir}/temp \
    overlay ${lower} || return 1
}

systemdisk=$(lvm lvs --noheadings -o vg_name,lv_name @aquarium |
             sed 's/^[ ]\+//' | tr ' ' '-')

[[ -z "${systemdisk}" ]] && \
  echo "Aquarium system disk not found, assuming new deployment" && \
  exit 0

[[ "${systemdisk}" != "aquarium-systemdisk" ]] && \
  echo "Unknown system disk, expected aquarium-systemdisk" >/dev/stderr && \
  exit 1

[[ ! -d "/aquarium" ]] && \
  (mkdir /aquarium || (echo "error creating /aquarium" && exit 1))

[[ ! -e "/dev/mapper/aquarium-systemdisk" ]] && \
  echo "Unable to find aquarium block device" && \
  exit 1

# mount system disk
mount /dev/mapper/aquarium-systemdisk /aquarium

# overlay
overlay /etc etc || exit 1
overlay /var/log logs || exit 1
overlay /var/lib/etcd etcd || exit 1
overlay /var/lib/aquarium aquarium || exit 1
overlay /var/lib/containers containers || exit 1
overlay /root roothome || exit 1

# bind mount
[[ ! -d "/var/lib/ceph" ]] && mkdir -p /var/lib/ceph
mount --bind /aquarium/ceph /var/lib/ceph || exit 1

echo "Aquarium system disk mounted successfully"

# The system obtains its hostname right at the beginning of boot, before disks
# have been mounted or udev and lvm have been setup to allow us to mount them.
# Because of that, let's set up the hostname once we do have the disks mounted.
echo "Setup host from system disk"
hostnamectl set-hostname $(cat /etc/hostname)
