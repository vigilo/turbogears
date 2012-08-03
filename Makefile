NAME := turbogears
EPYDOC_PARSE := vigilo\.turbogears\.(controllers\.autocomplete|rum\.fields)
SUBST_FILES := pkg/vigilo-clean-turbogears-sessions.sh

all: build
build: $(SUBST_FILES)

include buildenv/Makefile.common.python

pkg/vigilo-clean-turbogears-sessions.sh: pkg/vigilo-clean-turbogears-sessions.sh.in
	sed -e 's,@LOCALSTATEDIR@,$(LOCALSTATEDIR),g' $^ > $@
	chmod a+x $@

install: build install_python install_data
install_pkg: build install_python_pkg install_data

install_python: $(PYTHON) $(SUBST_FILES)
	$(PYTHON) setup.py install --record=INSTALLED_FILES
install_python_pkg: $(PYTHON) $(SUBST_FILES)
	$(PYTHON) setup.py install --single-version-externally-managed --root=$(DESTDIR) --record=INSTALLED_FILES

install_data: $(SUBST_FILES)
	# Cache
	mkdir -p $(DESTDIR)$(LOCALSTATEDIR)/cache/vigilo/sessions
	chmod 750 $(DESTDIR)$(LOCALSTATEDIR)/cache/vigilo/sessions
	[ `id -u` -ne 0 ] || chown $(HTTPD_USER): $(DESTDIR)$(LOCALSTATEDIR)/cache/vigilo/sessions

lint: lint_pylint
tests: tests_nose
doc: apidoc sphinxdoc
clean: clean_python
	rm -f $(INFILES)

.PHONY: install install_pkg install_python install_python_pkg install_data
