#!/bin/bash
# Copyright (c) 2020 SUSE LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#======================================
# Functions...
#--------------------------------------

test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

set -euxo pipefail

echo "Configure image: [$kiwi_iname]-[$kiwi_profiles]..."

#======================================
# Setup baseproduct link
#--------------------------------------
suseSetupProduct

#======================================
# Activate services
#--------------------------------------
suseInsertService sshd
suseInsertService aquarium

#======================================
# Specify default systemd target
#--------------------------------------
baseSetRunlevel multi-user.target

#======================================
# Import trusted rpm keys
#--------------------------------------
suseImportBuildKey

#======================================
# Set hostname by DHCP
#--------------------------------------
baseUpdateSysConfig /etc/sysconfig/network/dhcp DHCLIENT_SET_HOSTNAME yes

# Add repos from /etc/YaST2/control.xml
if [ -x /usr/sbin/add-yast-repos ]; then
	add-yast-repos
	zypper --non-interactive rm -u live-add-yast-repos
fi

#=====================================
# Enable chrony if installed
#-------------------------------------
if [ -f /etc/chrony.conf ]; then
	suseInsertService chronyd
fi


#======================================
# Configure Vagrant specifics
#--------------------------------------
if [[ "$kiwi_profiles" == *"Vagrant"* ]]; then
	# insert the default insecure ssh key from here:
	# https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub
	mkdir -p /home/vagrant/.ssh/
	echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key" > /home/vagrant/.ssh/authorized_keys
	chmod 0600 /home/vagrant/.ssh/authorized_keys
	chown -R vagrant:vagrant /home/vagrant/
	# recommended ssh settings for vagrant boxes
	echo "UseDNS no" >> /etc/ssh/sshd_config
	echo "GSSAPIAuthentication no" >> /etc/ssh/sshd_config

	# vagrant assumes that it can sudo without a password
	# => add the vagrant user to the sudoers list
	SUDOERS_LINE="vagrant ALL=(ALL) NOPASSWD: ALL"
	if [ -d /etc/sudoers.d ]; then
		echo "$SUDOERS_LINE" >| /etc/sudoers.d/vagrant
		visudo -cf /etc/sudoers.d/vagrant
		chmod 0440 /etc/sudoers.d/vagrant
	else
		echo "$SUDOERS_LINE" >> /etc/sudoers
		visudo -cf /etc/sudoers
	fi

	# the default shared folder
	mkdir -p /vagrant
	chown -R vagrant:vagrant /vagrant
fi
baseInsertService sshd

pip install fastapi uvicorn

exit 0

