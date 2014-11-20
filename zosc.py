#!/usr/bin/python3

import sys
import time
import socket
import signal
from threading import Thread
import queue

from zocp import ZOCP
import OSC


class OscBridgeNode(ZOCP):
    # Constructor
    def __init__(self, nodename = "", to_osc = None, from_osc = None):
        self.nodename = nodename
        self.to_osc = to_osc
        self.from_osc = from_osc

        self.receive_ip = "0.0.0.0"
        self.receive_port = 1234
        self.send_ip = "127.0.0.1"
        self.send_port = 1235

        super().__init__()


    def run(self):
        self.set_name(self.nodename)
        self.register_string("Receive ip", self.receive_ip, 'rw')
        self.register_int("Receive port", self.receive_port, 'rw')
        self.register_string("Send ip", self.send_ip, 'rw')
        self.register_int("Send port", self.send_port, 'rw')

        to_osc.put(['__init_receive__', (self.receive_ip, self.receive_port)])
        to_osc.put(['__init_send__', (self.send_ip, self.send_port)])

        super().run()


    def on_modified(self, data, peer=None):
        if self._running and peer:
            for key in data:
                if 'value' in data[key]:
                    self.receive_value(key)


    def on_peer_signaled(self, peer, data, *args, **kwargs):
        if self._running and peer:
            self.receive_value(data[0])


    def receive_value(self, key):
        new_value = self.capability[key]['value']

        # check for changes in sending and receiving ip/port
        reinit_receive = False
        reinit_send = False
        if key == "Receive ip":
            if new_value != self.receive_ip:
                self.receive_ip = new_value
                reinit_receive = True
        elif key == "Receive port":
            if new_value != self.receive_port:
                self.receive_port = new_value
                reinit_receive = True
        elif key == "Send ip":
            if new_value != self.send_ip:
                self.send_ip = new_value
                reinit_send = True
        elif key == "Send port":
            if new_value != self.send_port:
                self.send_port = new_value
                reinit_send = True
        else:
            if key[0] != '/':
                key = '/' + key
            to_osc.put([key, (new_value, self.capability[key]['typeHint']) ])   

        if reinit_receive:
            to_osc.put(['__init_receive__', (self.receive_ip, self.receive_port)])
        elif reinit_send:
            to_osc.put(['__init_send__', (self.send_ip, self.send_port)])


    def from_osc_loop(self):
        self._osc_loop = True
        while self._osc_loop:
            while not self.from_osc.empty():
                message = self.from_osc.get()
                addr = message[0]
                (stuff, tags) = message[1]
                # ignore messages without data
                if not (type(stuff) is list and len(stuff)>0):
                    continue

                if not addr in self.capability:
                    # add ZOCP capability for each path
                    if tags == 'f':
                        self.register_float(addr, 0, 'rw')
                    else:
                        self.register_string(addr, "", 'rw')
                self.emit_signal(addr, stuff[0])
        print("From OSC Loop stopped")

    def stop_from_osc_loop(self):
        self._osc_loop = False



class OSCTransceiver:
    # Constructor
    def __init__(self, to_osc, from_osc):
        self.to_osc = to_osc
        self.from_osc = from_osc
        self.client = None
        self.server = None
        pass

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            while not self.to_osc.empty():
                message = self.to_osc.get()
                if message[0]=='__init_receive__':
                    (address, port) = message[1]
                    self.initServer(address, port)
                elif message[0]=='__init_send__':
                    (address, port) = message[1]
                    self.initClient(address, port)
                else:
                    msg = OSC.OSCMessage()
                    addr = message[0]
                    (stuff, typehint) = message[1]
                    msg.setAddress(addr)
                    msg.append([stuff])
                    print(msg)
                    self.client.send(msg)

        print("OSCTransceiver stopped")

    def initClient(self, address, port):
        print("Start client on %s:%s" %(address, port))
        if not self.client is None:
            self.client.close()
        self.clientAddress = address
        self.clientPort = port

        self.clientThread = Thread( target = self.connectClient )
        self.clientThread.start()

    def connectClient(self):
        self.client = OSC.OSCClient()
        self.client.connect((self.clientAddress, self.clientPort))

    def initServer(self, address, port):
        print("Start server on %s:%s" %(address, port))
        if not self.server is None:
            self.server.close()

        self.server = OSC.OSCServer((address, port))
        self.server.addMsgHandler("default", self.messageHandler)
        self.serverThread = Thread( target = self.server.serve_forever )
        self.serverThread.start()

    # define a message-handler function for the server to call.
    def messageHandler(self, addr, tags, stuff, source):
        self.from_osc.put([addr, (stuff,tags)])




if __name__ == '__main__':
    to_osc = queue.Queue()
    from_osc = queue.Queue()

    z = OscBridgeNode("zosc_brigde@%s" % socket.gethostname(), to_osc, from_osc)

    loop_thread = Thread(target = z.from_osc_loop)
    loop_thread.start()

    o = OSCTransceiver(to_osc, from_osc)
    o_thread = Thread(target = o.run)
    o_thread.start()

    # Add SIGINT handler for killing the threads
    def signal_handler(signal, frame):
        print ("Caught Ctrl+C, shutting down...")
        o.stop()
        z.stop_from_osc_loop()

        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

    z.run()
    print("ZOCP Stopped")
