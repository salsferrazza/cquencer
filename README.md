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

## Rationale

The `cquencer` authors are proponents of the [Sequencer Architecture](https://electronictradinghub.com/an-introduction-to-the-sequencer-world/]) commonly found in electronic trading systems. While patterns like event-sourcing have gained more traction in recent years, we are of the opinion that the industry would benefit from more awareeness around the benefits of sequencer architectures. 

Current options tend to be commercial or attached to a larger solution that does much more than sequencing. Additionally, there is a heavy bias towards Java. There are no options for a simple network message sequencer unbundled from a larger or more vertically-specific package. 

Enter `cquencer`.

`cq`, the sequencer binary, compiles to just over 50K. It's job: accept bytes over TCP, prepend a sequence number to those bytes, and send the sequenced bytes to a multicast group.

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
>^C 
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

### Multicast listener

The `listener` binary simply streams all bytes received from the specified multicast group over UDP and sends them to standard output. 

```
% cq 3001 239.0.0.1 1234 > cq.log &
% bin/listener 239.0.0.1 1234 > tmp.bin &
% ls -la tmp.bin 
-rw-r--r--  1 undefined  staff  0 Jan 
% bin/client 3001
> this is a message
server says: 1
>^C
undefined@Undefineds-MacBook-Pro cquencer % cat cq.log 
Listening on port 3001...
Current sequence number is 0
client 6 connected
1736826518 send # 1: pfx 2 msg 23 total 25 bytes: this a message
client 6 disconnected
% ls -al tmp.bin 
-rw-r--r--  1 undefined  staff  25 Jan 13 22:48 tmp.bin
```

