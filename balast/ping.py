import abc
import socket
import requests
from multiprocessing.pool import ThreadPool, Pool
from server import Server, ServerList


class Ping(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.max_ping_time = None

    @abc.abstractmethod
    def is_alive(self, server):
        return False


class DummyPing(Ping):

    def is_alive(self, server):

        assert isinstance(server, Server)

        return True


class SocketPing(Ping):

    def is_alive(self, server):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.max_ping_time)
            s.connect((server.address, server.port))
            s.close()

            return True
        except:
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
            return result.ok
        except:
            return False


class PingStrategy(object):

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        # returns a list of booleans
        results = []
        for s in servers.get_servers():
            results.append(False)

        return results


class SerialPingStrategy(PingStrategy):

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        # returns a list of booleans
        results = []
        for s in servers.get_servers():
            is_alive = ping.is_alive(s)
            s._is_alive = is_alive
            results.append(s)

        return results


def _ping_in_background(ping, server):
    is_alive = ping.is_alive(server)
    server._is_alive = is_alive
    return server


class AsyncPoolPingStrategy(PingStrategy):

    def __init__(self, pool_type):
        self._pool_type = pool_type

    def ping(self, ping, servers):

        assert isinstance(ping, Ping)
        assert isinstance(servers, ServerList)

        futures = []
        results = []
        server_list = list(servers.get_servers())
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

        import gevent

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

        return results
