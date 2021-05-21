# Project Aquarium

![Website](https://img.shields.io/website?down_color=lightgrey&down_message=offline&up_color=green&up_message=online&url=https%3A%2F%2Faquarist-labs.github.io%2F)

![GitHub Repo stars](https://img.shields.io/github/stars/aquarist-labs/aquarium?style=social)

[![codecov](https://codecov.io/gh/aquarist-labs/aquarium/branch/main/graph/badge.svg?token=OX91ZNINML)](https://codecov.io/gh/aquarist-labs/aquarium) ![GitHub last commit](https://img.shields.io/github/last-commit/aquarist-labs/aquarium) ![Lines of code](https://img.shields.io/tokei/lines/github/aquarist-labs/aquarium) ![GitHub contributors](https://img.shields.io/github/contributors/aquarist-labs/aquarium) ![GitHub issues](https://img.shields.io/github/issues/aquarist-labs/aquarium) ![GitHub milestones](https://img.shields.io/github/milestones/all/aquarist-labs/aquarium)

Project Aquarium is a SUSE-sponsored open source project aiming at becoming an easy to use, rock solid storage appliance based on Ceph.

We are investigating the beginnings of a new storage appliance project in an opinionated fashion. The Aquarium project is split into two clearly defined work streams: Gravel (backend) and Glass (frontend).

Aquarist Labs is licensed under LGPL version 2.1. We do not require assignment of a copyright to contribute code; code is contributed under the terms of the applicable license.

## How do I get started?

Look at the [issue](https://github.com/aquarist-labs/aquarium/issues) list or
check out our Slack channel (see below) and ask one of the friendly contributors.
You can also view our [project board](https://github.com/orgs/aquarist-labs/projects/3)
and check our [Review Guidelines](CONTRIBUTING.md).

If you want to get your hands dirty as soon as possible, you can also run the
script at `tools/setup-dev.sh`. This will ensure you have a basic development
environment as soon as possible so you can start hacking.

You will be able to find the backend bits in `src/gravel`, while the frontend
bits are located in `src/glass`.

For i18n translation contribution please take a look at [Translator Guide](https://github.com/aquarist-labs/aquarium/blob/main/doc/i18n.md)

Check out our [From Zero to Hacking](https://github.com/aquarist-labs/aquarium/blob/main/doc/from-zero-to-hacking.md)
quickstart to help you get off your feet.

## Where can I get more help, if I need it?

Join us on Slack! You can sign up [here](https://join.slack.com/t/aquaristlabs/shared_invite/zt-lsjrkw8m-Jj_zYAs84PfMsUGwvMDOFA).

We have the following channels:

- #announcements: For all announcements related to Aquarist Labs and the Aquarium project
- #aquarium: For all conversation and questions surrounding the Aquarium project
- #general: Show us your best gif!
- #github-notifications: Notifications from the [github app](https://slack.github.com/).

If you have a new idea, or want to discuss any implementation details, we recommend using our [Discussion page](https://github.com/aquarist-labs/forum/discussions) on GitHub.

## Checking out the source

You can clone from github with

	git clone git@github.com:aquarist-labs/aquarium

or, if you are not a github user,

	git clone git://github.com/aquarist-labs/aquarium
