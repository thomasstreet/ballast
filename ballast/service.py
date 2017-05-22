import logging
import requests
from past.builtins import basestring, unicode
from requests.exceptions import RequestException
from ballast.util import UrlBuilder
from ballast.core import LoadBalancer
from ballast.exception import BallastConfigurationException
from ballast.discovery import ServerList
from ballast.discovery.static import StaticServerList


class Service(object):

    DEFAULT_REQUEST_TIMEOUT = 10

    def __init__(self, *args, **kwargs):
        self._load_balancer = kwargs.get('load_balancer')
        self._use_https = kwargs.get('use_https', False)
        self._request_timeout = kwargs.get('request_timeout', self.DEFAULT_REQUEST_TIMEOUT)
        self._logger = logging.getLogger(self.__module__)

        # if our load balancer wasn't configured via kwargs
        # and there are no positional args, we have a problem
        if self._load_balancer is None and len(args) == 0:
            raise BallastConfigurationException(
                "Expected either a collection of server "
                "addresses OR a ballast.LoadBalancer "
                "instance as an init parameter."
            )

        # either the load balancer is specified or the collection, not both
        if self._load_balancer is not None and len(args) > 0:
            raise BallastConfigurationException(
                "Keyword arg 'load_balancer' specified in addition to positional arg. "
                "Please either remove the positional arg, or specify the load balancer "
                "as the positional arg."
            )

        # load balancer or collection of servers
        # can be defined via 1st positional arg
        # (but only if load balancer not set via kwargs)
        a = args[0]
        if isinstance(a, LoadBalancer):
            self._load_balancer = a
        elif isinstance(a, ServerList):
            servers = a
            self._load_balancer = LoadBalancer(servers)
        elif hasattr(a, '__iter__') and not isinstance(a, basestring):
            servers = StaticServerList(a)
            self._load_balancer = LoadBalancer(servers)
        else:
            raise BallastConfigurationException(
                "An invalid configuration parameter was provided: %s" %
                a
            )

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
