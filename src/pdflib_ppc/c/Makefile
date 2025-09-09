# Makefile for PDFLib/C projects
# This may have to be changed for your build environment

CFLAGS	= -Wall -Wno-unused -I./include
LDFLAGS	= -L./lib
#LDLIBS	= -lpdf -lm
LOADLIBES= -lpdf -lm
RM	= rm -f

# use the following for Mac OS X...
LDLIBS	= -lpdf -lm -framework ApplicationServices

# ...and make sure to set the search path for dynamic libraries, e.g.
# (in the shell) unless you already installed PDFlib in the system:

DYLD_LIBRARY_PATH=./lib make test

#PROGS	= \
#	make_template \
#	hello \
#	image \
#	chartab \
#	pdfclock \
#	invoice \
#	businesscard \
#	quickreference \
#	make_corrugmini

PROGS = make_template

all: $(PROGS)

install:
	cp make_template ../../../bin

install-test:
	cp make_template ../../../bin/make_template_test

clean:
	$(RM) $(PROGS) *.pdf *.o
