# cquencer
The simplest possible network message sequencer (written in C).

Requirements:

- Listens on TCP port
- Clients connect, socket open
- Send length-prefixed messages
- cquencer responds with sequence # of message to client
- cquencer sends out length-prefixed datagrams to a configured multicast group, with a sequence number (in UDP header?)
- separate control port that returns the just the latest sequence number
- heartbeat message is a length-prefixed message of 0
- metadata: source IP of client message originator?
- no local storage
- zero-copy byte arrays from client to network (socket file descriptor [TCP] to socket file descriptor [UDP])
- enforce bind process to core

- uses only RAM, compute and network

`cq <tcp address to listen on> <multicast group to join and publish>`

e.g. `cq 9000 239.0.0.1`

Failover / live migration:
https://www.criu.org/Simple_TCP_pair

- Sequence # vanishes with the process
- All administrative facilities must be out of band (failover, message archival)

Maybe use https://criu.org/Main_Page for cquencer failover? VM needs to be checkpointed and restored continually? Maybe failover mode gets to start at last known sequence # vs. reset?
