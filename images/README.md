# images

To help us build an image reliably, we are relying on `kiwi` and `microOS`.

In `microOS/` one will be able to find `config.xml`, describing the image to be
created, with several different possible profiles. This file has been obtained
from [openSUSE's MicroOS Tumbleweed OBS repository](https://build.opensuse.org/package/show/openSUSE:Factory/openSUSE-MicroOS),
and slightly adapted to our needs.

One will also be able to find, under the same directory, a `config.sh` script.
This is automatically run by `kiwi` during the build process, at some point
after the packages have been installed, and before the image is generated. This
is generally where services will be enabled, for example. We are, at the moment
of writing, simply installing additional packages that are not available through
the repositories, relying on `pip` to do so. In the future, we expect to use
this file to enable the backend's service.

One can also find a `build.sh` script, which is merely a helper to build a
microOS image from `config.xml`. At the moment, a Vagrant image will be
generated. Feel free to run `build.sh --help` for slightly more info, but the
script itself should be fairly straightforward.
