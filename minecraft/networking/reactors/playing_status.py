from minecraft.networking.reactors import StatusReactor


class PlayingStatusReactor(StatusReactor):
    def __init__(self, connection):
        super(PlayingStatusReactor, self).__init__(connection, do_ping=False)

    def handle_status(self, status):
        if status == {}:
            # This can occur when we connect to a Mojang server while it is
            # still initialising, so it must not cause the client to connect
            # with the default version.
            raise IOError('Invalid server status.')
        elif 'version' not in status or 'protocol' not in status['version']:
            return self.handle_failure()

        proto = status['version']['protocol']
        if proto not in self.connection.allowed_proto_versions:
            self.connection._version_mismatch(
                server_protocol=proto,
                server_version=status['version'].get('name'))

        self.handle_proto_version(proto)

        if self.connection.context.enable_fml and not self.connection.context.fml_mods:
            self.connection.context.fml_mods = [(i['modid'], i['version'])
                                                for i in status['modinfo']['modList']]

    def handle_proto_version(self, proto_version):
        self.connection.allowed_proto_versions = {proto_version}
        self.connection.connect()

    def handle_failure(self):
        self.handle_proto_version(self.connection.default_proto_version)

    def handle_exception(self, exc, exc_info):
        if isinstance(exc, EOFError):
            # An exception of this type may indicate that the server does not
            # properly support status queries, so we treat it as non-fatal.
            self.connection.disconnect(immediate=True)
            self.handle_failure()
            return True
