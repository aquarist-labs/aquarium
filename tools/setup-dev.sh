#!/bin/bash

dependencies_opensuse_tumbleweed=(
  "btrfsprogs"
  "git"
  "kpartx"
  "make"
  "python3"
  "python3-kiwi"
  "nodejs-common"
  "npm"
  "vagrant"
  "vagrant-libvirt"
  "libvirt-daemon"
  "dosfstools"
)

cypress_opensuse_leap=(
  "xorg-x11-server"
  "xorg-x11-fonts"
  "gconf2"
  "gtk2-devel"
  "gtk3-devel"
  "libnotify-devel"
  "libxcb-screensaver0"
  "mozilla-nss"
  "alsa"
)

cypress_opensuse_tumbleweed=(
  "xorg-x11-server-Xvfb"
  "xorg-x11-fonts"
  "gconf2"
  "gtk2-devel"
  "gtk3-devel"
  "libnotify-devel"
  "libxcb-screensaver0"
  "mozilla-nss"
  "alsa"
)

cypress_debian_ubuntu=(
  "libgtk2.0-0"
  "libgtk-3-0"
  "libgbm-dev"
  "libnotify-dev"
  "libgconf-2-4"
  "libnss3"
  "libxss1"
  "libasound2"
  "libxtst6"
  "xauth"
  "xvfb"
)

dependencies_debian=(
  "btrfs-progs"
  "git"
  "make"
  "python3"
  "python3-pip"
  "python3-venv"
  "nodejs"
  "vagrant"
  "libvirt-daemon"
)

dependencies_ubuntu=(
  "btrfs-progs"
  "git"
  "make"
  "python3"
  "python3-pip"
  "python3-venv"
  "nodejs"
  "vagrant"
  "libvirt-daemon"
  "libvirt-daemon-system"
)

dependencies_build_python_leap=(
  "gcc"
  "automake"
  "bzip2"
  "libbz2-devel"
  "xz"
  "xz-devel"
  "openssl-devel"
  "ncurses-devel"
  "readline-devel"
  "zlib-devel"
  "libffi-devel"
  "sqlite3-devel"
)

dependencies_build_python_deb=(
  "make"
  "build-essential"
  "libssl-dev"
  "zlib1g-dev"
  "libbz2-dev"
  "libreadline-dev"
  "libsqlite3-dev"
  "wget"
  "curl"
  "llvm"
  "libncurses5-dev"
  "xz-utils"
  "tk-dev"
  "libxml2-dev"
  "libxmlsec1-dev"
  "libffi-dev"
  "liblzma-dev"
)


usage() {
  cat << EOF
usage: $(basename $0) [options]

options:
  --show-dependencies     Show required dependencies.
  --skip-install-deps     Skip installing dependencies.
  --pyenv-python          Use pyenv python version, e.g. 3.8.9

  -h|--help               This message.
EOF
}

yes_no() {
    while true; do
        read -p "$1 (y/n)? " yn
        case $yn in
            [Yy]* ) return 0; break;;
            [Nn]* ) return 1; break;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

if [ "$(id -u)" -eq 0 ]; then
	echo error: please do not run this script as root
	exit 1
fi

osid=$(grep '^ID=' /etc/os-release | sed -e 's/\(ID=["]*\)\(.\+\)/\2/' | tr -d '"')

skip_install_deps=false
show_dependencies=false

pyenv_python=""
pyenv_python_default=3.8.9
pyenv_url="https://github.com/pyenv/pyenv.git"

export PYENV_ROOT=${PYENV_ROOT:-"$HOME/.pyenv"}
export PATH=$PYENV_ROOT/bin:$PATH

case $osid in
    opensuse-leap)
      pyenv_python="$pyenv_python_default"
      ;;
    *)
      ;;
esac

while [[ $# -gt 0 ]]; do

  case $1 in
    --show-dependencies)
      show_dependencies=true
      ;;
    --skip-install-deps)
      skip_install_deps=true
      ;;
    --pyenv-python)
      pyenv_python=$2
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unrecognized parameter '$1'"
      usage
      exit 1
      ;;
  esac
  shift 1
done


if ${show_dependencies} ; then

  case $osid in
    opensuse-tumbleweed | opensuse-leap)
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      ;;
    debian)
      echo "  > ${dependencies_debian[*]}"
      ;;
    ubuntu)
      echo "  > ${dependencies_ubuntu[*]}"
      ;;
    *)
      echo "error: unsupported distribution"
      echo "These are the packages you might need:"
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      exit 1
      ;;
  esac
  exit 0
fi


