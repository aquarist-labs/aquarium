[comment]: # (Please use the project description to give an overview and updates)
[comment]: # (about the current state of your project)
[comment]: # (Why do you start this project, what's your interest?)

## Project Description

The SUSE Enterprise Storage team has embarked on a new open source project: Aquarium.

Aquarium is our take on an opinionated storage appliance. It is designed to take the fundamentals of Ceph, hide everything that makes it complicated to use, and develop an easy to use, rock solid storage appliance. The project started development in January, and has become a passion project for the team. The project is split into two clearly defined work streams: Gravel (backend) and Glass (frontend).

Currently, we see Ceph as being too complex to use for the average user. This complexity stems from Ceph's flexibility that supports a huge matrix of use cases and the effects this has on available capacity, performance and thus availability.

All current management tooling deploys Ceph bottom-up, i.e. the user must specify deployment patterns at the daemon level, create pools and crushmaps (which encode various availability and performance requirements) and only then can a user deploy their workload.

We are exploring if other user interface abstractions are practical and ultimately an improvement. The goal should be simplification where a user is not required to configure individual daemons or disk layouts, but can provide a high level specification of what they want (in terms of availability, usable capacity, ...?) and a piece of code translates that to a deployment layout. Whether this deployment layout can be set up on the current hardware can be determined by software and the user can be provided with the feedback (be it positive or negative).

## Who can be involved?

Literally, anyone. We're looking for people who are interested in hacking on new projects, or want to learn something new. We're also more than happy to teach *you* about storage if you come from a different knowledge background.

If you consider yourself to be non-technical, but interested in how communities work - we're also looking for people to get involved with the other sides of community management that are not related to code only.

[comment]: # (What are your goals to be achieved at the end of this Hackweek?)

## Goal for this Hackweek

We are currently in Phase 2 (Milestone 2) of the project where we are actively developing how to deploy a multi-node setup. Our goals:

- Testing deployment
- Bug finding/squashing
- And if you like the project, active development! We have a series of issues related to multi-node deployment, and anything you can grab is yours.

If you want to get involved in another way:

- Work on the plans for announcements/communication plan
- Work with the frontend development on UX/UI
- Documentation

[comment]: # (Please link to sources and other data here.)
[comment]: # (Prefer public repositories, such as GitHub!)

## Resources

- Project repo: https://github.com/aquarist-labs/aquarium
- We're on slack: https://join.slack.com/t/aquaristlabs/shared_invite/zt-lsjrkw8m-Jj_zYAs84PfMsUGwvMDOFA
- Check out our [From Zero to Hero](https://github.com/aquarist-labs/aquarium/blob/main/doc/from-zero-to-hero.md)
quickstart to help you get off your feet
- Check out the [issue](https://github.com/aquarist-labs/aquarium/issues) list and our [project board](https://github.com/orgs/aquarist-labs/projects/3)
- Contributing guidelines: https://github.com/aquarist-labs/aquarium/blob/main/CONTRIBUTING.md

[comment]: # (After creating the project, please add some keywords:)
[comment]: # (* What type of project mates are you looking for, which skills do you need or lack?)
[comment]: # (* Which keywords will help other people to find your project?)
