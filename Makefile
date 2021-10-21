# The version needs an annotated tag in the git repo in the form vX.Y.Z.
# If such is not present, fall back to using v0.0.0 so we get a non-empty
# version string.
VERSION=$(shell (git describe --match 'v*' --long 2>/dev/null || echo 'v0.0.0') | sed 's/^v//')

usage:
	@echo "Try running \`make dist\` to build a tarball"

submodules:
	git submodule update --init

glass:
	cd src/glass && rm -rf node_modules && npm install && npx ng build --configuration production --output-hashing=all

dist: submodules glass
	$(eval TMPDIR := $(shell mktemp -d))
	$(eval TAR_BASE := $(TMPDIR)/aquarium-$(VERSION))
	$(eval TAR_USR := $(TAR_BASE)/usr/share/aquarium)
	$(eval TAR_UNIT := $(TAR_BASE)/usr/lib/systemd/system)
	$(eval TAR_SBIN := $(TAR_BASE)/usr/sbin)
	mkdir -p $(TAR_USR) $(TAR_UNIT) $(TAR_SBIN)
	# Copy gravel, glass, aquarium.py and cephadm from src/...
	cd src && \
	find gravel -iname '*.py' | \
		xargs cp --parents --target-directory=$(TAR_USR) && \
	cp --target-directory=$(TAR_USR) ./aquarium.py && \
	cp -R --parents --target-directory=$(TAR_USR) glass/dist && \
	cp -R --target-directory=$(TAR_USR) boot && \
	cp ./gravel/cephadm/cephadm.bin $(TAR_SBIN)/cephadm
	chmod 700 $(TAR_SBIN)/cephadm
	# Copy aquarium service
	cp systemd/aquarium.service $(TAR_UNIT)
	tar -czf aquarium-$(VERSION).tar.gz -C $(TMPDIR) aquarium-$(VERSION)
	rm -r $(TMPDIR)
