import abc
import threading
from Queue import Queue
from discovery import Server
from exception import BalastException, NoReachableServers


class Rule(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._load_balancer = None

    @abc.abstractproperty
    def load_balancer(self):
        return self._load_balancer

    @load_balancer.setter
    def load_balancer(self, value):
        self._load_balancer = value

    @abc.abstractmethod
    def choose(self):
        return Server(None, None)


class RoundRobinRule(Rule):

    def __init__(self):
        super(RoundRobinRule, self).__init__()
        self._lock = threading.Lock()
        self._queue = Queue()

    @property
    def load_balancer(self):
        return self._load_balancer

    @load_balancer.setter
    def load_balancer(self, value):
        self._load_balancer = value

    def choose(self):

        with self._lock:

            if self._load_balancer is None:
                raise BalastException("Load balancer not set!")

            # push all available servers back onto
            # the queue if the queue is empty
            if self._queue.empty():
                servers = self._load_balancer.reachable_servers
                if len(servers) == 0:
                    raise NoReachableServers()
                sorted_by_priority = sorted(servers)
                for server in sorted_by_priority:
                    self._queue.put(server)

            # now just pop one off until
            # the queue is empty
            return self._queue.get(block=False)


class PriorityWeightedRule(Rule):

    def __init__(self):
        super(PriorityWeightedRule, self).__init__()
        self._load_balancer_stats = None

    @property
    def load_balancer(self):
        return self._load_balancer

    @load_balancer.setter
    def load_balancer(self, value):
        self._load_balancer = value
        self._load_balancer_stats = value.stats

    def choose(self):

        servers = self._load_balancer.reachable_servers

        server_count = len(servers)

        if len(servers) == 0:
            raise Exception("No reachable servers could be found")

        if server_count == 1:
            return servers.pop()

        def s(o1, o2):
            return -1

        sorted_by_priority = sorted(servers, s)

        # for server in sorted_by_priority:
        # stats = self._load_balancer_stats.get_server_stats(server)
        # assert isinstance(stats, ServerStats)
        # TODO: check weight/priority

        # sort the servers by priority
        # from the top-priority servers, get the server with utilization lowest compared to weight
        # if all utilizations are lower than respective weights, just pick the first server

        return sorted_by_priority[0]
