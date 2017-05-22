import logging
import threading
import time
from ballast.discovery import ServerList
from ballast.rule import Rule, RoundRobinRule
from ballast.ping import (
    Ping,
    SocketPing,
    PingStrategy,
    SerialPingStrategy
)


class LoadBalancer(object):

    DEFAULT_PING_INTERVAL = 30
    MAX_PING_TIME = 3

    def __init__(self, server_list, rule=None, ping_strategy=None, ping=None, ping_on_start=True):

        assert isinstance(server_list, ServerList)
        assert rule is None or isinstance(rule, Rule)
        assert ping_strategy is None or isinstance(ping_strategy, PingStrategy)
        assert ping is None or isinstance(ping, Ping)

        # some locks for thread-safety
        self._lock = threading.Lock()
        self._server_lock = threading.Lock()

        self._rule = rule \
            if rule is not None \
            else RoundRobinRule()

        self._ping_strategy = ping_strategy \
            if ping_strategy is not None \
            else SerialPingStrategy()

        self._ping = ping \
            if ping is not None \
            else SocketPing()

        self.max_ping_time = self.MAX_PING_TIME
        self._ping_interval = self.DEFAULT_PING_INTERVAL
        self._server_list = server_list
        self._servers = set()
        self._stats = LoadBalancerStats()
        self._rule.load_balancer = self
        self._logger = logging.getLogger(self.__module__)

        # start our background worker
        # to periodically ping our servers
        self._ping_timer_running = False
        self._ping_timer = None
        if ping_on_start:
            self._start_ping_timer()

    @property
    def ping_interval(self):
        return self._ping_interval

    @ping_interval.setter
    def ping_interval(self, value):
        self._ping_interval = value

        if self._ping_timer_running:
            self._stop_ping_timer()
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
        with self._server_lock:
            return set(self._servers)

    @property
    def reachable_servers(self):
        with self._server_lock:
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

    def ping_async(self, server=None):
        if server is None:
            # self._ping_all_servers()
            t = threading.Thread(name='ballast-worker', target=self._ping_all_servers)
            t.daemon = True
            t.start()
        else:
            is_alive = self._ping.is_alive(server)
            server._is_alive = is_alive

    def _ping_all_servers(self):
        with self._server_lock:
            results = self._ping_strategy.ping(
                self._ping,
                self._server_list
            )
            self._servers = set(results)

    def _start_ping_timer(self):

        with self._lock:
            if self._ping_timer_running:
                self._logger.debug("Background pinger already running")
                return

            self._ping_timer_running = True
            self._ping_timer = threading.Thread(name='ballast-worker', target=self._ping_loop)
            self._ping_timer.daemon = True
            self._ping_timer.start()

    def _stop_ping_timer(self):
        with self._lock:
            self._ping_timer_running = False
            self._ping_timer = None

    def _ping_loop(self):
        while self._ping_timer_running:
            try:
                self._ping_all_servers()
            except BaseException as e:
                self._logger.error("There was an error pinging servers: %s", e)

            time.sleep(self._ping_interval)


class LoadBalancerStats(object):

    def get_server_stats(self, server):
        pass
