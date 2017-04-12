import urlparse
import urllib


class UrlBuilder(object):

    def __init__(self):
        self._scheme = None
        self._hostname = None
        self._port = None
        self._path = None
        self._query = dict()
        self._username = None
        self._password = None
        self._fragment = None

    @staticmethod
    def from_url(url):
        parts = urlparse.urlparse(url)
        return UrlBuilder.from_parts(
            parts.scheme,
            parts.username,
            parts.password,
            parts.hostname,
            parts.port,
            parts.path,
            parts.query,
            parts.fragment
        )

    @staticmethod
    def from_parts(
            scheme=None,
            username=None,
            password=None,
            hostname=None,
            port=None,
            path=None,
            query=None,
            fragment=None
    ):

        builder = UrlBuilder().\
            scheme(scheme).\
            username(username).\
            password(password).\
            hostname(hostname).\
            port(port).\
            path(path).\
            fragment(fragment)

        if query is not None:
            if isinstance(query, basestring):
                builder._query = urlparse.parse_qs(query)
            elif isinstance(query, dict):
                # TODO: validate structure?
                builder._query = query
            else:
                raise Exception('Query format unexpected!')

        return builder

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            self.build()
        )

    def __str__(self):
        return self.build()

    def __unicode__(self):
        return self.build()

    def scheme(self, value):
        self._scheme = value
        return self

    def http(self):
        self._scheme = 'http'
        return self

    def https(self):
        self._scheme = 'https'
        return self

    def hostname(self, value):
        self._hostname = value
        return self

    def port(self, value):
        self._port = value
        return self

    def path(self, value):
        self._path = value
        return self

    def username(self, value):
        self._username = value
        return self

    def password(self, value):
        self._password = value
        return self

    def fragment(self, value):
        self._fragment = value
        return self

    def add_query_param(self, key, value):

        if key not in self._query:
            self._query[key] = []

        self._query[key].append(value)

        return self

    def remove_query_param(self, key, value=None):

        # nothing to do if the key isn't in there
        if key not in self._query:
            return self

        # if value is None, remove all
        # params for the specified key
        if value is None:
            del self._query[key]
            return self

        # otherwise, just remove the specified
        # value from the query param list for
        # the specified key
        l = self._query[key]
        l.remove(value)

        # if there are no more values,
        # remove the key from the dictionary
        if len(l) == 0:
            del self._query[key]

        return self

    def append_path(self, path):
        base = self._path

        if not base.endswith('/'):
            base += '/'

        self._path = urlparse.urljoin(base, path)

        return self

    def build(self):
        # create the array the unparse method expects
        # and populate with our values
        parts = [''] * 6
        parts[0] = self._scheme
        parts[1] = self._build_host()
        parts[2] = self._path
        parts[4] = urllib.urlencode(self._query, 1)
        parts[5] = self._fragment

        # finally, create the url from the parts
        return urlparse.urlunparse(parts)

    def _build_host(self):

        if self._username is not None:
            host = '{}:{}@{}'.format(
                self._username,
                self._password,
                self._hostname
            )
        else:
            host = self._hostname

        if self._port is not None:
            host += ':{}'.format(self._port)

        return host
