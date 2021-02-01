# vagrant test scripts

Essentially, through the `setup.sh` script we will generate a `Vagrantfile`
ready to deploy two nodes, `node01` and `node02`, ready for development or
testing.

This script will ensure a box name is provided, and if the box does not exist it
will check if there's a build matching the box's name, and add it to Vagrant if
so.

Setups will be then available under the `setups/` directory, matching the setup
name provided to the script. Each setup will be two nodes, as mentioned before,
each with four disks.

On each node, at `/srv/backend/` there will be an NFS mount of the root of this
repository. Oftentimes the user will have to provide the root password so
Vagrant can deal with NFS exports.
