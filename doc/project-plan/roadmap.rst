.. _aquarium-roadmap:

================
Aquarium Roadmap
================

Note Before
------------

- Assuming about 2 person time per team, backend and frontend, to tolerate
  non-exclusive work in Aquarium (e.g., support incidents).
- Attempt to add different work streams, albeit somewhat related, in the 
  backend when work packages seem to be a one-person thing.
- None of this should discourage people from working on other things should
  they have time, get blocked, or `enter reason here`.
- All work packages are being set with Joao rough-estimating effort they
  **might** take.
- All of this meant for discussion, and subject to change.


Milestones
----------

M4
~~~

* Frontend improvement

  * Dashboard

    * Adding new widgets (TBD)

      * Add Capacity (i.e., real usage) widget
      * Show time series delivered by Ceph itself (not Prometheus etc)
      * Change existing widgets

        * Rename "Capacity" to "Allocated"
        * Health message displayed on hover?
    * Backend support for what is required

  * Install Wizard

    * Devices config step (mostly backend, I hope)

* Testing improvements

  * All PRs need unit tests
  * Functional tests to stress the API (against a running cluster)

M5
~~~

* NFS HA (maybe) or RGW

  * Basic service deployment (backend)
  * Service creation (frontend)

* Provision system disk from available devices (backend, frontend)

  * Select system disk (frontend)
  * Partition system disk (backend)
  * Mount system disk (backend)

* User management
* HTTPS support

M6
~~~

* Frontend improvements

  * Dashboard
  
    * Add events widget (frontend)
    
    * Basic event stashing on etcd (backend)
      * node join
      * ???

    * Per-service usage (frontend, backend)

    * Per-host usage (frontend, backend)

  * Install wizard

    * set public / cluster networks step (frontend, backend)

* NFS HA or RGW (see M5 description)

M7
~~~

* Ops

  * Remove node (frontend, backend)

  * Reboot node (presumes working USB stick deployment by now) (frontend, backend)

  * Log these as events

* RBD (single site) (backend, frontend)

M8
~~~

* iSCSI (backend, frontend)

  * Basic support

* Assessment of what is needed further (backend)

  * Assess further by M6?

* LDAP/AD

* SMB/CIFS


THINGS N STUFF
---------------

A list of items brought to you in some unkempt, roughly prioritized order.
  
* Boot from USB stick

  * Specify system disk from available devices (backend, frontend)
  * Partition system disk (backend)
  * Mount system disk (backend)
  
* Test on real hardware

* Ops

  * Adding/removing/replacing/update/force-redeploy nodes, OSDs
  * Up to date status view, nagging, informing about available updates, etc
  * Validating that all clients are ready for the update
  
  * Supportability integration
  
    * Support remote console
    * Support data gathering
  
  * Changing configuration (network?)

* NFS HA
  
  * setup virtual ip (hopefully backend only, maybe frontend needs to be involved?)
  * provide mountpoint with virtual ip (frontend)
  
* Testing all over (frontend, backend)
  
  * Running task, in parallel with everything else
  
* RGW (single site)
  
  * Object service (backend, frontend)
  * Create / Deploy RGW (backend)
  * S3/RGW admin frontend? (User provisioning, mgmt of buckets etc)
  
* RBD (single site)
  
  * Block service (backend, frontend)
  * Create / Deploy RBD pools (backend)
  
* iSCSI (depends on RBD)
  
  * Block service (backend, frontend)
  * Create / Deploy iscsi targets, rely on RBD (backend)
  
* Frontend improvement
  
  * Obtain cluster events (backend)
  
    * Store them in etcd?
    * Mutual exclusion access to ceph cluster operations
  
  * Dashboard
  
    * Add new information to be displayed (frontend, backend)
    * Rename "Capacity" to "Allocated"
    * Add Capacity (i.e., real usage) widget
    * Health message displayed on hover?

    * Events widget

      * Figure out what is an event (backend)
      * Figure out how to display Ceph status updates as events (backend)
      * Store events in etcd (backend)
      * Display events (frontend)

    * Hosts

      * Per-host utilization (cpu, ram) (frontend, backend)
      * Per-host used space (frontend, backend)

    * Logs

      * Obtain logs endpoint (backend)
      * Obtain logs for each node (frontend, backend)
      * Obtain all logs (frontend, backend)

      * Likely rely on etcd to do keep obtained logs from all nodes (backend)

        * or on websockets to connect to each node and obtain those logs?

      * TGZ logs (backend)

    * Services

      * Per-service usage (frontend)

    * Install Wizard

      * Host config step

        * set hostname (backend, frontend)
        * setup password for 'aquarium' user (backend, frontend)

      * Network config step

        * set front and back networks (backend, frontend)

      * Devices config step (related to 'Boot from USB Stick')

        * obtain devices from host inventory (frontend, backend)  
        * choose devices per function (system, storage, none)

      * Pre-bootstrap Summary (Things we're about to do) (frontend)
  
* Scripted deploy for unattended provisioning of new clusters or ops

* Backup/restore
  
* Multi-site - S3, RBD, CephFS ...
  
* Resource constrains solver
  
  * This is the kind of thing we REALLY need to be thinking about how to achieve
  
* Soft to Hard quotas on service allocations
  
* Recommended Hardware specification

  * oof
  * Hardware allow/deny list support
  * Possibly sourcing from device telemetry data?
  
* Benchmark cluster (frontend, backend)

  * networking
  * disks
  * specific pools?
  * Client code?
  * Calibration of achievable performance
  
* Telemetry
  
  * Enabling/disabling Ceph telemetry
  * Inclusion of Aquarium specific telemetry/feedback
  * Adoption, config choices, etc
