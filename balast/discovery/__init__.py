import abc
from past.builtins import cmp


class Server(object):

    def __init__(self, address, port, weight=1, priority=1, ttl=300):
        self.address = address
        self.port = port
        self.weight = weight
        self.priority = priority
        self.ttl = ttl
        self._is_alive = False

    def __str__(self):
        return "%s(%s:%s, ttl:%s, weight:%s, priority:%s, alive:%s)" % (
            self.__class__.__name__,
            self.address,
            self.port,
            self.ttl,
            self.weight,
            self.priority,
            self.is_alive
        )

    def __hash__(self):
        return hash((self.address, self.port))

    def __eq__(self, other):
        return (
            self.address == other.address and
            self.port == other.port
        )

    def __lt__(self, other):
        return self.priority < other.priority

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    @property
    def is_alive(self):
        return self._is_alive


class ServerList(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_servers(self):
        return []


class ServerStats(object):

    @property
    def active_requests(self):
        """
        The current number of active requests
        """
        return 0

    @property
    def utilization(self):
        """
        The current utilization as a percentage between 0 and 100.
        """
        return 0

    @property
    def failure_count(self):
        return 0

    @property
    def average_response_time(self):
        return 0

    def add_response_time(self, time):
        pass

    def increment_failures(self):
        pass

    def increment_active_requests(self):
        pass

    def decrement_active_requests(self):
        pass

    def is_tripped(self, current_time):
        """
        Whether or not the circuit breaker tripped due to too many failures.
        """
        return False
