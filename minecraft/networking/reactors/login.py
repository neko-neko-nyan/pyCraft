import json
import re

from minecraft.exceptions import LoginDisconnect
from minecraft.networking import encryption
from minecraft.networking.packets import clientbound, serverbound
from minecraft.networking.reactors import PacketReactor, PlayingReactor


class LoginReactor(PacketReactor):
    get_clientbound_packets = staticmethod(clientbound.login.get_packets)

    def react(self, packet):
        if packet.packet_name == "encryption request":

            secret = encryption.generate_shared_secret()
            token, encrypted_secret = encryption.encrypt_token_and_secret(
                packet.public_key, packet.verify_token, secret)

            # A server id of '-' means the server is in offline mode
            if packet.server_id != '-':
                server_id = encryption.generate_verification_hash(
                    packet.server_id, secret, packet.public_key)
                if self.connection.auth_token is not None:
                    self.connection.auth_token.join(server_id)

            encryption_response = serverbound.login.EncryptionResponsePacket()
            encryption_response.shared_secret = encrypted_secret
            encryption_response.verify_token = token

            # Forced because we'll have encrypted the connection by the time
            # it reaches the outgoing queue
            self.connection.write_packet(encryption_response, force=True)

            # Enable the encryption
            cipher = encryption.create_aes_cipher(secret)
            encryptor = cipher.encryptor()
            decryptor = cipher.decryptor()
            self.connection.socket = encryption.EncryptedSocketWrapper(
                self.connection.socket, encryptor, decryptor)
            self.connection.file_object = \
                encryption.EncryptedFileObjectWrapper(
                    self.connection.file_object, decryptor)

        elif packet.packet_name == "disconnect":
            # Receiving a disconnect packet in the login state indicates an
            # abnormal condition. Raise an exception explaining the situation.
            try:
                msg = json.loads(packet.json_data)
                msg = _collect_message(msg)
            except (ValueError, TypeError, KeyError):
                msg = packet.json_data
            match = re.match(r"Outdated (client! Please use|server! I'm still on) (?P<ver>\S+)$", msg)
            if match:
                ver = match.group('ver')
                self.connection._version_mismatch(server_version=ver)
            raise LoginDisconnect('The server rejected our login attempt with: "%s".' % msg)

        elif packet.packet_name == "login success":
            self.connection.reactor = PlayingReactor(self.connection)

        elif packet.packet_name == "set compression":
            self.connection.options.compression_threshold = packet.threshold
            self.connection.options.compression_enabled = True

        elif packet.packet_name == "login plugin request":
            self.connection.write_packet(
                serverbound.login.PluginResponsePacket(
                    message_id=packet.message_id, successful=False))


def _collect_message(data):
    res = []
    if 'text' in data:
        res.append(data['text'])

    return ''.join(res)
