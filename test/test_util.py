import unittest
from past.builtins import unicode
from balast.util import UrlBuilder
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


class UrlBuilderTest(unittest.TestCase):

    def test_builder_url_should_be_same(self):

        expected_url = 'http://test.com/path/to/resource'
        url = UrlBuilder.from_url(expected_url)

        self.assertEqual(expected_url, unicode(url))

        expected_url = 'http://my-user:my-pass@test.com:8080/some/path?test=hi&test=hi2&other=bye#my-frag/path/to/frag'
        url = UrlBuilder.from_url(expected_url)

        actual_url = urlparse(unicode(url))
        actual_query = parse_qs(actual_url.query)

        self.assertEqual(actual_url.scheme, 'http')
        self.assertEqual(actual_url.username, 'my-user')
        self.assertEqual(actual_url.password, 'my-pass')
        self.assertEqual(actual_url.hostname, 'test.com')
        self.assertEqual(actual_url.path, '/some/path')
        self.assertEqual(actual_url.fragment, 'my-frag/path/to/frag')
        self.assertIn('hi', actual_query['test'])
        self.assertIn('hi2', actual_query['test'])
        self.assertIn('bye', actual_query['other'])
