# Host Requirement Assessment

This document describes the basic hardware requirements for a host to
join / deploy a cluster.

## Problem Description

Aquarium's Host Management should assess whether a node meets the
requirements for joining an existing cluster, or to deploy an initial
seed cluster, providing immediate feedback to the user on its
feasibility.

## Proposed Changes

Considering that the requirements depened on a cluster purpose
(production, testing, educational) it seems we have two provide at
least two profiles: "minimal" requirements (enough for Ceph to work),
and "optimal" requirements (to meet user expectations).

In future we might need to have several "optimal" profiles for
different use cases.

## Minimal profile

It is based on Ceph upstream minimum hardware recommendations [^1].

### ceph-osd

- Processor: 1+ core per daemon
- RAM: 4GB+ per daemon (2GB will probably work, but will require
  changing osd_memory_target)
- Volume Storage: 1x 20GB+ storage drive per daemon
- DB/WAL: optional, 1x 10Gb+ SSD partition per daemon
- Network: 1x 1GbE+ NICs

### ceph-mon, ceph-mgr

- Processor: 2+ cores per daemon
- RAM: 2GB+ per daemon
- Disk Space: may be the OS disk, 60GB+ per daemon
- Network: 1x 1GbE+ NICs

### ceph-mds

- Processor: 2+ cores per daemon
- RAM: 2GB+ per daemon
- Disk Space: may be the OS disk, no special requirements
- Network: 1x 1GbE+ NICs

## Optimal profile

It is based both on Ceph upstream hardware recommendations [^2] and SES
hardware requirements and recommendations [^3].

### ceph-osd

- Processor: 4+ core per daemon (1x 2GHz CPU Thread per spinner, 2x
  2GHz CPU Thread per SSD, 4x 2GHz CPU Thread per NVMe)
- RAM: 5GB+ (osd_memory_target + 1GB) per daemon + 16GB+ for OS
- Volume Storage: 1x 1TB+ storage drive per daemon
- DB/WAL: 1x SSD/NVMe 200G+ partition per daemon, not more than six
  WAL/DB partitions on the same SSD disk and 12 on NVMe disks. Not
  needed if the volume storage is SSD.
- Network: two bonded 25 GbE (or faster) network interfaces bonded
  using 802.3ad (LACP)

### ceph-mon, ceph-mgr

- Processor: 4+ cores per daemon
- RAM: 4GB+ per daemon + 16GB+ for OS
- Disk Space: 500GB+ SSD (RAID?) disk/partition for mon db,
  no requirements for ceph-mgr
- Network: two bonded 25 GbE (or faster) network interfaces bonded
  using 802.3ad (LACP)

### ceph-mds

- Processor: 4+ cores per daemon
- RAM: 16GB+ per daemon (for caching) + 16GB+ for OS
- Disk Space: may be the OS disk, no special requirements
- Network: two bonded 25 GbE (or faster) network interfaces bonded
  using 802.3ad (LACP)

## Additional considerations

### Solid State Drives

Some drives are known to behave badly with Ceph. Should we have a
blacklist for optimal profile?

### Controllers

A controller may be a bottleneck. Should we check number of disks per
controller? Topology?

### Write Caches

Usual recommendation is to disable write cache. Should we do this
automatically?

### Networks

Make separate public and cluster network mandatory for optimal
profile? Check for jumbo frames enabled and test network for "large"
package (jumbo frames misconfiguration is a common problem)?

### "Asymmetric" configurations

Mixing hosts with different number of osd disks or disks of different
size is usually a bad idea. Should we allow only "symmetric"
configurations for optimal profile?

### Failure Domains

Should we check the minimum "host" failure domain for the optimal
profile? Number of nodes (at least 4 physical OSD nodes, with 8? OSD
disks each)?

### Log storage

Should we check storage for logs?


[^1]: https://docs.ceph.com/en/latest/start/hardware-recommendations/#minimum-hardware-recommendations
[^2]: https://docs.ceph.com/en/latest/start/hardware-recommendations/
[^3]: https://documentation.suse.com/ses/7/html/ses-all/storage-bp-hwreq.html
