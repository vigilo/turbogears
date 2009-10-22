NAME := turbogears
include ../glue/Makefile.common
all: build
MODULE := $(NAME)
CODEPATH := $(NAME)
lint: lint_pylint
tests: tests_tg
