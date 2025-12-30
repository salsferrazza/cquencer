cc=gcc
flags=-Wall -Werror
src=src
bin=bin

all: setup clean $(bin)/cq $(bin)/destn $(bin)/sendr

install:
	@mkdir -p /opt/cq/bin
	@cp $(bin)/cq $(bin)/destn $(bin)/sendr /opt/cq/bin
	@echo cq binaries installed to /opt/cq/bin

setup:
	mkdir -p $(bin)

clean:
	rm -f $(bin)/*

$(bin)/cq: $(src)/cq.c $(src)/vector.c
	$(cc) $(flags) -o $@ $^

$(bin)/destn: $(src)/destn.c
	$(cc) $(flags) -o $@ $^

$(bin)/sendr: $(src)/sendr.c
	$(cc) $(flags) -o $@ $^
