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

FROM registry.opensuse.org/opensuse/leap:15.3
LABEL aquarium.image.author="Joao Eduardo Luis <joao@suse.com>"
LABEL aquarium.url="https://aquarist-labs.io"
LABEL aquarium.github="https://github.com/aquarist-labs/aquarium"
LABEL version="0.1.0"
LABEL description="Aquarium image builder"

# Use the latest Kiwi version.
RUN zypper ar --repo http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/openSUSE_Leap_15.3/Virtualization:Appliances:Builder.repo

RUN zypper --gpg-auto-import-keys ref
RUN zypper --non-interactive install \
  git python3 python3-pip python3-rados \
  python3-kiwi nodejs-common npm \
  sudo which gptfdisk kpartx dosfstools e2fsprogs \
  make qemu-tools xfsprogs btrfsprogs


RUN mkdir -p /builder/{cache,bin,src,out}
VOLUME [ "/builder/cache", "/builder/bin", "/builder/src", "/builder/out" ]

ENTRYPOINT [ "/builder/bin/autobuilder.sh" ]

