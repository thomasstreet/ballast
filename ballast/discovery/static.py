import logging
from past.builtins import basestring
from ballast.discovery import Server, ServerList
from ballast.exception import BallastException


class StaticServerList(ServerList):

    def __init__(self, servers):
        self._servers = set()
        self._logger = logging.getLogger(self.__module__)

        for server in servers:

            if isinstance(server, Server):
                self._servers.add(server)
            elif isinstance(server, basestring):
                parts = server.split(":")

                if len(parts) > 1:
                    self.add_server(parts[0], int(parts[1]))
                else:
                    self.add_server(parts[0])
            else:
                raise BallastException('Server was in unexpected format: "%s"' % server)

    def add_server(self, address, port=80, weight=1, priority=1):
        s = Server(address, port, weight, priority)
        self._servers.add(s)

    def get_servers(self):
        self._logger.debug("Resolved %s servers", len(self._servers))
        return set(self._servers)
