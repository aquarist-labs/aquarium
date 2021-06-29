#!/bin/bash

# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

cat > /etc/sysconfig/network/ifcfg-${INTERFACE} << EOF
BOOTPROTO='dhcp'
MTU=''
REMOTE_IPADDR=''
STARTMODE='onboot'
EOF

