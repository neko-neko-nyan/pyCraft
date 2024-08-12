from minecraft.networking.packets import serverbound
from minecraft.networking.types import String, Byte, VarInt, Enum

class ServerHandshakePhase(Enum):
    START = 0
    HELLO = 1
    WAITINGCACK = 2
    COMPLETE = 3
    DONE = 4
    ERROR = 5


class ServerboundFMLHSPacket(serverbound.play.PluginMessagePacket):
    channel = 'FML|HS'


class ClientHello(ServerboundFMLHSPacket):
    Discriminator = 1
    definition = [
        {'Discriminator': Byte},
        {'FMLProtocolVersion': Byte},
    ]

    fields = 'FMLProtocolVersion',


class ClientModList(ServerboundFMLHSPacket):
    Discriminator = 2
    definition = [
        {'Discriminator': Byte},
    ]

    fields = 'Mods',

    def write_fields(self, packet_buffer):
        super().write_fields(packet_buffer)
        VarInt.send_with_context(len(self.Mods), packet_buffer, self.context)
        for name, version in self.Mods:
            String.send_with_context(name, packet_buffer, self.context)
            String.send_with_context(version, packet_buffer, self.context)


class ClientHandshakeAck(ServerboundFMLHSPacket):
    packet_name = "FML|HS:ClientHandshakeAck"

    Discriminator = -1

    definition = [
        {'Discriminator': Byte},
        {'Phase': Byte}
    ]


class ClientHandshakePhase(Enum):
    START = 0
    HELLO = 1
    WAITINGSERVERDATA = 2
    WAITINGSERVERCOMPLETE = 3
    PENDINGCOMPLETE = 4
    COMPLETE = 5
    DONE = 6
    ERROR = 7
