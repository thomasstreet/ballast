import unittest
import mock
from dns import rdatatype, resolver, message, name, rrset
from ballast.discovery.ns import DnsServiceRecordList, DnsARecordList


class _MockSrvResolver(object):

    def __init__(self):
        self.cache = None
        self.port = 53
        self.nameservers = ['127.0.0.1']
        self.executed_query = None

    def query(self, qname, rdtype):

        # expose our query params
        self.executed_query = (qname, rdtype)

        # hack up a response that our class is expecting
        q = message.make_query(qname, rdtype)
        r = message.make_response(q)
        a = resolver.Answer(name.from_text(qname), rdtype, 1, r, raise_on_no_answer=False)
        a.rrset = rrset.from_text(qname, 300, 1, rdtype, '1 1 3000 %s' % qname)
        additional = rrset.from_text(qname, 333, 1, rdatatype.A, '127.1.1.1')
        a.response.additional.append(additional)

        return a


class _MockAResolver(object):

    def __init__(self):
        self.cache = None
        self.port = 53
        self.nameservers = ['127.0.0.1']
        self.executed_query = None

    def query(self, qname, rdtype):

        # expose our query params
        self.executed_query = (qname, rdtype)

        # hack up a response that our class is expecting
        q = message.make_query(qname, rdtype)
        r = message.make_response(q)
        a = resolver.Answer(name.from_text(qname), rdtype, 1, r, raise_on_no_answer=False)
        a.rrset = rrset.from_text(qname, 333, 1, rdatatype.A, '127.1.1.1')
        a.response.answer.append(a.rrset)

        return a


class DnsServiceRecordListTest(unittest.TestCase):

    @mock.patch('ballast.discovery.ns.resolver.Resolver', return_value=_MockSrvResolver())
    @mock.patch('ballast.discovery.ns.socket.gethostbyname', return_value='10.1.2.3')
    def test_resolve(self, mock_gethostbyname, mock_resolver):

        qname = 'my.local-service.'
        dns_host = 'my.dns.host'
        dns_port = 1234
        servers = DnsServiceRecordList(qname, dns_host, dns_port)

        # verify our resolver configuration
        resolver = servers._dns_resolver
        self.assertIsNotNone(resolver.cache)
        self.assertEqual(resolver.port, 1234)
        self.assertIn('10.1.2.3', resolver.nameservers)

        self.assertTrue(mock_gethostbyname.called)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(3000, server_list[0].port)
        self.assertEqual(333, server_list[0].ttl)

        # ensure the query was as expected
        actual_qname, rdtype = mock_resolver.return_value.executed_query
        self.assertEqual(actual_qname, qname)
        self.assertEqual(rdtype, rdatatype.SRV)

    @mock.patch('ballast.discovery.ns.resolver.Resolver', return_value=_MockSrvResolver())
    def test_resolve_with_defaults(self, mock_resolver):

        qname = 'my.server.local.'
        servers = DnsServiceRecordList(qname)

        resolver = servers._dns_resolver

        # should be the defaults
        self.assertEqual(resolver.port, 53)
        self.assertIn('127.0.0.1', resolver.nameservers)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(3000, server_list[0].port)
        self.assertEqual(333, server_list[0].ttl)

        # ensure the query was as expected
        actual_qname, rdtype = mock_resolver.return_value.executed_query
        self.assertEqual(actual_qname, qname)
        self.assertEqual(rdtype, rdatatype.SRV)


class DnsARecordListTest(unittest.TestCase):

    @mock.patch('ballast.discovery.ns.resolver.Resolver', return_value=_MockAResolver())
    @mock.patch('ballast.discovery.ns.socket.gethostbyname', return_value='10.1.2.3')
    def test_resolve(self, mock_gethostbyname, mock_resolver):

        qname = 'cns.service.aws-uw2-staging.consul.'
        dns_host = 'my.dns.host'
        dns_port = 1234
        servers = DnsARecordList(qname, dns_host, dns_port, 3000)

        # verify our resolver configuration
        resolver = servers._dns_resolver
        self.assertIsNotNone(resolver.cache)
        self.assertEqual(resolver.port, 1234)
        self.assertIn('10.1.2.3', resolver.nameservers)

        self.assertTrue(mock_gethostbyname.called)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(3000, server_list[0].port)
        self.assertEqual(333, server_list[0].ttl)

        # ensure the query was as expected
        actual_qname, rdtype = mock_resolver.return_value.executed_query
        self.assertEqual(actual_qname, qname)
        self.assertEqual(rdtype, rdatatype.A)

    @mock.patch('ballast.discovery.ns.resolver.Resolver', return_value=_MockAResolver())
    def test_resolve_with_defaults(self, mock_resolver):

        qname = 'my.server.local.'
        servers = DnsARecordList(qname)

        resolver = servers._dns_resolver

        # should be the defaults
        self.assertEqual(resolver.port, 53)
        self.assertIn('127.0.0.1', resolver.nameservers)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(80, server_list[0].port)
        self.assertEqual(333, server_list[0].ttl)

        # ensure the query was as expected
        actual_qname, rdtype = mock_resolver.return_value.executed_query
        self.assertEqual(actual_qname, qname)
        self.assertEqual(rdtype, rdatatype.A)
