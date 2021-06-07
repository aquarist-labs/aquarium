# Aquarium systemd boot process

## aquarium-boot

`systemd` unit that will be running after `local-fs.target`, runs
`/usr/share/aquarium/boot/aqrbootsetup.sh`, which tries to find an LVM disk
tagged with `@aquarium`. If such a disk is found, the disk will be mounted in
`/aquarium` and several operation critical directories will either be overlayed
over existing system directories, or bind mounted to specific places.

### Overlayed directories

These are

* `/etc`, so we can keep track of system configuration files that were changed
  for Aquarium's operations. This includes Ceph's systemd unit files.

* `/var/log`, so logs are persisted between runs.

* `/var/lib/etcd`, where we keep this node's etcd persistent db.

* `/var/lib/containers`, where container images are kept.

### Bind mounted directories

* `/var/lib/ceph`, where we'll keep Ceph's persistent data. This directory
  cannot be overlayed, because overlaying causes Ceph to misbehave. Reasons
  unknown.
  
### Known issues

Unfortunately we have been unable to ensure we overlay `/etc` at a time before
`systemd` reads the contents of `/etc/systemd`. Therefore, we are overlaying
`/etc` contents after systemd already has a list of units to be started. This
means that the Ceph units are not started automatically during boot, because
from `systemd`'s point of view they did not exist when it looked for them.

This means the onus of starting the `ceph.target` falls on Aquarium.


## aquarium

`systemd` unit that will be running after `network.target`, runs Aquarium from
`/usr/lib/share/aquarium`.

