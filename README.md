# cquencer
_A central sequence number server_

## Synopsis

The `cquencer` is a standalone central sequence number server, embodying the "Fixed Sequencer" 
ordering mechanism described by [Défago, et al](https://infoscience.epfl.ch/server/api/core/bitstreams/068f8add-50ce-4216-b750-3cde412ee397/content) (2004). 

<img width="2126" height="1146" alt="image" src="https://github.com/user-attachments/assets/953d9c36-3f9d-4a72-b29b-54ceaa3c543f" />

`cquencer` adheres to a simple protocol and is payload-agnostic. It
listens for connections over TCP on a local address and port. Each message received over that port is assigned a
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

TCP clients, upon sequencing of the message, are returned an
ASCII-encoded sequence number as the only response. Messages sent with
no content are returned the current sequence number and do not mutate
the stream.

The message sent to the multicast group is framed as a nested [netstring](https://en.wikipedia.org/wiki/Netstring). The entire contents of the multicast message is itself a netstring that is composed of two child netstrings. The first child netstring contains the sequence number. The second child netstring contains the original message bytes, undisturbed. For example:

TCP Sender:
```
% bin/sendr 3001
? <RET> 
# 5:85636,
? hello world
# 5:88485,
? 
```

UDP Destination:
```
% bin/destn 239.0.0.1 1234
23:5:88485,11:hello world,,
```

## Why netstring?

One principle of `cquencer` is that there should be no need for the sequencer to inspect or modify the contents of any message payloads submitted. Thus, where to apply the sequence number of outbound sequenced messages becomes a challenge to overcome. 

Length-prefixed binary was the initial instinct for output encoding, and functionally this approach would be most efficient. However, it is possible that developers who are not accustomed to dealing with binary encodings may find that an obstacle to getting started, especially if the message payloads they are currently represented as text.

Netstrings might be viewed as training wheels for length-prefixed binary encodings. The length and payload delimiters are in plain-text and easy to keep track of visually while sniffing network traffic or inspecting messages saved to a file. The use of netstrings doesn't preclude employing binary encoding of message payloads, so applications may leverage their existing encodings without adjustments. Developers new to sequencer architecture will likely find netstring encoding easier to work with as opposed to binary length-prefixing.

The ability to nest netstrings provided a simple, clear solution for representing sequence numbers alongside the originally submitted payload, without having to crack messages open affirmatively to prepend a sequence number.  This allows the sequenced message to retain the bit identity of the original payload, without interfering with any requisite hash or checksum validation of submitted messages downstream.

However, netstrings do come with several drawbacks. The first is efficiency. Netstring encodings simply require more bytes on the wire than an equivalent binary encoding. In particular, the delimiters being represented with ASCII characters add several bytes to each message. 

In addition, netstring payloads yield more variability in the size of payloads per message. For example, a value of `1` encoded as a netstring yields:

```
1:1,
```

which is four bytes. The equivalent binary value would always yield 10 bytes (eight for the 64-bit integer + two for the length prefix) on the wire. For values in the lower range, netstrings are actually more compact on the wire. This assessment, though, ignores the additional encoding and decoding compute required at the source and destination. 

However, As the sequence number increases, the footprint on the sequenced netstring also increases.  The maximum value of a 64-bit unsigned integer is `18446744073709551615`. As a netstring, this becomes:

```
20:18446744073709551615,
```

Which increases the footprint of the transmitted netstring to 24 bytes. A binary encoding would remain at 10 bytes throughout the entire range of values sent over the wire.

Future revisions of `cquencer` will look to parameterize encoding strategies such that users may select from a choice of codecs for sequenced messages. 

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

- `cq` is the sequencer binary. 

```
cq: a fixed sequencer for atomic broadcast

Usage: cq <tcp port> <multicast group> <multicast port>
  Messages submitted over TCP are multicast
  to the specified group and port, using nested
  netstring framing
  ```

- `destn` is an example multicast destination that logs all received
  data to `STDOUT`


`destn <multicast group IP> <multicast group port>`

- `sendr` is a shell that allows for interactive submission of
  plain-text messages.

`sendr <port of sequencer process>` 

## Acknowledgements

## See also
