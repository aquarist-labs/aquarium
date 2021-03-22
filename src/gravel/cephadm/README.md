cephadm
========

Here lies (or should lie) a symlink to upstream's cephadm. This symlink,
`cephadm.bin` should be pointing to `ceph.git/src/cephadm/cephadm`. This ceph
repository should be living in the root of this project's repository,
initialized as a submodule. The version should be fixed.

If you do not have such a file, we encourage you to either manually initializing
the submodule with `git submodule update --init` and then creating the symlink,
or running the script found at `tools/setup-dev.sh`.

Additionally, we are here preparing cephadm to be consumed as a library
throughout our project, wherever applicable.

Changes to cephadm should be contributed upstream. Be a good citizen.
