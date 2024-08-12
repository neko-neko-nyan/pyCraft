from minecraft.networking.packets import clientbound, serverbound
from minecraft.networking.packets.serverbound.plugins import fml_hs
from minecraft.networking.reactors import PacketReactor


class PlayingReactor(PacketReactor):
    get_clientbound_packets = staticmethod(clientbound.play.get_packets)
    get_plugin_packets = staticmethod(clientbound.plugins.get_packets)

    def react(self, packet):
        if packet.packet_name == "set compression":
            self.connection.options.compression_threshold = packet.threshold
            self.connection.options.compression_enabled = True

        elif packet.packet_name == "keep alive":
            keep_alive_packet = serverbound.play.KeepAlivePacket()
            keep_alive_packet.keep_alive_id = packet.keep_alive_id
            self.connection.write_packet(keep_alive_packet)

        elif packet.packet_name == "player position and look":
            if self.connection.context.protocol_later_eq(107):
                teleport_confirm = serverbound.play.TeleportConfirmPacket()
                teleport_confirm.teleport_id = packet.teleport_id
                self.connection.write_packet(teleport_confirm)
            else:
                position_response = serverbound.play.PositionAndLookPacket()
                position_response.x = packet.x
                position_response.feet_y = packet.y
                position_response.z = packet.z
                position_response.yaw = packet.yaw
                position_response.pitch = packet.pitch
                position_response.on_ground = True
                self.connection.write_packet(position_response)
            self.connection.spawned = True

        elif packet.packet_name == "disconnect":
            self.connection.disconnect()

        elif packet.packet_name == "REGISTER:":
            resp = serverbound.plugins.RegisterPluginMessagePacket()
            resp.channels = packet.channels
            self.connection.write_packet(resp)

        elif packet.packet_name == "UNREGISTER:":
            resp = serverbound.plugins.UnregisterPluginMessagePacket()
            resp.channels = packet.channels
            self.connection.write_packet(resp)

        elif packet.packet_name == "FML|HS:ServerHello":
            resp = fml_hs.ClientHello()
            resp.FMLProtocolVersion = packet.FMLProtocolVersion
            self.connection.write_packet(resp)

            resp = fml_hs.ClientModList()
            resp.Mods = self.connection.context.fml_mods
            self.connection.write_packet(resp)

        elif packet.packet_name == "FML|HS:ServerModList":
            resp = fml_hs.ClientHandshakeAck()
            resp.Phase = fml_hs.ClientHandshakePhase.WAITINGSERVERDATA
            self.connection.write_packet(resp)

        elif packet.packet_name == "FML|HS:RegistryData":
            if not packet.HasMore:
                resp = fml_hs.ClientHandshakeAck()
                resp.Phase = fml_hs.ClientHandshakePhase.WAITINGSERVERCOMPLETE
                self.connection.write_packet(resp)

        elif packet.packet_name == "FML|HS:ServerHandshakeAck":
            if packet.Phase == fml_hs.ServerHandshakePhase.WAITINGCACK:
                resp = fml_hs.ClientHandshakeAck()
                resp.Phase = fml_hs.ClientHandshakePhase.PENDINGCOMPLETE
                self.connection.write_packet(resp)
            elif packet.Phase == fml_hs.ServerHandshakePhase.COMPLETE:
                resp = fml_hs.ClientHandshakeAck()
                resp.Phase = fml_hs.ClientHandshakePhase.COMPLETE
                self.connection.write_packet(resp)

        elif isinstance(packet, clientbound.play.PluginMessagePacket):
            print(packet)
