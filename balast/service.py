import logging
import requests
from exception import BalastException


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
            if isinstance(e, BalastException):
                raise e
            else:
                raise BalastException(cause=e)

    def _get_absolute_url(self, url):
        service_address, server = self._get_service_address()
        base_url = self._BASE_URL_FORMAT.format(service_address)

        return base_url + url, server