if ! ${skip_install_deps} ; then

  case $osid in
    opensuse-tumbleweed | opensuse-leap)
      echo "=> try installing dependencies"
      sudo zypper --non-interactive install ${dependencies_opensuse_tumbleweed[*]} || {
        echo "Dependency installation failed"
        exit 1
      }
      if [ -n "$pyenv_python" ] ; then
        echo "=> try installing dependencies for building python because --pyenv-python requested"
        sudo zypper --non-interactive install ${dependencies_build_python_leap[*]} || {
          echo "Dependency installation failed"
          exit 1
      }
      fi
      echo "=> try installing dependencies for cypress"
      case $osid in
        *-tumbleweed)
          sudo zypper --non-interactive install ${cypress_opensuse_tumbleweed[*]} || {
            echo "Dependency installation for cypress failed"
            exit 1
          }
          ;;
        *-leap)
          echo "=> try installing dependencies for cypress"
          sudo zypper --non-interactive install ${cypress_opensuse_leap[*]} || {
            echo "Dependency installation for cypress failed"
            exit 1
          }
          ;;
      esac
      ;;
    debian)
      echo "=> installing nodejs16.x repo to apt source"
      wget -qO - https://deb.nodesource.com/setup_16.x | sudo bash -
      echo "=> try installing dependencies"
      sudo apt-get install -q -y ${dependencies_debian[*]} || {
        echo "Dependency installation failed"
        exit 1
      }
      if [ -n "$pyenv_python" ] ; then
        echo "=> try installing dependencies for building python because --pyenv-python requested"
        sudo apt-get install -q -y --no-install-recommends ${dependencies_build_python_deb[*]} || {
          echo "Dependency installation failed"
          exit 1
        }
      fi
      echo "=> try installing dependencies for cypress"
      sudo apt-get install -q -y ${cypress_debian_ubuntu[*]} || {
	  echo "Dependency installation for cypress failed"
          exit 1
      }
      ;;
    ubuntu)
      echo "=> installing nodejs16.x repo to apt source"
      wget -qO - https://deb.nodesource.com/setup_16.x | sudo bash -
      echo "=> try installing dependencies"
      sudo apt-get install -q -y ${dependencies_ubuntu[*]} ||  {
        echo "Dependency installation failed"
        exit 1
      }
      if [ -n "$pyenv_python" ] ; then
        echo "=> try installing dependencies for building python because --pyenv-python requested"
        sudo apt-get install -q -y --no-install-recommends ${dependencies_build_python_deb[*]} || {
          echo "Dependency installation failed"
          exit 1
        }
      fi
      echo "=> try installing dependencies for cypress"
      sudo apt-get install -q -y ${cypress_debian_ubuntu[*]} || {
	  echo "Dependency installation for cypress failed"
          exit 1
      }
      ;;
    *)
      echo "error: unsupported distribution ($osid)"
      echo "please install the following dependencies if not met:"
      echo "  > ${dependencies_opensuse_tumbleweed[*]}"
      echo "and then run with '--skip-install-deps'"
      exit 1
      ;;
  esac

fi

if [ -n "$pyenv_python" ] ; then
  if [ -d $PYENV_ROOT ] ; then
    echo "WARNING: Found previously installed pyenv by [$PYENV_ROOT]" > /dev/stderr
    if yes_no "Cleanup and reinstall from [$pyenv_url]" ; then
      rm -rf $PYENV_ROOT
    fi
  fi

  if [ ! -d $PYENV_ROOT ] ; then
    mkdir -p $PYENV_ROOT
    git clone $pyenv_url $PYENV_ROOT
    (cd $PYENV_ROOT && src/configure && make -C src)
  fi

  if $PYENV_ROOT/bin/pyenv versions --bare | grep -s "^${pyenv_python}$" ; then
    echo "Python version $pyenv_python is already installed in pyenv by $PYENV_ROOT" > /dev/stderr
  else
    echo "No required python version $pyenv_python installed in pyenv by $PYENV_ROOT" > /dev/stderr
    echo Available python versions for the pyenv: > /dev/stderr
    $PYENV_ROOT/bin/pyenv install --list | grep -sE '(3.8|3.9)'
    $PYENV_ROOT/bin/pyenv install $pyenv_python
  fi
  $PYENV_ROOT/bin/pyenv local $pyenv_python
fi

PYTHON="python3"
if [ -n "$pyenv_python" ] ; then
  PYTHON="$PYENV_ROOT/bin/pyenv exec python"
fi

if ! PY_VER_STR=$($PYTHON --version) ; then
  echo "error: missing python3"
  exit 1
fi

PY_MINOR=$(echo $PY_VER_STR | cut -d. -f2)
if [ $PY_MINOR -lt 8 ] ; then
  echo "error: python >= 3.8 is required ($PY_VER_STR installed)"
  exit 1
fi

if ! npm --version &>/dev/null ; then
  echo "error: missing npm"
  exit 1
fi

# don't recurse into ceph.git unless we explicitly need a submodule.
git submodule update --init || exit 1

[[ ! -e "src/gravel/cephadm/cephadm.bin" ]] && \
  ln -fs ../ceph.git/src/cephadm/cephadm src/gravel/cephadm/cephadm.bin

if [ -d venv ] ; then
    echo
    echo "Detected an existing virtual environment:"
    echo "  > $(realpath venv)"
    if yes_no "Blow it away"; then
        rm -rf venv || exit $?
    fi
    echo
fi


# We need system site packages because librados python bindings are only
# available as a package, they're not on pypi (and Tim thinks they probably
# never will be). Setting --system-site-packages here means the venv will
# work properly if someone uses it inside the image, where we need to be
# able to fall back to system packages to get librados.
$PYTHON -m venv --system-site-packages venv || exit 1

source venv/bin/activate
pip install -r src/requirements.txt -U || exit 1
deactivate

pushd src/glass &>/dev/null
rm -rf node_modules
npm install || exit 1
npx ng build || exit 1
popd &>/dev/null
