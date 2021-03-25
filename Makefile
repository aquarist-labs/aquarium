# The version needs an annotated tag in the git repo in the form vX.Y.Z.
# If such is not present, fall back to using v0.0.0 so we get a non-empty
# version string.
VERSION=$(shell (git describe --match 'v*' --long 2>/dev/null || echo 'v0.0.0') | sed 's/^v//')

usage:
	@echo "Try running \`make dist\` to build a tarball"

submodules:
	git submodule update --init

glass:
	cd src/glass && npm install && npx ng build --prod --output-hashing=all

dist: submodules glass
	$(eval TMPDIR := $(shell mktemp -d))
	$(eval TAR_BASE := $(TMPDIR)/aquarium-$(VERSION))
	$(eval TAR_USR := $(TAR_BASE)/usr/share/aquarium)
	$(eval TAR_UNIT := $(TAR_BASE)/usr/lib/systemd/system)
	$(eval TAR_SBIN := $(TAR_BASE)/usr/sbin)
	mkdir -p $(TAR_USR) $(TAR_UNIT) $(TAR_SBIN)
	# Copy gravel, glass, aquarium.py and cephadm from src/...
	cd src && \
	find gravel -iname '*ceph.git*' -prune -false -o -iname '*.py' | \
		xargs cp --parents --target-directory=$(TAR_USR) && \
	cp --target-directory=$(TAR_USR) ./aquarium.py && \
	cp -R --parents --target-directory=$(TAR_USR) glass/dist && \
	cp --target-directory=$(TAR_SBIN) ./gravel/ceph.git/src/cephadm/cephadm
	# Copy aquarium service
	cp systemd/aquarium.service $(TAR_UNIT)
	# Create python venv for use by aquarium at runtime.  Have to explicitly
	# specify /usr/bin/python3 here, rather than just calling python3 with
	# no path, otherwise if we're already in a venv when running `make dist`,
	# /usr/share/aquarium/venv/bin/python3 will point to the existing venv
	# python on the build host, which is completely wrong.
	/usr/bin/python3 -m venv $(TAR_USR)/venv
	# Install requirements (note: deliberately *not* using
	# --system-site-packages, otherwise we might accidentally not install
	# some of our dependencies which are already present on the build host)
	$(TAR_USR)/venv/bin/pip install -r src/requirements.txt
	# At this point, the shebang lines for everyting in venv/bin will be
	# absolute paths on the build host (e.g. /tmp/tmp.QoQm2t2j06/aquarium-0.1.0-0-gc28eb76/usr/share/aquarium/venv/bin/python3)
	# but we need them to be appropriate for the host we're *installing* on,
	# so need to strip out the leading part of the path.  Also, even though
	# the venv was created without --system-site-packages, we actually need
	# to set that to true now, so that python *inside* the venv will find
	# the python rados library which is installed as a package.
	cd $(TAR_USR)/venv ; \
	fixfiles=$$(find -type f -not -name *.py[cox] -exec grep -Il "#\!.*$(TAR_BASE)" {} \;) ; \
	fixfiles="$$fixfiles bin/activate*" ; \
	for f in $$fixfiles; do \
		echo -n "fixing path in $$f: " ; \
		grep $(TAR_BASE) "$$f" ; \
		sed -i -e "s;$(TAR_BASE);;" $$f ; \
	done ; \
	sed -i -e "s;^include-system-site-packages.*;include-system-site-packages = true;" pyvenv.cfg
	tar -czf aquarium-$(VERSION).tar.gz -C $(TMPDIR) aquarium-$(VERSION)
	rm -r $(TMPDIR)

