NAME := turbogears

all: build

include buildenv/Makefile.common
lint: lint_pylint
tests: tests_nose
clean: clean_python
