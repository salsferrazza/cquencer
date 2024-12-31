cc=gcc
flags=-Wall -Werror
src=src
bin=bin

all: setup clean $(bin)/cq $(bin)/listener $(bin)/sender

setup:
	mkdir -p $(bin)

clean:
	rm -f $(bin)/*

$(bin)/cq: $(src)/cq.c $(src)/vector.c
	$(cc) $(flags) -o $@ $^

$(bin)/listener: $(src)/listener.c
	$(cc) $(flags) -o $@ $^

$(bin)/sender: $(src)/sender.c
	$(cc) $(flags) -o $@ $^
