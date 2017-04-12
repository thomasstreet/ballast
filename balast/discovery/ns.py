import abc
import logging
import socket
from dns import resolver, rdatatype, exception
from dns.rdtypes.IN.A import A
from dns.rdtypes.ANY.CNAME import CNAME
from balast.exception import BalastException
from balast.discovery import ServerList, Server


class DnsRecordList(ServerList):

    __metaclass__ = abc.ABCMeta

    _RESOLVER_CACHE = resolver.LRUCache()

    def __init__(self, dns_qname, dns_host=None, dns_port=None):

        self._dns_qname = dns_qname
        self._logger = logging.getLogger(self.__module__)

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
                s = Server(
                    srv.address,
                    self.server_port,
                    ttl=ttl
                )

                self._logger.debug("Created server from DNS A record: %s", s)

                yield s

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
                rdata = answer.response.additional[0].items[i]
                if isinstance(rdata, A):
                    address = rdata.address
                elif isinstance(rdata, CNAME):
                    address = unicode(rdata.target)
                else:
                    raise BalastException('Unexpected DNS record: %s' % rdata)

                ttl = answer.response.additional[0].ttl
                s = Server(
                    address,
                    srv.port,
                    srv.weight,
                    srv.priority,
                    ttl
                )

                self._logger.debug("Created server from DNS SRV record: %s", s)

                yield s

        except (exception.DNSException, BalastException):
            return
