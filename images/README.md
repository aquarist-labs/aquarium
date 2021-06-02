# images

To help us build an image reliably, we are relying on `kiwi`. We do so by
offering the required build configuration files to natively build using
`kiwi`, and containerized environments to build this image on.

## Aquarium's image

In `aquarium/` one will be able to find `config.xml`, describing the image to
be created, with several different possible profiles. This file was initially
based on [openSUSE's MicroOS Tumbleweed image](https://build.opensuse.org/package/show/openSUSE:Factory/openSUSE-MicroOS),
but evolved to become its own thing, focused solely on our use cases and needs.

One will also be able to find, under the same directory, a couple of scripts:
`config.sh` and `disk.sh`. Both will be executed by `kiwi` at different steps of
the [build process](https://osinside.github.io/kiwi/concept_and_workflow/shell_scripts.html).

The former, `config.sh`, will be run at some point after the packages have
been installed, and before the image is generated. During this step we will be
installing additional packages not available through our repositories, namely
python packages through `pip`, and will enable the `aquarium` service, which
will be then be started on boot.

The latter, `disk.sh`, is run within a chrooted image mount, but before the
image is finalized. During this step we will be obtaining container images
needed for Aquarium's execution, so we have them available upon first run,
including an image for `Ceph` and an image for `etcd`.


## Containerized build environment

Under `builder/` we provide a `Dockerfile` that will be able to automatically
build an image from a checked out branch. This might be useful for those on
distributions that do not support `kiwi`, or under which `kiwi` does not work
reliably.
