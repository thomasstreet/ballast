import unittest
import mock
from requests import models, exceptions
from balast import ping, Service, LoadBalancer
from balast.util import UrlBuilder
from balast.discovery import Server
from balast.discovery.static import StaticServerList
from balast.exception import (
    BalastException,
    NoReachableServers,
    BalastConfigurationException
)


_EXPECTED_SERVERS = ['127.0.0.1', '127.0.0.2']


class _MockResponse(models.Response):

    def __init__(self, status_code):
        super(_MockResponse, self).__init__()
        self.status_code = status_code


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self._service = self._create_service()
        self._load_balancer = self._service._load_balancer
        self._servers = self._load_balancer.servers

    def test_init_with_server_collection(self):

        servers = [
            Server('127.0.0.1', 80),
            Server('127.0.0.2', 81)
        ]
        # create a service with a collection
        # of server addresses
        service = Service(servers)

        # should have auto-created a load balancer
        load_balancer = service._load_balancer
        self.assertIsNotNone(load_balancer)

        # should have auto-created a static server list
        server_list = load_balancer._server_list
        self.assertIsInstance(server_list, StaticServerList)

        for server in server_list.get_servers():
            self.assertIn(server.address, _EXPECTED_SERVERS)

    def test_init_with_server_string_collection(self):

        # create a service with a collection
        # of server addresses
        service = Service(_EXPECTED_SERVERS)

        # should have auto-created a load balancer
        load_balancer = service._load_balancer
        self.assertIsNotNone(load_balancer)

        # should have auto-created a static server list
        server_list = load_balancer._server_list
        self.assertIsInstance(server_list, StaticServerList)

        for server in server_list.get_servers():
            self.assertIn(server.address, _EXPECTED_SERVERS)

    def test_init_with_bad_args(self):

        # no args
        self.assertRaises(BalastConfigurationException, lambda: Service())

        # positional arg not LoadBalancer or collection
        self.assertRaises(BalastConfigurationException, lambda: Service('bad-arg!'))

        # collection items not in proper format (either Server or strings)
        self.assertRaises(BalastException, lambda: Service([1, 2, 3]))

        # positional arg AND LoadBalancer
        def init_service():
            Service('bad-arg!', load_balancer=self._load_balancer)
        self.assertRaises(BalastConfigurationException, init_service)

    @mock.patch('balast.service.requests.request', return_value=_MockResponse(200))
    def test_request_ok(self, mock_request):

        # make our request
        result = self._service.request('GET', '/relative/path')

        # should have tried twice - once for each server
        self.assertEqual(1, mock_request.call_count)
        self.assertEqual(result, mock_request.return_value)

        # verify the url we create
        call_arg = mock_request.call_args_list[0]
        url = UrlBuilder.from_url(call_arg[0][1])
        self.assertIn(url._hostname, _EXPECTED_SERVERS)
        self.assertEqual(url._scheme, 'https')
        self.assertIsNone(url._port)
        self.assertEqual(url._path, '/relative/path')

    @mock.patch('balast.service.requests.head', return_value=_MockResponse(200))
    def test_head_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.head)

    @mock.patch('balast.service.requests.options', return_value=_MockResponse(200))
    def test_options_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.options)

    @mock.patch('balast.service.requests.get', return_value=_MockResponse(200))
    def test_get_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.get)

    @mock.patch('balast.service.requests.post', return_value=_MockResponse(200))
    def test_post_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.post)

    @mock.patch('balast.service.requests.put', return_value=_MockResponse(200))
    def test_put_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.put)

    @mock.patch('balast.service.requests.patch', return_value=_MockResponse(200))
    def test_patch_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.patch)

    @mock.patch('balast.service.requests.delete', return_value=_MockResponse(200))
    def test_delete_ok(self, mock_request):
        self.assert_request_ok(mock_request, self._service.delete)

    @mock.patch('balast.service.requests.request', return_value=_MockResponse(500))
    def test_all_request_servers_error(self, mock_request):

        mock_request.side_effect = exceptions.RequestException('mock exception')

        # will try each server, and mark each down on a 500 response
        # when no servers are left, a NoReachableServersException is thrown
        self.assertRaises(NoReachableServers, self._service.request, 'GET', '/relative/path')

        # should have tried twice - once for each server
        self.assertEqual(2, mock_request.call_count)

        # add our hostnames to a set (to ensure the
        # same server isn't being used repeatedly)
        # all other info should be the same for each server request
        hostnames = set()
        for i, call_arg in enumerate(mock_request.call_args_list):
            url = UrlBuilder.from_url(call_arg[0][1])
            hostnames.add(url._hostname)
            self.assertEqual(url._scheme, 'https')
            self.assertIsNone(url._port)
            self.assertEqual(url._path, '/relative/path')

        # less than 2 means a server has been reused
        self.assertEqual(2, len(hostnames))
        for hostname in hostnames:
            self.assertIn(hostname, _EXPECTED_SERVERS)

    @mock.patch('balast.service.requests.options', return_value=_MockResponse(500))
    def test_all_options_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.options)

    @mock.patch('balast.service.requests.head', return_value=_MockResponse(500))
    def test_all_head_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.head)

    @mock.patch('balast.service.requests.get', return_value=_MockResponse(500))
    def test_all_get_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.get)

    @mock.patch('balast.service.requests.post', return_value=_MockResponse(500))
    def test_all_post_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.post)

    @mock.patch('balast.service.requests.put', return_value=_MockResponse(500))
    def test_all_put_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.put)

    @mock.patch('balast.service.requests.patch', return_value=_MockResponse(500))
    def test_all_patch_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.patch)

    @mock.patch('balast.service.requests.delete', return_value=_MockResponse(500))
    def test_all_delete_servers_error(self, mock_request):
        mock_request.side_effect = exceptions.RequestException('mock exception')
        self.assert_all_servers_fail(mock_request, self._service.delete)

    @mock.patch('balast.service.requests.request', return_value=_MockResponse(500))
    def test_all_request_servers_500(self, mock_request):

        # will try each server, and mark each down on a 500 response
        # when no servers are left, a NoReachableServersException is thrown
        self.assertRaises(NoReachableServers, self._service.request, 'GET', '/relative/path')

        # should have tried twice - once for each server
        self.assertEqual(2, mock_request.call_count)

        # add our hostnames to a set (to ensure the
        # same server isn't being used repeatedly)
        # all other info should be the same for each server request
        hostnames = set()
        for i, call_arg in enumerate(mock_request.call_args_list):
            url = UrlBuilder.from_url(call_arg[0][1])
            hostnames.add(url._hostname)
            self.assertEqual(url._scheme, 'https')
            self.assertIsNone(url._port)
            self.assertEqual(url._path, '/relative/path')

        # less than 2 means a server has been reused
        self.assertEqual(2, len(hostnames))
        for hostname in hostnames:
            self.assertIn(hostname, _EXPECTED_SERVERS)

    @mock.patch('balast.service.requests.options', return_value=_MockResponse(500))
    def test_all_options_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.options)

    @mock.patch('balast.service.requests.head', return_value=_MockResponse(500))
    def test_all_head_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.head)

    @mock.patch('balast.service.requests.get', return_value=_MockResponse(500))
    def test_all_get_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.get)

    @mock.patch('balast.service.requests.post', return_value=_MockResponse(500))
    def test_all_post_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.post)

    @mock.patch('balast.service.requests.put', return_value=_MockResponse(500))
    def test_all_put_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.put)

    @mock.patch('balast.service.requests.patch', return_value=_MockResponse(500))
    def test_all_patch_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.patch)

    @mock.patch('balast.service.requests.delete', return_value=_MockResponse(500))
    def test_all_delete_servers_500(self, mock_request):
        self.assert_all_servers_fail(mock_request, self._service.delete)

    def assert_request_ok(self, mock_request, request_call):

        # make our request
        result = request_call('/relative/path')

        # should have tried twice - once for each server
        self.assertEqual(1, mock_request.call_count)
        self.assertEqual(result, mock_request.return_value)

        # verify the url we create
        call_arg = mock_request.call_args_list[0]
        url = UrlBuilder.from_url(call_arg[0][0])
        self.assertIn(url._hostname, _EXPECTED_SERVERS)
        self.assertEqual(url._scheme, 'https')
        self.assertIsNone(url._port)
        self.assertEqual(url._path, '/relative/path')

    def assert_all_servers_fail(self, mock_request, request_call):

        # will try each server, and mark each down on a 500 response
        # when no servers are left, a NoReachableServersException is thrown
        self.assertRaises(NoReachableServers, request_call, '/relative/path')

        # should have tried twice - once for each server
        self.assertEqual(2, mock_request.call_count)

        # add our hostnames to a set (to ensure the
        # same server isn't being used repeatedly)
        # all other info should be the same for each server request
        hostnames = set()
        for i, call_arg in enumerate(mock_request.call_args_list):
            url = UrlBuilder.from_url(call_arg[0][0])
            hostnames.add(url._hostname)
            self.assertEqual(url._scheme, 'https')
            self.assertIsNone(url._port)
            self.assertEqual(url._path, '/relative/path')

        # less than 2 means a server has been reused
        self.assertEqual(2, len(hostnames))
        for hostname in hostnames:
            self.assertIn(hostname, _EXPECTED_SERVERS)

    @staticmethod
    def _create_service():

        servers = StaticServerList(_EXPECTED_SERVERS)
        load_balancer = LoadBalancer(servers, ping=ping.DummyPing())
        service = Service(load_balancer, use_https=True, request_timeout=0.1)

        import gevent
        gevent.sleep()

        return service
