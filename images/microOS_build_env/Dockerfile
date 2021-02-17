FROM registry.opensuse.org/opensuse/leap:15.2
MAINTAINER Volker Theile <vtheile@suse.com>

RUN zypper ref && zypper --non-interactive install zsh git \
    python3 python3-pip python3-rados python3-kiwi nodejs-common \
    vagrant vagrant-libvirt npm sudo which gptfdisk kpartx \
    btrfsprogs dosfstools e2fsprogs

CMD ["zsh"]
