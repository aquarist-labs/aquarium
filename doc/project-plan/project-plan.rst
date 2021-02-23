.. _aquarium-project-plan:

======================
Aquarium Project Plan
======================

Project Scope
~~~~~~~~~~~~~

Aquarist Labs is an organization of like-minded individuals working on
the Aquarium project.

The scope of Aquarist Labs is to investigate the beginnings of an opinionated
new storage appliance project in an collaborative fashion. This includes the planning,
design, development, testing and successful public release of a new project.

The Aquarium project aims to develop a standalone Ceph-based storage appliance.

The scope of this project also includes measuring successful external user adoption
based on feedback, issues, downloads, GitHub stars, project telemetry, testing, and documentation.
The Aquarium project is split into two development work streams: Gravel
(backend) and Glass (frontend). Other work items include documentation and social media communication.

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
user. This complexity stems from Ceph's flexibility that supports a huge
matrix of use cases and the effects this has on available capacity,
performance and thus availability.

All current management tooling deploys Ceph bottom-up, i.e. the user must
specify deployment patterns at the daemon level, create pools and crushmaps
(which encode various availability and performance requirements) and only
then can a user deploy their workload.

This project should also explore if other user interface abstractions are
practical and ultimately an improvement. The goal should be simplification
where a user is not required to configure individual daemons or disk layouts,
but can provide a high level specification of what they want (in terms of
availability, usable capacity, ...?)  and a piece of code translates that
to a deployment layout. Whether this deployment layout can be set up on the
current hardware can be determined by software and the user can be provided
with the feedback (be it positive or negative).

Project Vision
~~~~~~~~~~~~~~

The Aquarium project is designed to deliver a Ceph-based appliance for
enterprise, built on on industry standard scripts, tools, and frameworks
(lightweight, modern CI, lightweight build system, etc.).

Aquarium is the following:

- Built on Ceph
- Installation capabilities on any Linux distribution
- Support major storage protocols: iSCSI, NFS and S3
- Horizontal scalability, HA, failover, iSCSI multipath
- New UI and installer
- Quality Management
- Testing

Quality Management
~~~~~~~~~~~~~~~~~~

Project quality is ensured by light-weight, modern CI/CD tools that automatically validate builds. The project team will also prioritize user feedback on quality over features. This will be refined in future milestones.

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
         - Demonstration to internal stakeholders
         - Multi-node deploy
         - Introduce CI/CD, testing, and documentation to support multi-node deploy
     - March 17, 2021
   * - Milestone 3
     -
         - Announce Aquarist Labs publicly
     - April 17, 2021
