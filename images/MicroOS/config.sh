#!/bin/bash
# Copyright (c) 2021 SUSE LLC
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
# prepare for setting root pw, timezone
#--------------------------------------
echo "** reset machine settings"
rm -f /etc/machine-id \
      /var/lib/zypp/AnonymousUniqueId \
      /var/lib/systemd/random-seed \
      /var/lib/dbus/machine-id

#======================================
# MicroOS removed - Setup baseproduct link
#--------------------------------------
# suseSetupProduct


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

#======================================
# MicroOS added - Adjust zypp conf
#--------------------------------------
sed -i 's/^multiversion =.*/multiversion =/g' /etc/zypp/zypp.conf


#=====================================
# MircoOS added - Configure snapper
#-------------------------------------
if [ "${kiwi_btrfs_root_is_snapshot-false}" = 'true' ]; then
	echo "creating initial snapper config ..."
	cp /etc/snapper/config-templates/default /etc/snapper/configs/root
	baseUpdateSysConfig /etc/sysconfig/snapper SNAPPER_CONFIGS root

	# Adjust parameters
	sed -i'' 's/^TIMELINE_CREATE=.*$/TIMELINE_CREATE="no"/g' /etc/snapper/configs/root
	sed -i'' 's/^NUMBER_LIMIT=.*$/NUMBER_LIMIT="2-10"/g' /etc/snapper/configs/root
	sed -i'' 's/^NUMBER_LIMIT_IMPORTANT=.*$/NUMBER_LIMIT_IMPORTANT="4-10"/g' /etc/snapper/configs/root
fi

#=====================================
# Enable chrony if installed
#-------------------------------------
if [ -f /etc/chrony.conf ]; then
	suseInsertService chronyd
fi

#=====================================
# MircoOS added - fstab overlay hack
#-------------------------------------
# The %post script can't edit /etc/fstab sys due to https://github.com/OSInside/kiwi/issues/945
# so use the kiwi custom hack
cat >/etc/fstab.script <<"EOF"
#!/bin/sh
set -eux

/usr/sbin/setup-fstab-for-overlayfs
# If /var is on a different partition than /...
if [ "$(findmnt -snT / -o SOURCE)" != "$(findmnt -snT /var -o SOURCE)" ]; then
	# ... set options for autoexpanding /var
	gawk -i inplace '$2 == "/var" { $4 = $4",x-growpart.grow,x-systemd.growfs" } { print $0 }' /etc/fstab
fi
EOF


#=====================================
# MircoOS added - ONIE additions
#-------------------------------------
if [[ "$kiwi_profiles" == *"onie"* ]]; then
	systemctl enable onie-adjust-boottype
	# For testing:
	echo root:linux | chpasswd
	systemctl enable salt-minion

	cat >>/etc/fstab.script <<"EOF"
# Grow the root filesystem. / is mounted read-only, so use /var instead.
gawk -i inplace '$2 == "/var" { $4 = $4",x-growpart.grow,x-systemd.growfs" } { print $0 }' /etc/fstab
# Remove the entry for the EFI partition
gawk -i inplace '$2 != "/boot/efi"' /etc/fstab
EOF
fi

#=====================================
# MircoOS added - fstab finish
#-------------------------------------
chmod a+x /etc/fstab.script

#=====================================
# MircoOS added - Enable growfs
#-------------------------------------
# To make x-systemd.growfs work from inside the initrd
cat >/etc/dracut.conf.d/50-microos-growfs.conf <<"EOF"
install_items+=" /usr/lib/systemd/systemd-growfs "
EOF

#=====================================
# MircoOS added - container enable btrfs 
#-------------------------------------
# Use the btrfs storage driver. This is usually detected in %post, but with kiwi
# that happens outside of the final FS.
if [ -e /etc/containers/storage.conf ]; then
	sed -i 's/driver = "overlay"/driver = "btrfs"/g' /etc/containers/storage.conf
fi

#======================================
# MircoOS added - zypper set onlyRequires
# Disable recommends on virtual images (keep hardware supplements, see
# https://bugzilla.suse.com/show_bug.cgi?id=1089498
#--------------------------------------
sed -i 's/.*solver.onlyRequires.*/solver.onlyRequires = true/g' /etc/zypp/zypp.conf

#======================================
# MicroOS added - Remove documentation
#--------------------------------------
sed -i 's/.*rpm.install.excludedocs.*/rpm.install.excludedocs = yes/g' /etc/zypp/zypp.conf

#======================================
# MicroOS added - Remove documentation
# Workaround: Force network-legacy, network-wicked is not usable, see
# https://bugzilla.suse.com/show_bug.cgi?id=1182227
#--------------------------------------
if rpm -q ignition-dracut-grub2; then
	# Modify module-setup.sh, but undo the modification on the first call
	mv /usr/lib/dracut/modules.d/40network/module-setup.sh{,.orig}
	sed 's#echo "kernel-network-modules $network_handler"$#echo kernel-network-modules network-legacy; mv /usr/lib/dracut/modules.d/40network/module-setup.sh{.orig,}#' \
		/usr/lib/dracut/modules.d/40network/module-setup.sh.orig > /usr/lib/dracut/modules.d/40network/module-setup.sh
fi


#======================================
# MicroOS added - Configure Pine64 
#--------------------------------------
if [[ "$kiwi_profiles" == *"Pine64"* ]]; then
	echo 'add_drivers+=" fixed sunxi-mmc axp20x-regulator axp20x-rsb "' > /etc/dracut.conf.d/sunxi_modules.conf
fi

#======================================
# MicroOS added - Configure Raspberry Pi
# on TW it is done by raspberrypi-firmware
#--------------------------------------
if [[ "$kiwi_profiles" == *"RaspberryPi"* ]] && ! [[ -e /usr/lib/dracut/dracut.conf.d/raspberrypi_modules.conf ]]; then
	# Add necessary kernel modules to initrd see 
	# https://bugzilla.suse.com/show_bug.cgi?id=1084272
	echo 'add_drivers+=" bcm2835_dma dwc2 "' > /etc/dracut.conf.d/raspberrypi_modules.conf

	# Add necessary kernel modules to initrd 
	# https://bugzilla.suse.com/show_bug.cgi?id=1162669
	echo 'add_drivers+=" pcie-brcmstb "' >> /etc/dracut.conf.d/raspberrypi_modules.conf

	# Work around network issues
  	cat > /etc/modprobe.d/50-rpi3.conf <<-EOF
		# Prevent too many page allocations (bsc#1012449)
		options smsc95xx turbo_mode=N
	EOF

	cat > /usr/lib/sysctl.d/50-rpi3.conf <<-EOF
		# Avoid running out of DMA pages for smsc95xx (bsc#1012449)
		vm.min_free_kbytes = 2048
	EOF
fi

#======================================
# Configure Vagrant specifics
#--------------------------------------
if [[ "$kiwi_profiles" == *"Vagrant"* ]]; then
	# insert the default insecure ssh key from here:
	# https://github.com/hashicorp/vagrant/blob/master/keys/vagrant.pub
	baseVagrantSetup
fi

pip install fastapi==0.63.0 uvicorn==0.13.3 websockets==8.1 \
    bcrypt==3.2.0 pyjwt==2.1.0 python-multipart==0.0.5 \
    git+https://github.com/aquarist-labs/aetcd3/@edf633045ce61c7bbac4d4a6ca15b14f8acfe9cd

#======================================
# Activate services
#--------------------------------------
baseInsertService sshd
baseInsertService aquarium
baseInsertService update_motd
baseInsertService aquarium-boot

exit 0
