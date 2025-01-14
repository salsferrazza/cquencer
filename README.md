# cquencer
_Barebones unicast-multicast message sequencing_

## Synopsis

The `cquencer` is an ultra barebones unicast-muilticast network message sequencer,
written in C. 

`cquencer` adheres to a simple protocol and is designed to be
payload-agnostic. It listens for connections over TCP on a local
address and port. Each message received over that port is assigned a
sequence number and both the sequence number and the original message
payload are published to the specified multicast group with UDP and
length-prefixed message framing. 

## Building `cquencer`

```
% cd cquencer
% make
mkdir -p bin
rm -f bin/*
gcc -Wall -Werror -o bin/cq src/cq.c src/vector.c
gcc -Wall -Werror -o bin/listener src/listener.c
gcc -Wall -Werror -o bin/client src/client.c
undefined@Undefineds-MacBook-Pro cquencer % ls bin
client		cq		listener
% 
```

## Usage

- `cq` is the sequencer process. 

`cq <TCP listen port> <multicast group IP> <multicast group port>`

- `listener` is an example multicast listener that sends all sequenced
  messages as bytes to standard out.

`listener <multicast group IP> <multicast group port>`

- `client` is a shell that allows for interactive submission of
  plain-text messages.
  
  `client <IP of sequencer process> <port of sequencer process>` 

## Example

### Start the sequencer on port 3001

```
% cq 3001 239.0.0.1 1234
Listening on port 3001...
Current sequence number is 0
```

### Use client to send a message and receive sequence number reply

```
% bin/client 3001
> this is a message
server says: 1
> 
```

### ... or use netcat to blast random bytes to the sequencer – disregarding the response

```
% head -c$(( (RANDOM % 91) + 10 )) /dev/random| nc -c localhost 3001 
```

### Sequencer output

```
% cq 3001 239.0.0.1 1234
Listening on port 3001...
Current sequence number is 0
client 6 connected
1736820576 send # 1: pfx 2 msg 26 total 28 bytes: this is a message
client 7 connected
1736820713 send # 2: pfx 2 msg 49 total 51 bytes: f??
G'?"??|9 8?%,]??0??2??SL8~?e7???
handle_client_message(): send(): Broken pipe
```


