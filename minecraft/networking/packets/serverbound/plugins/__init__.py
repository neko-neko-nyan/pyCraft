from minecraft.networking.packets.serverbound.play import PluginMessagePacket
from minecraft.networking.types import String


class RegisterPluginMessagePacket(PluginMessagePacket):
    @classmethod
    def get_channel(cls, context):
        return "minecraft:register" if context.protocol_later_eq(393) else "REGISTER"

    packet_name = "REGISTER:"

    fields = 'channels',

    def read(self, file_object):
        channels = String.read_with_context(file_object, self.context)
        self.channels = channels.split('\0')

    def write_fields(self, packet_buffer):
        channels = '\0'.join(self.channels)
        String.send_with_context(channels, packet_buffer, self.context)


class UnregisterPluginMessagePacket(PluginMessagePacket):
    @classmethod
    def get_channel(cls, context):
        return "minecraft:unregister" if context.protocol_later_eq(393) else "UNREGISTER"

    packet_name = "UNREGISTER:"

    fields = 'channels',

    def read(self, file_object):
        channels = String.read_with_context(file_object, self.context)
        self.channels = channels.split('\0')

    def write_fields(self, packet_buffer):
        channels = '\0'.join(self.channels)
        String.send_with_context(channels, packet_buffer, self.context)
