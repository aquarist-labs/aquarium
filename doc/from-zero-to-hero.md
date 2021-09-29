# From Zero to Hero

The goal of this document is to guide you through the process of setting
up a local, VM-based test instance via `Vagrant` on a Linux system of
your choice.

This includes checking out all the required repositories, setting up
a local build environment, running your first image build, and
starting the resulting cluster.

After only about half an hour, you will be able to login to a Ceph
cluster managed via `Aquarium` for the first time!

## Requirements

The requirements on your environment to follow this guide are as
follows:

- A physical machine, *not* a VM
  - Currently, this guide is tested on `x86_64`, but `aarch64` is
    coming!
- At least 16 GB of disk space
  - Approximately 4 GB for the directory you're building Aquarium in,
    and another 4 GB for `/var/lib/libvirt/` (or equivalent on your
    system). Note that this will grow if you actually store data in the
    cluster.
- Preferably [openSUSE Leap](https://www.opensuse.org/#Leap) or
  [openSUSE Tumbleweed](https://get.opensuse.org/tumbleweed) as the
  host, though we're working on extending this guide and our tooling to
  support other distributions - patches more than welcome!
- You will need access to the `root` account on the system for the image
  build and possibly need to install packages on the host to do so

Additionally, if you are developing and intend to run `tox` on the host, you
will require a python 3.8+ distribution. In case your distribution does not
support python 3.8, you may want to look into
[`pyenv`](https://github.com/pyenv/pyenv).

## Note On Host/Network References

Throughout this document, where we mention a `localhost` address, we are
assuming these steps are being run on the machine local to the user/developer.

Often that may not be the case (e.g., developers running their stuff on
remote development boxes). In those cases, please remember that
`aquarium` will be running on `0.0.0.0` (i.e., all interfaces), thus one
should be able to access the service through the remote machine's
network name/address. If this fails, please check whether the firewall
settings allow remote incoming connections.

The provided `Vagrant` image will be forwarding ports to the local host. In the
`localhost`, ports `1337` and `1338` will be used; the former for `node1`, the
latter for `node2`.

At this moment, although we spin-up both virtual machines, we do not
support a multi-node deployment yet.


## Why you currently need a physical setup

At this point, our development guide and code base only supports running
Aquarium in a small VM environment hosted on the machine you're
following this guide on.

This allows the lab environment to simulate a cluster of multiple
independent nodes fully under its control on a single physical node
instance.

Within these (virtual) nodes, the appliance installer takes care of all
further provisioning and deployment, from time synchronization to device
partitioning.

As the project evolves, we plan to support deploying these VMs directly
to the public or private cloud of your choice (again, patches welcome!),
as well as bare-metal hardware environments.

### Initial Steps

1. clone the repository locally:

    `git clone https://github.com/aquarist-labs/aquarium.git`

   This will reproduce the `main` branch from upstream, which is fine
   for testing but to which you cannot commit directly.

   If you want to check out your own fork with the branch on which your
   development is happening, use a command similar to:

    `git clone -b wip-getting-started https://github.com/aquarist-labs/aquarium.git`

2. change into the directory containing the checked out project:

    `cd aquarium`

3. run

    `./tools/setup-dev.sh`

   which will install required package dependencies, check out further
   repositories from GitHub (which can take quite a while for our larger
   submodules, sorry about that - never fear, it will complete!), start
   the compile, and set up the environment such that one can start
   hacking.

   There will be a few warning from `npm` which you can safely ignore.

   Aquarium requires python3.8+ to run successfully. If your host distribution does
   not support python3.8+ offically yet, our setup script provides pyenv to
   help you setup an alternative python environment. If pyenv already
   exists in`$HOME/.pyenv/` , the script will try to reuse your setup. Regardless,
   you will need to provide the python version. For example:
    `--pyenv-python 3.8.8`
   The script can also replace and rebuild a new pyenv python for you. Just
   reply yes when it ask you cleanup and reinstall pyenv.

4. run `source tools/venv/bin/activate`.

   You are now in the virtual environment with all the python packages
   in the required versions. If you want to exit and return to your
   normal shell environment at any time, run `deactivate`.

### Building a MicroOS image

At this time, we provide the means to build a `Vagrant` image based on
`MicroOS`. While, technically, one can run Aquarium in whatever machine they
want, we took steps to ensure this built image will have all the required
dependencies to run Aquarium. Additionally, we also package whatever is the
repository's current version of Aquarium, such that one has a working
environment upon booting the image.

1. run `./tools/build-image.sh [-n <BUILDNAME>]` (by default, `BUILDNAME` will be `aquarium`)

2. `kiwi`, the VM image building tool, will ask for the `root` password
   once during this build, since it needs to complete a few privileged
   operations while laying out the virtual file system. This will not
   make modifications to your host system.

3. [Go grab yourself a beverage, a snack, or both.](https://xkcd.com/303/)


### Running a MicroOS image on Vagrant

Assuming we've succesfully built a MicroOS image, getting a `Vagrant` setup up
and running should not be much of a hurdle.

1. run `./tools/aqua create [--box BOXNAME] [--image IMAGENAME] <NAME>`

    This will create a vagrant deployment under `tests/vagrant/deployments/` with
    name `NAME`. If omitted, `BOXNAME` defaults to `aquarium`. If `IMAGENAME` is
    provided, then the tool will attempt to find an existing image with said
    name and import it as a Vagrant box to be used for this deployment. As an
    example, let's assume we run `./tools/aqua create foobar`.

2. to start the deployment we just created, we'll run:

    `./tools/aqua start --conservative foobar`

   which will bring up your machines one by one. (Once you are happy
   this works, you can drop the last option and bring all your machines up in
   parallel!)

   Important notes:

   - Vagrant may ask for the root password to setup NFS shares exports on the host,
     to share files between the host and the VMs (see [the Vagrant
     docs](https://www.vagrantup.com/docs/synced-folders/nfs#root-privilege-requirement)
     if you wish to avoid this); and

   - on some systems one might have to open NFS ports prior to running
     `aqua start`, or it just might get stuck trying to reach a server
     that is unreachable.

   - if you see an error such as

     `Call to virConnectOpen failed: authentication unavailable: no polkit agent available to authenticate action 'org.libvirt.unix.manage'`

     make sure that your user is allowed to connect to libvirt. One
     solution is to add the user to the `libvirt` group as follow:

     `sudo usermod --append --groups libvirt $(whoami)`

     For this change to take effect (you should see the group when
     running `id`), you may have to login again.

   - The host must support NFSv3. Otherwise, you may have to tweak the
     `Vagrantfile` [to use
     NFSv4](https://www.vagrantup.com/docs/synced-folders/nfs#other-notes)

3. This break has the perfect length for an espresso.

4. `./tools/aqua shell foobar [--node NODE]`

    If `NODE` is not specified, the shell will be dropped by default on
    `node1`. You can always choose to drop into `node2` by specifying that
    much.

    Note this will drop you into a regular user session and you will
    need to use `sudo` to perform admin tasks.

At this point you will have shell access to the node, and it is expected
that Aquarium will be running. Accessing `http://localhost:1337` (or
`1338` depending which node you are trying to access) should be
possible, and you should be presented with a nice frontend. If your
connection is refused or reset, it might just be that you need to open
firewall ports.


### Restarting the daemon

Changes to the code repository will not immediately reflect in the
running instance, since that will already have loaded all source files.

However, since files are shared via NFS between the host and the VMs,
a simple restart of the daemon from the shared directory will activate
those changes.

1. run `sudo systemctl stop aquarium`, which will stop the Aquarium daemon.

   You can confirm that this properly stopped the services by checking
   that you can no longer access Aquarium on the host's port `1337` (or
   `1338`, depending on which node the command was run).

2. `cd /srv/aquarium` within the VM

3. `sudo ./tools/run_aquarium.sh`

3. a) you can use `--use-venv` to have a virtual-env created inside the
      current-working-directory (as "venv") in which the dependencies are
      installed. This is separate to the virtual-env that was created earlier
      by `setup-dev.sh` which is used for the purposes of the tools inside
      `tools/` (such as `aqua`).

4. access your newly running environment at `http://localhost:1337`

And this should cover the initial steps to allow one to start hacking on
Aquarium. The next section will cover development in finer detail.


## Developing

Let's add our first trivial patch!

### Access the Ceph cluster via CLI

For development purposes, it can be helpful to access the cluster via
CLI. You can reach the Ceph CLI within Aquarium as follows:

1. Connect to the VM and run Aquarium

2. Run the `sudo cephadm shell` command within the VM


## Updating

This section will walk you through incrementally updating your local
environment and images build.
