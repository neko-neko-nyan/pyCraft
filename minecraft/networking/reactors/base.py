import zlib

import select

from minecraft.networking import packets
from minecraft.networking.packets import clientbound, AbstractPluginMessagePacket
from minecraft.networking.types import VarInt


class PacketReactor(object):
    """
    Reads and reacts to packets
    """
    state_name = None

    # Handshaking is considered the "default" state
    get_clientbound_packets = staticmethod(clientbound.handshake.get_packets)

    @staticmethod
    def get_plugin_packets(context):
        return {}

    def __init__(self, connection):
        self.connection = connection
        context = self.connection.context
        self.clientbound_packets = {
            packet.get_id(context): packet
            for packet in self.__class__.get_clientbound_packets(context)}
        self.plugin_packets = {
            packet.get_channel(context): packet
            for packet in self.__class__.get_plugin_packets(context)}

    def read_packet(self, stream, timeout=0):
        # Block for up to `timeout' seconds waiting for `stream' to become
        # readable, returning `None' if the timeout elapses.
        ready_to_read = select.select([stream], [], [], timeout)[0]

        if ready_to_read:
            length = VarInt.read(stream)

            packet_data = packets.PacketBuffer()
            packet_data.send(stream.read(length))
            # Ensure we read all the packet
            while len(packet_data.get_writable()) < length:
                packet_data.send(
                    stream.read(length - len(packet_data.get_writable())))
            packet_data.reset_cursor()

            if self.connection.options.compression_enabled:
                decompressed_size = VarInt.read(packet_data)
                if decompressed_size > 0:
                    decompressor = zlib.decompressobj()
                    decompressed_packet = decompressor.decompress(
                                                       packet_data.read())
                    assert len(decompressed_packet) == decompressed_size, \
                        'decompressed length %d, but expected %d' % \
                        (len(decompressed_packet), decompressed_size)
                    packet_data.reset()
                    packet_data.send(decompressed_packet)
                    packet_data.reset_cursor()

            packet_id = VarInt.read(packet_data)

            # If we know the structure of the packet, attempt to parse it
            # otherwise, just return an instance of the base Packet class.
            if packet_id in self.clientbound_packets:
                packet = self.clientbound_packets[packet_id]()
                packet.context = self.connection.context
                packet.read(packet_data)

                if isinstance(packet, AbstractPluginMessagePacket) and packet.channel in self.plugin_packets:
                    packet = self.plugin_packets[packet.channel]()
                    packet.context = self.connection.context
                    packet.read(packet_data)

            else:
                packet = packets.Packet()
                packet.context = self.connection.context
                packet.id = packet_id
            return packet
        else:
            return None


    def react(self, packet):
        """Called with each incoming packet after early packet listeners are
           run (if none of them raise 'IgnorePacket'), but before regular
           packet listeners are run. If this method raises 'IgnorePacket', no
           subsequent packet listeners will be called for this packet.
        """
        raise NotImplementedError("Call to base reactor")

    def handle_exception(self, exc, exc_info):
        """Called when an exception is raised in the networking thread. If this
           method returns True, the default action will be prevented and the
           exception ignored (but the networking thread will still terminate).
        """
        return False
