=========
Objective
=========

To have sufficient, stable, fast, and accurate testing of aquarium.

We do not need to test ceph's functionality or performance itself. Upstream
ceph tests should either be sufficient in this regard or expanded upon.

Our primary scope is Aquarium. That is, we want to ensure aquarium does the
right things, makes the right/expected decisions, and executes the orchestrated
plan as expected. We also want to test the integration between Aquarium, the
host OS, Ceph, and any other services (etcd for example) to ensure that the
deployment and operation of such services is functional and works with
Aquarium's directives (ie, opinionated configuration).

Other goals:
 * To be as fast as possible. Nobody likes slow tests.
 * To be ran pre-commit and on pull request. (Avoid breaking master).
 * Be rock solid. We can't have flaky tests.
 * Provide useful feedback during failures for debugging.
 * Be easy to access and diagnose (eg good logging and reporting etc).

================
Testing approach
================

There are many differing definitions of tests, so these may not be entirely
accurate or what you've seen elsewhere. Below is an attempt to explain the
general expectation of each type and its purpose.

The primary part here though is to focus on what we *should* be testing.

Unit/Integration Tests
----------------------

A unit test should verify that new functions perform as expected. Integration
tests should confirm that the new functions interact with the rest of the
application correctly.

We write unit and integration tests for all of our backend (ie gravel/python)
code. Any pull request should at the very least keep our code coverage the same
- if not increase it.

These are written with the `pytest` framework for `Gravel`. Unit tests are
based on `Jest` for `Glass`.

Functional tests
----------------

These are very close to integration tests and are sometimes used
interchangeably.

A functional test should simulate in code as best as possible a user
interacting with the program. For example, confirming that the correct
operations are performed and state is reached when a disk is added.

We write functional tests for gravel using the `pytest` framework.

Smoke tests
-----------

These are a handful of tests that check operation works in a real deployment.
These can be written as part of `aqrtest` and is probably in most need of
expansion.

A pull request could include a relevant smoke test with it. However we likely
need some "cards" on writing specific tests for scenarios that we want to cover
(for example: What happens when $x disks are removed).

End to end tests
----------------

These are very similar to smoke tests but should simulate the end user. These
therefore exercise the GUI.

The `Glass` frontend is using `Cypress`framework for E2E tests.

=================
Tools and systems
=================

Currently we have components in place that are capable of running linting
tests, unit tests, integration tests, functional tests, and smoke/end-to-end
tests. They are achieved with the following components:

aqrdev
------
aqrdev is our developer tooling used to build and run aquarium on top of
vagrant VM's.

flake8
------
flake8 is used to validate our python formatting.

mypy
----
mypy validates our python typing.

pytest
------
pytest runs any python unit and function tests using the pytest framework.
These exists in `src/gravel/tests`.

tox
---
Tox is a python virtual environment manager that can be used to execute the
above tools. `tox` is what our github actions call to validate pull requests
and subsequently runs `flake8`, `mypy`, and `pytest`.

The tox configuration can be found in `src/tox.ini`

wasser
------
Wasser is our test infrastructure runner. It can create VM's in OpenStack and
execute arbitrary commands on them. This is used to do builds of `aquarium`
inside a VM on each pull request. Our Jenkins instance executes this and uses
the wasser instructions from [.wasser/config.yaml](https://github.com/aquarist-labs/aquarium/blob/main/.wasser/config.yaml).

Currently wasser is configured to build aquarium much like the developer docs,
and validates the build by launching aquarium in vagrant using `aqrdev`.

Jenkins
-------
Jenkins is configured to run `wasser` on each PR. The jobs are defined in 
https://github.com/aquarist-labs/wasser/blob/main/examples/jjb/aquarium.yaml

aqrtest
-------

This is not run as part of any CI yet.

TODO