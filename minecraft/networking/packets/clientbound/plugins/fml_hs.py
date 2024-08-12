from minecraft.networking.packets.clientbound.play import PluginMessagePacket
from minecraft.networking.types import Byte, String, VarInt, Boolean, Integer


class ClientboundFMLHSPacket(PluginMessagePacket):
    channel = 'FML|HS'

    definition = [
        {'Discriminator': Byte},
    ]

    __packets = {}

    def read(self, file_object):
        Discriminator = Byte.read(file_object)

        if Discriminator == 0:
            self.packet_name = "FML|HS:ServerHello"
            self.FMLProtocolVersion = Byte.read(file_object)
            if self.FMLProtocolVersion > 1:
                self.OverrideDimension = Integer.read(file_object)
            else:
                self.OverrideDimension = None

        elif Discriminator == 2:
            self.packet_name = "FML|HS:ServerModList"
            count = VarInt.read(file_object)
            self.Mods = []
            for _ in range(count):
                name = String.read(file_object)
                version = String.read(file_object)
                self.Mods.append((name, version))

        elif Discriminator == 3:
            self.packet_name = "FML|HS:RegistryData"

            self.HasMore = Boolean.read(file_object)
            self.Name = String.read(file_object)

            count = VarInt.read(file_object)
            self.Ids = []
            for _ in range(count):
                name = String.read(file_object)
                id = VarInt.read(file_object)
                self.Ids.append((name, id))

            count = VarInt.read(file_object)
            self.Substitutions = []
            for _ in range(count):
                name = String.read(file_object)
                self.Substitutions.append(name)

            self.Dummies = []
            if not file_object.is_eof():
                count = VarInt.read(file_object)
                for _ in range(count):
                    name = String.read(file_object)
                    self.Dummies.append(name)

        elif Discriminator == -1:
            self.packet_name = "FML|HS:ServerHandshakeAck"
            self.Phase = Byte.read(file_object)
