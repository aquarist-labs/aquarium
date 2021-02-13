# From Zero to Hacking

## Note Before

Throughout this document, where we mention a `localhost` address, we are
assuming these steps are being run on the machine local to the user/developer.

Often that may not be the case (e.g., developers running their stuff on remote
development boxes). In those cases, please remember that `aquarium` will be
running on `0.0.0.0` (i.e., all interfaces), thus one should be able to access
the service through the remote machine's address; however, that may require
opening firewall ports.

The provided `Vagrant` image will be forwarding ports to the local host. In the
localhost, ports `1337` and `1338` will be used; the former for `node01`, the
latter for `node02`. At the moment of writing, although we spin-up both
machines, we do not support a multi-node deployment. Regardless, one can always
run Aquarium on either machine, or both machines.


## Running things for fun and pleasure

Given the nature of Aquarium, it's probably a good idea not to run it on the
same machine where you are developing. While that is not impossible, nor should
it cause any particular damage, the fact is that its requirements are often not
what one would expect to provide while developing:

1. to be usable, one needs to bootstrap a cluster: this means running several
   containers, running Ceph;

2. to further be of use, one needs to deploy services: this means having spare
   disks to deploy OSDs on, and then provision the services;

3. It means relinquishing control of some aspects of your machine to Aquarium,
   namely NTP servers configuration, some firewall ports will need to be opened,
   SSH keys will need to passed around; and,

4. Ultimately, it needs root access. We are going to be provisioning disks after
   all, and a lot more shenanigans that might touch parts of your system that _do_
   require root privileges.

That said, if _you_ want to deploy Aquarium on your machine, or any machine, for
whatever reason, don't feel discouraged: we will be happy to lend a hand if/when
things go haywire. But, generally speaking, that's really not what most people
will want if they are playing with, or developing for Aquarium.

This guide is focused on getting one's environment up to speed, so they can
start playing or developing. The path of least resistance is relying on VMs or
containers. This is what this guide focuses on.


### Initial Steps


1. clone the repository:

    `git clone https://github.com/aquarist-labs/aquarium.git`

2. run `./tools/setup-dev.sh`, which will install required dependencies, and set
   up the environment such that one can start hacking.

3. run `source venv/bin/activate`.


### Building a MicroOS image

At this time, we provide the means to build a `Vagrant` image based on
`MicroOS`. While, technically, one can run Aquarium in whatever machine they
want, we took steps to ensure this built image will have all the required
dependencies to run Aquarium. Additionally, we also package whatever is the
repository's current version of Aquarium, such that one has a working
environment upon booting the image.

1. run `./tools/build-image.sh [-n <BUILDNAME>]` (by default, `BUILDNAME` will be `aquarium`)

2. input your root password once `kiwi` asks for it. We're not the ones at fault
   here. That is a `kiwi` thing.

3. Go grab yourself a beverage, a snack, or both.


### Running a MicroOS image on Vagrant

Assuming we've succesfully built a MicroOS image, getting a `Vagrant` setup up
and running should not be much of a hurdle.

1. `cd ./tests/vagrant/`

2. run `./setup.sh [-b BUILDNAME] <NAME>`

    This will create a vagrant deployment under `tests/vagrant/setups/` with
    name `NAME`. If omitted, `BUILDNAME` defaults to `aquarium`. As an example,
    let's assume we run `./setup.sh foobar`.

3. `cd setups/foobar/`

4. run `vagrant up`, which will bring up your machines. This, however, may bring
   up a couple of things one should be aware of:

    - root password may be asked to address NFS shares, given we are exporting
      the repository's root to the VMs for development purposes; and

    - on some systems one might have to open NFS ports prior to running
      `vagrant up`, or it just might get stuck trying to reach a server that is
      unreachable.

5. Go grab some water, better for your health.

6. `vagrant ssh [NODE]`

    If `NODE` is not specified, the shell will be dropped by default on
    `node01`. You can always choose to drop into `node02` by specifying that
    much.
    
At this point we have shell access to the node, and it is expected that Aquarium
will be running. Accessing `http://localhost:1337` (or `1338` depending which
node you are trying to access) should be possible, and you should be presented
with a nice frontend. If your connection is refused or reset, it might just be
that you need to open firewall ports for localhost access.


### Setting up for development

Given the version of Aquarium currently running on a MicroOS image is
essentially burnt into the image, one is unable to actively develop on it. But
never fear!

1. run `systemctl stop aquarium`, which will stop the Aquarium daemon. One will
   no longer be able to access Aquarium on the host's port `1337` (or `1338`,
   depending on which node the command was run).

2. `cd /srv/aquarium`

3. run `sudo ./run_aquarium.sh`

4. access your running environment at `http://localhost:1337`


And this should cover the initial steps to allow one to start hacking on
Aquarium. The next section will cover development in finer detail.


## Developing

TBD

