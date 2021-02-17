# About this Docker container
This Docker container is meant to be used on systems that are not based
on openSUSE to be able to build the MicroOS based Vagrant box.

# Build the container
To build the container run the following command.
```
$ cd /<GIT_REPO>/aquarium/images/microOS_build_env
$ docker build -t aquarium-dev-docker .
```

# Run the container
The `Aquarium` git repository will be mounted to `/srv/aquarium` in the container.
```
$ docker run -itd -v /<GIT_REPO>/aquarium:/srv/aquarium --hostname=aquarium-dev-docker --privileged aquarium-dev-docker
```

# Build the MicroOS Vagrant box
Please consult the `doc/from-zero-to-hacking.md` document for more information.
