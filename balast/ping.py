import abc
import logging
import threading
import socket
import requests
from timeit import default_timer as timer
from multiprocessing.pool import ThreadPool, Pool
from balast.discovery import Server, ServerList
from balast.exception import BalastException


# current thread name (so we know who 'main' is)
_MAIN_THREAD_NAME = threading.currentThread().name

# the thread name format for our ping threads
_THREAD_NAME_FORMAT = 'balast-ping-'


def _ping_in_background(ping, server):

    # rename the thread according to our convention
    t = threading.currentThread()
    if not t.name == _MAIN_THREAD_NAME and not t.name.startswith('balast'):
        t.setName(_THREAD_NAME_FORMAT + t.name)

    # ping the server
    server._is_alive = ping.is_alive(server)

    return server


class Ping(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.max_ping_time = None
        self._logger = logging.getLogger(self.__module__)

    def __getstate__(self):

        # logger can't be pickeled
        d = self.__dict__.copy()
        del d['_logger']

        return d

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._logger = logging.getLogger(self.__module__)

    @abc.abstractmethod
    def is_alive(self, server):
        return False


class DummyPing(Ping):

    def is_alive(self, server):

        assert isinstance(server, Server)

        self._logger.debug("Ping succeeded for server: %s", server)

        return True


class SocketPing(Ping):

    def is_alive(self, server):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.max_ping_time)
            s.connect((server.address, server.port))
            s.close()

            self._logger.debug("Ping succeeded for server: %s", server)

            return True
        except:
            self._logger.warn("Ping failed for server: %s", server)
            return False


class UrlPing(Ping):

    _HTTP = 'http'
    _HTTPS = 'https'
    _URL_FORMAT = '{}://{}:{}'

    def __init__(self, is_secure=False):
        super(UrlPing, self).__init__()
        self.is_secure = is_secure

    def is_alive(self, server):
        try:
            scheme = self._HTTPS \
                if self.is_secure \
                else self._HTTP

            url = self._URL_FORMAT.format(
                scheme,
                server.address,
                server.port
            )

            result = requests.get(url)

            self._logger.debug("Ping succeeded for server: %s", server)

            return result.ok
        except:
            self._logger.warn("Ping failed for server: %s", server)
            return False


class PingStrategy(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._logger = logging.getLogger(self.__module__)

    def __getstate__(self):

        # logger can't be pickeled
        d = self.__dict__.copy()
        del d['_logger']

        return d

    def __setstate__(self, state):
        self.__dict__.update(state)

    @abc.abstractmethod
    def ping(self, ping, servers):
        return []


class SerialPingStrategy(PingStrategy):

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        start_time = timer()

        # returns a list of booleans
        results = []
        for s in servers.get_servers():
            is_alive = ping.is_alive(s)
            s._is_alive = is_alive
            results.append(s)

        end_time = timer() - start_time

        self._logger.debug("Pinged %s servers in %s seconds", len(results), end_time)

        return results


class AsyncPoolPingStrategy(PingStrategy):

    def __init__(self, pool_type):
        super(AsyncPoolPingStrategy, self).__init__()
        self._pool_type = pool_type

    def __getstate__(self):
        s = super(AsyncPoolPingStrategy, self).__getstate__()
        return s

    def __setstate__(self, state):
        pass

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        start_time = timer()

        futures = []
        results = []
        server_list = list(servers.get_servers())
        if not any(server_list):
            self._logger.debug("Ping failed - no servers to ping!")
            return results

        pool = self._pool_type(processes=len(server_list))

        # create our threads in the thread pool
        for s in server_list:
            future = pool.apply_async(_ping_in_background, (ping, s))
            futures.append(future)

        # now, join the threads and grab the results
        for f in futures:
            server = f.get()
            results.append(server)

        pool.close()

        end_time = timer() - start_time

        self._logger.debug("Pinged %s servers in %s seconds", len(results), end_time)

        return results


class ThreadPoolPingStrategy(AsyncPoolPingStrategy):

    def __init__(self):
        super(ThreadPoolPingStrategy, self).__init__(ThreadPool)


class MultiprocessingPoolPingStrategy(AsyncPoolPingStrategy):

    def __init__(self):
        super(MultiprocessingPoolPingStrategy, self).__init__(Pool)


class GeventPingStrategy(PingStrategy):

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        start_time = timer()

        try:
            import gevent
        except ImportError:
            raise BalastException(
                "Please install optional gevent dependencies "
                "in order to use this feature: \n\n"
                "$ pip install balast[gevent] or \n"
                "$ pip install balast[all]"
            )

        results = []
        greenlets = []

        # create our greenlets
        for s in servers.get_servers():
            g = gevent.spawn(_ping_in_background, ping, s)
            greenlets.append(g)

        # wait for all greenlets to finish
        gevent.joinall(greenlets)

        # now, grab the results
        for g in greenlets:
            server = g.get()
            results.append(server)

        end_time = timer() - start_time

        self._logger.debug("Pinged %s servers in %s seconds", len(results), end_time)

        return results
