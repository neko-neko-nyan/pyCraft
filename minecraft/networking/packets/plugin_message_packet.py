from minecraft.networking.types import String, VarInt
from . import PacketBuffer
from .packet import Packet
from ...utility import overridable_property


class AbstractPluginMessagePacket(Packet):
    """NOTE: Plugin channels were significantly changed, including changing the
       names of channels, between Minecraft 1.12 and 1.13 - see <http://wiki.vg
       /index.php?title=Pre-release_protocol&oldid=14132#Plugin_Channels>.
    """
    definition = [
        {'channel': String},
    ]

    @classmethod
    def get_channel(cls, _context):
        return getattr(cls, 'channel')

    @overridable_property
    def channel(self):
        return None if self.context is None else self.get_channel(self.context)

    def write(self, socket, compression_threshold=None):
        # buffer the data since we need to know the length of each packet's
        # payload
        packet_buffer = PacketBuffer()
        # write packet's id right off the bat in the header
        VarInt.send(self.id, packet_buffer)
        String.send(self.channel, packet_buffer)
        # write every individual field
        self.write_fields(packet_buffer)
        self._write_buffer(socket, packet_buffer, compression_threshold)
