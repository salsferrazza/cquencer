# Use case: inventory management

_"Customers expect retailers to have real-time knowledge of stock availability"_

To illustrate the use of `cq` and sequencer architectures more broadly, a simple use case is presented where a point-of-sale and fulfillment center maintain shared view of inventory levels. Using a sequencer architecture, we can ensure that no orders will be placed for a quantity of items larger than what is fulfillable by the warehouse at any moment.  

The key feature that a sequencer architecture enables is a consistent view of the amount of inventory available, discretized by point-in-time sequence number, available to every application.

The warehouse broadcasts mutations to each SKU's inventory level (increment or decrement) to the network, so that points-of-sale can avoid booking against phantom inventory. Point-of-sale systems send orders to the network and upon receiving the order, the warehouse decrements it's inventory count and broadcasts the new value to all systems. Points-of-sale are written to check existing inventory before sending an order to the network. 
The warehouse is written to check itsw own inventory levels before accepting an order and sequencing the inventory decrement to the network.

# Characteristics of sequencer architectures 

While cquencer provides a fixed sequencer module, this by itself is a necessary but insufficient component of the classic sequencer architecture. Other important characteristics found in these systems include:

## Shared message schema

The schema represents the collection of _message types_ that flow over the sequenced stream. Each message payload contains a message type identifier as a field. In many cases, a particular application will only operate on a subset of the message types on the stream, ignoring the rest. Similarly, any individual application may only produce a subset of the message types represented by the schema.

The example uses a simple message schema, consisting of whitespace-delimited encoding of field values and three distinct message types, consisting of the same three fields. 

- *Inventory*

This instructs applications to replace their entire level for a particular SKU with the value transmitted in the messages quantity field. The integer values of the quantity field are unsigned.

`I <qty> <sku>`

- *Inventory delta*

This instructs applications to apply the value transmitted in the quantity field to the current levels it has for the specified SKU. The integer values of the quantity field are signed. 

`D <qty> <sku>`

- *Order*

This instructs the warehouse to process an order for the demanded quantity of the SKU. If the order is successfully processed, the warehouse will follow up with a inventory delta message that instructs the network to decrement the available levels of the specified SKU.

`O <qty> <sku>`

## Efficient representation of message payloads and encodings

Stock exchange binary feeds are one example. Everyone knows `AAPL` but if you are talking directly to the exchange you better know the `SecurityId` as well, which is expressed as an integer. The exchange provides the symbol reference data en masse before trading sessions, then individually if a specific entity mutates intra-session. 

The largest message in Nasdaq's TotalView ITCH 5.0 feed is 50 bytes. A JSON encoding of a semantically identical message could be in the range of 300-400 bytes. The self-describing schema embedded with the encoding degrades the signal-to-byte ratio considerably. We call this class of encoding "high-context", with YAML being the cleanest shirt in a laundry basket dominated by XML and JSON. 

As Ron Minsky of Jane Street puts it: "[these] messages actually pack a lot of punch, right? Part of the way that you optimize the system like this is you try and have a fairly concise encoding of the data that you actually stick on the network. So you can have pretty high transaction rates with a fairly small number of bytes per transaction."

In this example., messages run about 20 bytes each, and are represented using a compact, CSV-style ASCII encoding. The only three columns in use are: message type, quantity and SKU.

## Foundation classes abstract sequenced stream management from the application

We find this particular architectural characteristic more emblematic of sequencer architectures than the sequencer module itself. It lets applications ignore the particulars around stream management and simply provide application logic in response to inbound messages. Inbound messages arrive over multicast and trigger an `on_message()` event within the generic `Destination` superclass and its subclasses. Subclasses of `Destination` get more and more domain-specific as the hierarchy descends. An `InventoryDestination` is a class derived from `Destination`. `InventoryDestination` overrides `on_message()`, and defers to two new methods it introduces to its lineage: `on_inventory` and `on_inventory_delta`, that get invoked after `InventoryDestination`'s `on_message()` implementation identifies the message type of any inbound message. 

## Inbound messages are dispatched to applications as domain-specific events

The sequenced stream abstraction typically does not need to leak into the application. The business logic of the application relies on the sequencing of individual messages, but the logic itself is triggered by events aligned to the problem domain. For a typical class hierarchy, the sequence number is a characteristic of the _message_ abstraction, but application code generally works at the abstraction level of individual business events. The sequence number itself is part of the envelope, not the payload.

## One process, one thread

Sequencer architectures are a solution to coordinate _inherently sequential_ workloads. These are the polar opposite of map/reduce style embarrassingly parallel workloads. Applications designed with sequencer architectures coordinate events coming from distributed network peers that all require a consistent view of single state machine, yet mutable by sequenced stream publishers.








