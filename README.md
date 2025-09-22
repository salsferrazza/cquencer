# cquencer
_A central sequence number server_

## Synopsis

The `cquencer` is a standalone central sequence number server, embodying the "Fixed Sequencer" 
ordering mechanism described by [Défago, et al](https://infoscience.epfl.ch/server/api/core/bitstreams/068f8add-50ce-4216-b750-3cde412ee397/content) (2004). 

<img width="1786" height="1806" alt="image" src="https://github.com/user-attachments/assets/12104b42-c239-44ce-bd40-a135e481fe7c" />



`cquencer` adheres to a simple protocol and is payload-agnostic. It listens for connections over TCP on a local
address and port. Each message received over that port is assigned a
sequence number and both the sequence number and the original message
payload are published to the specified multicast group over UDP. 

## Rationale

The `cquencer` authors are proponents of the [Sequencer
Architecture](https://electronictradinghub.com/an-introduction-to-the-sequencer-world/])
commonly found in electronic trading systems. While adjacent patterns
such as [event-sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) have gained traction in recent years, we are of
the opinion that the world could use more advocacy and open-source tooling to
more clealry illustrate the benefits of sequencer architectures. 

The currently available options tend to be commercial or attached to a
larger solution that does much more than sequencing. Additionally,
the existing tools bias toward Java as a host language. There are no
clear options for a network message sequencer unbundled from a larger or more vertically-specific package. 

Enter `cquencer`.

`cq`, the sequencer binary, compiles to just over 50K. It's job:
accept bytes over TCP, prepend a sequence number to those bytes, and
send the sequenced bytes to its specified multicast group.

## Protocol

The `cquencer` accepts any data over its TCP port as a discrete
message.

TCP clients, upon sequencing of the message, are returned an ASCII-encoded sequence number as the only response. 

The message sent to the multicast group is encoded as a nested [netstring](https://en.wikipedia.org/wiki/Netstring). The entire contents of the multicast message is itself a netstring that is composed of two child netstrings. The first child netstring contains the sequence number. The second child netstring contains the original message bytes, undisturbed. For example:

TCP Sender:
```
% bin/sendr 3001
? hello world
# 83761
```

UDP Destination:
```
% bin/destn 239.0.0.1 1234
23:5:83761,11:hello world,,
```

## Building `cquencer`

```
% cd cquencer
%  make
mkdir -p bin
rm -f bin/*
gcc -Wall -Werror -o bin/cq src/cq.c src/vector.c
gcc -Wall -Werror -o bin/destn src/destn.c
gcc -Wall -Werror -o bin/sendr src/sendr.c
% ls -l bin
total 248
-rwxr-xr-x  1 sal  staff  52848 Aug  3 16:26 cq
-rwxr-xr-x  1 sal  staff  34024 Aug  3 16:26 destn
-rwxr-xr-x  1 sal  staff  34472 Aug  3 16:26 sendr
%
```

## Usage

- `cq` is the sequencer process. 

`cq <TCP listen port> <multicast group IP> <multicast group port>`

- `destn` is an example multicast destination that logs each message's
sequence number and size

`destn <multicast group IP> <multicast group port>`

- `sendr` is a shell that allows for interactive submission of
  plain-text messages.

`sendr <IP of sequencer process> <port of sequencer process>` 

## Acknowledgements

## See also
