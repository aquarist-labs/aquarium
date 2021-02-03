======================
Aquariums Project Plan
======================

Project Scope
~~~~~~~~~~~~~

Aquarist Labs are an organization of like-minded individuals working on
the Aquariums project. 

The scope of Aquarist Labs is to investigate the beginnings of a new storage
appliance project in an opinionated fashion. This includes the planning,
design, development, testing and successful public release of a new project.

The Aquariums project is a new project developed by SUSE engineers to develop
a new storage appliance. Aquariums is initially designed to be a standalone
project, and not at all related to the SUSE product, SUSE Enterprise Storage.

The scope of this project also includes successful external user adoption
based on GitHub stars, testing, and documentation. The Aquariums project is
split into two clearly defined work streams: Gravel (backend) and Glass
(frontend). 

Project Success Metrics
-----------------------

The goal is to launch a minimally viable project within 4 months (see
`Milestones`_ below for more details).

This means the project will not be feature complete, but a showcase of the
concept, "open source storage appliance powered by Ceph".

Project completion is relative to the success of the project's adoption at
this time.

User Story
~~~~~~~~~~

Currently, the perception is that Ceph is too complex to use for the average
user. This complexity stems from ceph's flexibility that supports a huge
matrix of use cases and the effects this has on available capacity,
performance and thus availability. At least partially this perceived complexity
can also be blamed on the current user interface abstraction.

All current management tooling deploys ceph bottom-up, i.e. the user must
specify deployment patterns at the daemon level, create pools and crushmaps
(which encode various availability and performance requirements) and only
then can a user deploy their workload.

This project should also explore if other user interface abstractions are
practical and ultimately an improvement. The goal should be simplification
where a user is not required to configure individual daemons or disk layouts,
but can provide a high level specification of what they want (in terms of
availability, usable capacity, ...?)  and a piece of code translates that
to a deployment layout. Whether this deployment layout can be set up on the
current hardware can be determined by software and the user can be provided
with the feedback (be it positive or negative).

Project Vision
~~~~~~~~~~~~~~

The Aquariums project is designed to deliver FreeNAS for enterprise,
built on on industry standard scripts, tools, and frameworks (lightweight,
modern CI, no OBS, etc.) as an open source alternative to NetApp and EMC.

Aquariums has the following:

- Built on Ceph
- Installation capabilities on any Linux distribution
- Support major storage protocols: iSCSI, NFS and S3
- Horizontal scalability, HA, failover, iSCSI multipath
- New UI and installer
- Quality Management
- Testing

Quality Management
~~~~~~~~~~~~~~~~~~

Testing

Risk Management 
~~~~~~~~~~~~~~~

Identify risks and ensure team members monitor the risks associated with them.

Milestones
~~~~~~~~~~

.. list-table::
   :widths: 35 35 25
   :header-rows: 1

   * - Milestone
     - Description
     - Due Date
   * - Milestone 1
     -
         - "Early dev on-boarding edition"
         - Goal: everyone can easily build and install their build.
         - Single node deploy
         - Introduce sufficient CI/CD, testing, and documentation to support single node deploy
     - February 17, 2021
   * - Milestone 2
     -
         - Demonstration to Sheng
         - Multi-node deploy
         - Introduce CI/CD, testing, and documentation to support multi-node deploy
     - March 17, 2021
   * - Milestone 3
     -
         - Announce Aquarist Labs publicly
     - April 17, 2021

Communication Management Plan
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 15 45 10 10 10 10
   :header-rows: 1

   * - Communicate Type
     - Description
     - Frequency
     - Format
     - Distribution
     - Owner
   * - Team meeetings
     -
         - Weekly meeting (x3 per timezone) to discuss Aquarist Labs.
         - This includes meeting minutes that are regularly sent to the mailing list.
     - Weekly
     - Teams
     - ceph@suse.de
     - asettle@suse.com
   * - Chat
     -
         - Public communication channels
     - Daily
     - TBD
     - TBD
     - TBD
   * - Social media
     -
         - Blogs?
         - Twitter?
     - TBD
     - TBD
     - TBD
     - TBD
   * - Announcements
     -
         - Milestone 1 announcement
         - Website changes
         - Social media announcements
     - Monthly
     -
         - Email?
         - GitHub discussions
     - TBD
     -
         - asettle@suse.com
         - larsmb@suse.com
