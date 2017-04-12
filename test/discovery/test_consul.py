import unittest
import mock
import urlparse
from requests import models
from balast.discovery.consul import ConsulRestRecordList


_MOCK_RESPONSE = """
[
  {
    "Node":"ins-alb",
    "Address":"127.1.1.1",
    "ServiceID":"ins",
    "ServiceName":"ins",
    "ServiceTags":["staging"],
    "ServiceAddress":"",
    "ServicePort":3000,
    "ServiceEnableTagOverride":false,
    "CreateIndex":138159,
    "ModifyIndex":776311
  }
]
"""


class _MockResponse(models.Response):

    def __init__(self, content):
        super(_MockResponse, self).__init__()
        self._content = content
        self.status_code = 200


class ConsulRestRecordListTest(unittest.TestCase):

    @mock.patch('balast.discovery.consul.requests.get', return_value=_MockResponse(_MOCK_RESPONSE))
    def test_resolve(self, mock_get_request):

        consul_base_url = 'http://my.consul.url'
        service = 'my-service'
        dc = 'my-dc'
        near = 'me'
        tag = 'testing'

        servers = ConsulRestRecordList(consul_base_url, service, dc, near, tag)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(3000, server_list[0].port)
        self.assertEqual(10, server_list[0].ttl)

        # verify request url was properly formatted
        args = mock_get_request.call_args[0]
        actual_url = urlparse.urlparse(args[0])
        actual_query = urlparse.parse_qs(actual_url.query)

        self.assertEqual(actual_url.scheme, 'http')
        self.assertEqual(actual_url.hostname, 'my.consul.url')
        self.assertEqual(actual_url.path, '/v1/catalog/service/my-service')
        self.assertIn(dc, actual_query['dc'])
        self.assertIn(near, actual_query['near'])
        self.assertIn(tag, actual_query['tag'])

    @mock.patch('balast.discovery.consul.requests.get', return_value=_MockResponse(_MOCK_RESPONSE))
    def test_resolve_with_defaults(self, mock_get_request):

        consul_base_url = 'http://my.consul.url'
        service = 'my-service'

        servers = ConsulRestRecordList(consul_base_url, service)

        # resolve some servers
        server_list = list(servers.get_servers())
        self.assertEqual(1, len(server_list))
        self.assertEqual('127.1.1.1', server_list[0].address)
        self.assertEqual(3000, server_list[0].port)
        self.assertEqual(10, server_list[0].ttl)

        # verify request url was properly formatted
        args = mock_get_request.call_args[0]
        actual_url = urlparse.urlparse(args[0])

        self.assertEqual(actual_url.scheme, 'http')
        self.assertEqual(actual_url.hostname, 'my.consul.url')
        self.assertEqual(actual_url.path, '/v1/catalog/service/my-service')
        self.assertEqual(actual_url.query, '')
