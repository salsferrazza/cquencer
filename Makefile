cc=gcc
flags=-Wall -Werror
src=src
bin=bin

all: setup clean $(bin)/cq

setup:
	mkdir -p $(bin)

clean:
	rm -f $(bin)/*

$(bin)/cq: $(src)/cq.c $(src)/vector.c
	$(cc) $(flags) -o $@ $^

