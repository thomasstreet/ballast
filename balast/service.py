import abc
import logging
import socket
import requests
from dns import resolver, rdatatype
from core import LoadBalancer
from ping import SocketPing, SerialPingStrategy
from rule import PriorityWeightedRule
from server import ServerList, Server
from exception import BalastException


class ConsulException(BalastException):

    DEFAULT_MSG = "There was a problem querying Consul: %s"

    def __init__(self, msg=DEFAULT_MSG, cause=None):

        assert isinstance(msg, basestring)
        assert cause is None or isinstance(cause, BaseException)

        self.cause = cause

        message = msg % cause if cause is not None else msg

        super(ConsulException, self).__init__(message)


class ConsulServiceNotFoundException(ConsulException):

    _MESSAGE = "Consul agent returned no results for service: '{}'"

    def __init__(self, consul_service_id):

        assert isinstance(consul_service_id, basestring)

        message = self._MESSAGE.format(consul_service_id)

        super(ConsulServiceNotFoundException, self).__init__(message)


class ConsulQueryFailedException(ConsulException):

    _MESSAGE = "Consul agent: '{}' returned status code: {}"

    def __init__(self, consule_endpoint, status_code):

        # assert isinstance(consul_service_id, basestring)

        message = self._MESSAGE.format(consule_endpoint, status_code)

        super(ConsulQueryFailedException, self).__init__(message)


class DnsRecordList(ServerList):

    __metaclass__ = abc.ABCMeta

    _RESOLVER_CACHE = resolver.LRUCache()

    def __init__(self, dns_qname, dns_host=None, dns_port=None):

        self._dns_qname = dns_qname

        # create a DNS resolver that caches results
        self._dns_resolver = resolver.Resolver()
        self._dns_resolver.cache = DnsRecordList._RESOLVER_CACHE

        if dns_port is not None:
            self._dns_resolver.port = dns_port

        if dns_host is not None:
            self._dns_resolver.nameservers = [
                socket.gethostbyname(dns_host)
            ]

    @abc.abstractmethod
    def get_servers(self):
        pass


class DnsARecordList(DnsRecordList):

    def __init__(self, dns_qname, dns_host=None, dns_port=None, server_port=80):
        super(DnsARecordList, self).__init__(
            dns_qname,
            dns_host,
            dns_port
        )
        self.server_port = server_port

    def get_servers(self):

        try:
            # query SRV records for our service name
            answer = self._dns_resolver.query(self._dns_qname, rdatatype.A)

            # iterate the results, generate server objects
            for i, srv in enumerate(answer):
                ttl = answer.response.answer[0].ttl
                yield Server(
                    srv.address,
                    self.server_port,
                    ttl=ttl
                )

        except resolver.NXDOMAIN, resolver.NoNameservers:
            yield None


class DnsServiceRecordList(DnsRecordList):

    def __init__(self, dns_qname, dns_host=None, dns_port=None):
        super(DnsServiceRecordList, self).__init__(
            dns_qname,
            dns_host,
            dns_port
        )

    def get_servers(self):

        try:
            # query SRV records for our service name
            answer = self._dns_resolver.query(self._dns_qname, rdatatype.SRV)

            # iterate the results, generate server objects
            for i, srv in enumerate(answer):
                address = answer.response.additional[0].items[i].address
                ttl = answer.response.additional[0].ttl
                yield Server(
                    address,
                    srv.port,
                    srv.weight,
                    srv.priority,
                    ttl
                )

        except resolver.NXDOMAIN, resolver.NoNameservers:
            yield None


class Service(object):

    _SERVICE_ADDRESS = '{}:{}'
    _BASE_URL_FORMAT = 'http://{}'

    def __init__(self, load_balancer):
        self._load_balancer = load_balancer
        self._logger = logging.getLogger(self.__class__.__name__)

    def options(self, url, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.options(absolute_url, **kwargs)

    def head(self, url, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.head(absolute_url, **kwargs)

    def get(self, url, params=None, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.get(absolute_url, params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        absolute_url, server = self._get_absolute_url(url)
        try:
            return requests.post(absolute_url, data, json, timeout=10, **kwargs)
        except BaseException:
            self._load_balancer.mark_server_down(server)
            return self.post(url, data, json, **kwargs)

    def put(self, url, data=None, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.put(absolute_url, data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.patch(absolute_url, data, **kwargs)

    def delete(self, url, **kwargs):
        # TODO: if fails to connect, mark server down, choose again
        absolute_url, server = self._get_absolute_url(url)
        return requests.delete(absolute_url, **kwargs)

    def _get_service_address(self):

        try:
            server = self._load_balancer.choose_server()
            return self._SERVICE_ADDRESS.format(
                server.address,
                server.port
            ), server
        except BaseException as e:
            if isinstance(e, ConsulException):
                raise e
            else:
                raise ConsulException(cause=e)

    def _get_absolute_url(self, url):
        service_address, server = self._get_service_address()
        base_url = self._BASE_URL_FORMAT.format(service_address)

        return base_url + url, server


class DnsSrvService(Service):
    """
    Load-balancing base class implementation for services
    using DNS SRV records for service-discovery.

    """

    def __init__(self, dns_qname, dns_host, dns_port):

        servers = DnsServiceRecordList(dns_qname, dns_host, dns_port)
        rule = PriorityWeightedRule()
        ping = SocketPing()
        strategy = SerialPingStrategy()
        load_balancer = LoadBalancer(
            servers,
            rule,
            strategy,
            ping
        )
        super(DnsSrvService, self).__init__(load_balancer)

        self._logger = logging.getLogger(self.__class__.__name__)
