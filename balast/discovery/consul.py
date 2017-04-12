import logging
import requests
from balast.util import UrlBuilder
from balast.discovery import Server, ServerList


class ConsulRestRecordList(ServerList):

    _SERVICE_URL = '/v1/catalog/service/'

    def __init__(self, base_url, service, dc=None, near=None, tag=None):
        super(ConsulRestRecordList, self).__init__()
        self.base_url = base_url
        self.service = service
        self.dc = dc
        self.near = near
        self.tag = tag
        self._logger = logging.getLogger(self.__module__)

    def get_servers(self):

        try:
            url = UrlBuilder.from_url(self.base_url)
            url.path(self._SERVICE_URL)
            url.append_path(self.service)

            if self.dc is not None:
                url.add_query_param('dc', self.dc)

            if self.near is not None:
                url.add_query_param('near', self.near)

            if self.tag is not None:
                url.add_query_param('tag', self.tag)

            response = requests.get(unicode(url))
            json = response.json()

            for entry in json:
                s = Server(
                    entry['Address'],
                    entry['ServicePort'],
                    ttl=10
                )

                self._logger.debug("Created server from Consul REST API record: %s", s)

                yield s

        except:
            return
