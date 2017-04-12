import logging
import gevent
from discovery import ServerList
from rule import Rule, RoundRobinRule
from ping import (
    Ping,
    SocketPing,
    PingStrategy,
    SerialPingStrategy
)


class LoadBalancer(object):

    def __init__(self, server_list, rule=None, ping_strategy=None, ping=None):

        assert isinstance(server_list, ServerList)
        assert rule is None or isinstance(rule, Rule)
        assert ping_strategy is None or isinstance(ping_strategy, PingStrategy)
        assert ping is None or isinstance(ping, Ping)

        self._rule = rule \
            if rule is not None \
            else RoundRobinRule()

        self._ping_strategy = ping_strategy \
            if ping_strategy is not None \
            else SerialPingStrategy()

        self._ping = ping \
            if ping is not None \
            else SocketPing()

        self.max_ping_time = 3
        self._ping_interval = 30
        self._server_list = server_list
        self._stats = LoadBalancerStats()
        self._rule.load_balancer = self
        self._servers = set()
        self._logger = logging.getLogger(self.__module__)

        # start pinging our servers
        self._start_ping_timer()

    @property
    def ping_interval(self):
        return self._ping_interval

    @ping_interval.setter
    def ping_interval(self, value):
        self._ping_interval = value

        if self._ping_timer is not None:
            self._ping_timer.kill()

        self._start_ping_timer()

    @property
    def max_ping_time(self):
        if self._ping is None:
            return 0
        return self._ping.max_ping_time

    @max_ping_time.setter
    def max_ping_time(self, value):
        if self._ping is not None:
            self._ping.max_ping_time = value

    @property
    def stats(self):
        return self._stats

    @property
    def servers(self):
        return set(self._servers)

    @property
    def reachable_servers(self):
        servers = set()
        for s in self._servers:
            if s.is_alive:
                servers.add(s)

        return servers

    def choose_server(self):

        # choose a server, will
        # throw if there are none
        server = self._rule.choose()

        return server

    def mark_server_down(self, server):
        self._logger.debug("Marking server down: %s", server)
        server._is_alive = False

    def ping(self, server=None):
        if server is None:
            self._ping_all_servers()
        else:
            is_alive = self._ping.is_alive(server)
            server._is_alive = is_alive

    def _ping_all_servers(self):

        # get our servers
        results = self._ping_strategy.ping(
            self._ping,
            self._server_list
        )
        self._servers = set(results)

    def _start_ping_timer(self):
        self._ping_timer = gevent.spawn(self._ping_loop)

    def _ping_loop(self):
        while True:
            try:
                self._ping_all_servers()
            except BaseException as e:
                self._logger.error("There was an error pinging servers: %s", e)

            gevent.sleep(self._ping_interval)


class LoadBalancerStats(object):

    def get_server_stats(self, server):
        pass
