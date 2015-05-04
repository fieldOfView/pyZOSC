#!/usr/bin/python3

import socket
from threading import Thread

from zocp import ZOCP
import OSC


class OscBridgeNode(ZOCP):
    # Constructor
    def __init__(self):
        self.client = None
        self.server = None

        self.receive_ip = "0.0.0.0"
        self.receive_port = 1234
        self.send_ip = "127.0.0.1"
        self.send_port = 1235

        super().__init__()


    def run(self):
        self.register_string("Receive ip", self.receive_ip, 'rw')
        self.register_int("Receive port", self.receive_port, 'rw')
        self.register_string("Send ip", self.send_ip, 'rw')
        self.register_int("Send port", self.send_port, 'rw')

        self.init_server(self.receive_ip, self.receive_port)
        self.init_client(self.send_ip, self.send_port)

        super().run()

        # Close down OSC after ZOCP has stopped running
        if self.client:
            self.client.close()
        if self.server:
            self.server.close()


    def on_modified(self, peer, name, data, *args, **kwargs):
        if self._running and peer:
            for key in data:
                if 'value' in data[key]:
                    self.receive_value(key)


    def on_peer_signaled(self, peer, name, data, *args, **kwargs):
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
            # any other capability is mirrored to OSC
            if key[0] != '/':
                # make sure the capability name looks like an OSC path
                key = '/' + key
            self.send_message(key, [new_value])

        if reinit_receive:
            self.init_server(self.receive_ip, self.receive_port)

        elif reinit_send:
            self.init_client(self.send_ip, self.send_port)


    def init_client(self, address, port):
        if self.client is not None:
            self.client.close()

        print("Connect client to %s:%s" %(address, port))
        self.client = OSC.OSCClient()
        self.client.connect((address, port))


    def init_server(self, address, port):
        if self.server is not None:
            self.server.close()

        print("Start server on %s:%s" %(address, port))
        self.server = OSC.OSCServer((address, port))
        self.server.addMsgHandler("default", self.message_handler)
        serverThread = Thread( target = self.server.serve_forever )
        serverThread.setDaemon(True)
        serverThread.start()


    def send_message(self, addr, stuff):
        osc_message = OSC.OSCMessage()
        osc_message.setAddress(addr)
        osc_message.append(stuff)
        if self.client:
            try:
                self.client.send(osc_message, 1)
            except:
                print("Could not send message to OSC server")
                self.client.close()
                self.client = None


    def message_handler(self, addr, tags, stuff, source):
        if not (type(stuff) is list and len(stuff)>0):
            # ignore messages without data
            return

        if not addr in self.capability:
            # add ZOCP capability for each path
            if tags == 'f' or tags == 'd':
                self.register_float(addr, 0, 'rwes')
            elif tags == 'ff' or tags == 'dd':
                self.register_vec2f(addr, [0,0], 'rwes')
            elif tags == 'fff' or tags == 'ddd':
                self.register_vec3f(addr, [0,0,0], 'rwes')
            elif tags == 'ffff' or tags == 'dddd':
                self.register_vec4f(addr, [0,0,0,0], 'rwes')

            elif tags == 'i':
                self.register_int(addr, 0, 'rwes')
            else:
                self.register_string(addr, "", 'rwes')

        type_hint = self.capability[addr]['typeHint']

        if type_hint.startswith("vec"):
            data = stuff
        else:
            data = stuff[0]

        self.emit_signal(addr, data)



if __name__ == '__main__':
    z = OscBridgeNode()
    z.set_name("zosc_brigde@%s" % socket.gethostname())

    z.start()
    z.run()
    print("ZOCP Stopped")
