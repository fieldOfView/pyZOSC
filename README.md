pyZOSC
======

Provides a bridge between OSC and the ZOCP network.

Data received from OSC on the specified port/network are emitted 
to the ZOCP network. New capabilities are automatically added to 
the node when an OSC message is received with a new address/path. 

Capability values from ZOCP are sent out the a connected OSC
server, with the address/path name mirroring the ZOCP capability
(prefixed with ´/' if necessary).
