pyZOSC
======

Provides a bridge between OSC and the ZOCP network.

Data received from OSC on the specified port/network are emitted 
to the ZOCP network. New capabilities are automatically added to 
the node when an OSC message is received with a new address/path. 

Capability values from ZOCP are sent out the a connected OSC
server, with the address/path name mirroring the ZOCP capability
(prefixed with ´/' if necessary).


pyOSC
-----

Includes pyOSC 0.3.6
Copyright (c) Daniel Holth & Clinton McChesney. (SimpleOSC)  
Copyright (c) 2008-2010, Artem Baguinski <artm@v2.nl> et al., Stock, V2_Lab, Rotterdam, Netherlands.  
Copyright (c) 2010 Uli Franke <uli.franke@weiss.ch>, Weiss Engineering, Uster, Switzerland.


Testing
-------

To test, you need something that sends out OSC, and something
that receives OSC. Many tools can do both at the same time
(eg Touch OSC), but they don't necessarily have to be on the
same machine.

Start both urwZOCP.py and zosc.py with Python3. In the
urwid-monitor you will see node named zosc_bridge@HOSTNAME.
Use urwid to set the 'send ip' to the ip of the machine
where you want to send OSC messages to. Leave at 127.0.0.1
if the OSC receiver is an application on the same machine as
the ZOSC node.The 'receive ip' should probably be left at
0.0.0.0, so it can receive from any source. Be sure to fill
in the ports to the values your OSC apps need.

Now send some OSC data. You should see a new capability
appear on the ZOSC node, reflecting the data. If you use urwid
to change one of those values, the new value will be sent to
the OSC address/port specified.

