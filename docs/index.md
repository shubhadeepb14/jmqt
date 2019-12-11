## What is JMQT?

JMQT is a publish-subscribe based IoT and messaging protocol. JMQT protocol is open & free, and can be used without any license agreement. No one owns JMQT.

JMQT version 1.0 has been released in December, 2018. 

### Why JMQT was developed?

JMQT has been developed to **simplify** and **modernize** the **publish-subscribe** based messaging systems. JMQT uses **JSON** packets for data exchange which minimizes the learning curve for the developers and can speed up the development cycle. JSON is natively supported in almost every major programming language which makes the parsing and formatting the JMQT packets easier. 

JMQT supports **P2P** (Point to Point) messaging in addition to publish-subscribe based messaging. This feature allows the programmers to develop robust solutions (for example, IoT or messenger applications) which needs point to point communication between the clients.

### Principles of JMQT 

- JMQT is a **publish-subscribe** based messaging system which uses JSON packets for data exchange.

- JMQT is a **text based** (more precisely, JSON text) protocol and works on top of TCP/IP.

- JMQT has **modernized** the authentication system using **Authentication Token** on the contrary to the other IoT protocols which use conventional user id and password (such as MQTT). 

- JMQT can be useful in **IoT**, **messengers** or other **real-time remote messaging** solutions where the a client needs to distribute a message among multiple remote clients or send a message directly to a remote client without interfering the other clients.

- JMQT supports **Point to Point** Messaging enabling the clients to send direct messages to a remote client.

- JMQT clients can send **Control Messages** which works like HTTP APIs, i.e. the server processes the control messages and replies back with some data which the clients may need.

- JMQT is **not** designed for **low bandwidth** networks, though the size of the JMQT packets can be as small as 10 Bytes. JMQT packets needs more memory and bandwidth than the byte-based protocols (e.g. MQTT) because of its text-based nature.


### Versions and Documentation

Version 1.0
Released on December, 2018

[Download Protocol Documentation](https://github.com/shubhadeepb14/jmqtdoc/raw/master/JMQT_1_0_Specifications.pdf)
 

### Implementation

An open source implementation of JMQT is available. [Click here](https://github.com/shubhadeepb14/jmqt) to visit the repository.

 

### Stay Connected

To become a part of the JMQT community, you can subscribe to our newsletter below. You can also find us on twitter @jmqtorg.
