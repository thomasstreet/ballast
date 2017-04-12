import logging
import requests
from requests.exceptions import RequestException
from util import UrlBuilder


class Service(object):

    DEFAULT_REQUEST_TIMEOUT = 10

    def __init__(self, load_balancer, use_https=False, request_timeout=DEFAULT_REQUEST_TIMEOUT):
        self._load_balancer = load_balancer
        self._use_https = use_https
        self._request_timeout = request_timeout
        self._logger = logging.getLogger(self.__module__)

    def request(self, method, url, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: %s %s", method.upper(), absolute_url)

        try:
            response = requests.request(method, absolute_url, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.request(method, url, **kwargs)

    def options(self, url, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: OPTIONS %s", absolute_url)

        try:
            response = requests.options(absolute_url, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.options(url, **kwargs)

    def head(self, url, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: HEAD %s", absolute_url)

        try:
            response = requests.head(absolute_url, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.head(url, **kwargs)

    def get(self, url, params=None, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: GET %s", absolute_url)

        try:
            response = requests.get(absolute_url, params, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.get(url, params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: POST %s", absolute_url)

        try:
            response = requests.post(absolute_url, data, json, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.post(url, data, json, **kwargs)

    def put(self, url, data=None, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: PUT %s", absolute_url)

        try:
            response = requests.put(absolute_url, data, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.put(url, data, **kwargs)

    def patch(self, url, data=None, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: PATCH %s", absolute_url)

        try:
            response = requests.patch(absolute_url, data, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.patch(url, data, **kwargs)

    def delete(self, url, **kwargs):

        # choose a server from the pool
        server = self._load_balancer.choose_server()
        absolute_url = self._get_absolute_url(server, url, self._use_https)

        self._logger.debug("Request: DELETE %s", absolute_url)

        try:
            response = requests.delete(absolute_url, timeout=self._request_timeout, **kwargs)

            # 5xx errors should mark the server down
            # everything else is good to go
            if response.status_code < 500:
                return response

        except RequestException as e:
            self._logger.error("Request to server failed for url: '%s': %s", absolute_url, e)

        # mark this server down and try the
        # request again with a new server
        self._load_balancer.mark_server_down(server)

        return self.delete(url, **kwargs)

    @staticmethod
    def _get_absolute_url(server, relative_url, use_https):

        url = UrlBuilder.from_parts(
            hostname=server.address,
            port=server.port
        )
        url.append_path(relative_url)

        if use_https:
            url.https()

        return unicode(url)
