import json
import time

from minecraft.networking.packets import clientbound, serverbound
from minecraft.networking.reactors import PacketReactor


class StatusReactor(PacketReactor):
    get_clientbound_packets = staticmethod(clientbound.status.get_packets)

    def __init__(self, connection, do_ping=False):
        super(StatusReactor, self).__init__(connection)
        self.do_ping = do_ping

    def react(self, packet):
        if packet.packet_name == "response":
            status_dict = json.loads(packet.json_response)
            if self.do_ping:
                ping_packet = serverbound.status.PingPacket()
                # NOTE: it may be better to depend on the `monotonic' package
                # or something similar for more accurate time measurement.
                ping_packet.time = time.monotonic_ns()
                self.connection.write_packet(ping_packet)
            else:
                self.connection.disconnect()
            self.handle_status(status_dict)

        elif packet.packet_name == "ping":
            if self.do_ping:
                now = time.monotonic_ns()
                self.connection.disconnect()
                self.handle_ping(now - packet.time)

    def handle_status(self, status_dict):
        print(status_dict)

    def handle_ping(self, latency_ms):
        print('Ping: %d ms' % latency_ms)