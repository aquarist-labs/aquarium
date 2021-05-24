# Aquarium's image autobuilder, with containers

This container image will be able to automatically build an Aquarium vagrant
image, allowing its user to specify where to build from and where to build to.

## Recommended usage

### Build the container image

    sudo podman build -t aqr-builder .

### Start a build

Assuming we have our source repository in `/home/foo/aquarium.git`, and want the
final build to live under `/tmp/builds`, this would be the command to pass on:

    sudo podman run --privileged \
        -v /tmp/builds:/builder/out \
        -v /home/foo/aquarium.git:/builder/src \
        -v /home/foo/aquarium.git/tools:/builder/bin \
        -v /var/cache/kiwi:/builder/cache aqr-builder

In this example we are providing four volumes to the container:

* The first one is for the output directory, where the resulting build will
  live. Multiple calls to the `run` command will result in multiple resulting
  builds under the specified output directory.

* The second specifies the source repository directory; this is where we're
  going to be obtaining the sources and needed files to build the image.

* The third volume specified the location of the binaries we need; for most
  builds, these live under the source repository's `tools/` directory. Amongst
  the required files is the container image's entrypoint script:
  `autobuilder.sh`.
  
* Finally, the fourth volume is the cache to be used by `kiwi-ng`. It is
  particularly useful to have a shared cache directory if multiple builds are
  being created in a short span of time (less than a week apart, ish). This
  avoids pulling packages over and over.

In the end, and assuming the build was successful, one will be able to find a
new directory under `/tmp/builds/`. It will be named in the form of
`aqr-<branch>-<date>.<N>`, where `branch` will be the name of the checked out
branch from the source repository; `date` will be the current date in the format
`YYYYMMDD`, and `N` will be a zero-padded integer representing the number of the
build in case of multiple builds for the same branch and date.
