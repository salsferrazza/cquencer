cc=gcc
flags=-Wall -Werror
src=src
bin=bin

all: setup clean $(bin)/cq $(bin)/listener $(bin)/client

setup:
	mkdir -p $(bin)

clean:
	rm -f $(bin)/*

$(bin)/cq: $(src)/cq.c $(src)/vector.c
	$(cc) $(flags) -o $@ $^

$(bin)/listener: $(src)/listener.c
	$(cc) $(flags) -o $@ $^

$(bin)/client: $(src)/client.c
	$(cc) $(flags) -o $@ $^
