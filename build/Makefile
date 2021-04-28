# width = 120, use -s to suppress command echo
DOCKER := $(wildcard /.dockerenv)

ifeq (/.dockerenv, $(wildcard /.dockerenv))
    include /root/makefile.docker
else
    include makefile.local
endif

PYTHON := $(PYTHON_ROOT)/bin/python3
YASHA := $(PYTHON_ROOT)/bin/yasha
BUILD_DIR := .
VAR_DIR := var
LOG_DIR := log
DOCS_DIR := docs
TMP_DIR := tmp
PROJECT_DIR := ..
SRC_DIR := $(BUILD_DIR)/src
TARGET_DIR := $(BUILD_DIR)/target
INCLUDE_DIR := $(BUILD_DIR)/include
VPATH = src
J2_FILES := $(shell cd $(SRC_DIR); find . -type f -name '*.j2')
MD_FILES := $(patsubst %.j2,%.md, $(J2_FILES))
TARGET_FILES := $(shell /usr/bin/find $(PROJECT_DIR) -name "*.md" | $(GREP) -v build)
IMAGE_FILES := $(shell cd $(SRC_DIR); find . -type f -name '*.png')


all: clean package
	echo "packaging $(MD_FILES)"

# start up the dynamic data fifo daemon
#   this exists because the template engine requires data files and I refuse to create temporary ones
#   really, I just wanted to have python fun
data:
#	-$(PYTHON) bin/data_gen.py --server  # just write to file instead for now till I debug fifo race condition
	-$(PYTHON) bin/data_gen.py

# agressively kill off the dynamic data fifo daemon
stop-data:
	-/bin/kill `cat var/data_gen.pid`
	-/bin/rm var/data_gen.pid
	-/bin/kill `/usr/bin/pgrep -f data_gen.py`

package: data templates readmes docs
	echo "making package"

docs:
	echo "making project docs"
	doxygen doxygen.conf

templates:
	echo "making templates"

readmes: data $(MD_FILES)
	echo "making docs, python is $(PYTHON) and pwd is "
	pwd
	echo "files: $(MD_FILES)"
	echo "images: $(IMAGE_FILES)"
	for x in $(IMAGE_FILES) ; do \
		/bin/mkdir -p `dirname $(TARGET_DIR)/$$x` && \
		/bin/cp -v $(SRC_DIR)/$$x $(TARGET_DIR)/$$x ; \
	done

# includes example of doing json as well, not included in this release
test: clean data README.md test/test.md test/json-test.json.md
	echo "making test: $^"

init: $(TARGET_FILES)
	echo "initing the build/src directory with seed templates"
	echo "MD files:"
# this could be done better but it works so moving on. If you care, fix it.
	for x in $(TARGET_FILES) ; do \
		prefix=$(PROJECT_DIR)/ ; \
		y=$${x#$$prefix} ; \
		y=$${y%.md} ; \
		z=$$y.yaml ; \
		y=$$y.j2 ; \
		/bin/mkdir -p `dirname $(SRC_DIR)/$$y` ; \
		cp -nv $(INCLUDE_DIR)/EXAMPLE_README.jt2 $(SRC_DIR)/$$y ; \
		cp -nv $(INCLUDE_DIR)/sample.yaml $(SRC_DIR)/$$z ;\
	done
# TODO: for init I should use diff or merge against examples to create
# more complete seed jinja per use case. or not. example below
# merge -p src/README.j2 ../README.md target/README.md > tmp/evolve/README.md

info:
	echo "Docker: $(DOCKER)"
	echo "MD_FILES: "
	for x in $(MD_FILES) ; do \
		echo $$x ; \
	done
	echo "J2_FILES: "
	for x in $(J2_FILES) ; do \
		echo $$x ; \
	done
	echo "TARGET_DIR: "
	for x in $(TARGET_DIR) ; do \
		echo $$x ; \
	done
	echo "TARGET_FILES: "
	for x in $(TARGET_FILES) ; do \
		echo $$x ; \
	done


.PHONY: clean
clean : stop-data
	echo "making clean"
	rm -rf $(TARGET_DIR)
	rm -rf $(VAR_DIR)
	rm -rf $(LOG_DIR)
	rm -rf $(DOCS_DIR)/html
	rm -rf $(TMP_DIR)

# TODO: separate recipes for .md.j2 and json.j2 out to support json templates as well

%.md: %.j2 %.yaml
	echo "building $< -> $(TARGET_DIR)/$@ using $*.yaml and $*.j2"
	/bin/mkdir -p `dirname $(TARGET_DIR)/$@`
	$(YASHA) -I $(INCLUDE_DIR) --targetPath="$(TARGET_DIR)" -v include/default.yaml -v $(SRC_DIR)/$*.yaml -v ./tmp/generated_data.yaml -o $(TARGET_DIR)/$@ $<

diff:
	echo "diffing"
	diff -Ebwqrd -x *.py $(TARGET_DIR)/ -x *.yaml $(PROJECT_DIR)/

publish: readmes
	echo "Publishing Docs"
	rm -rf $(TARGET_DIR)/test
	for x in $(MD_FILES) ; do \
		[[ -e $(PROJECT_DIR)/$$x ]] && /bin/cp $(TARGET_DIR)/$$x $(PROJECT_DIR)/$$x ; \
	done
