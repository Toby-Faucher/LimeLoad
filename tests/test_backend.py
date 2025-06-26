
import unittest
from urllib.parse import urlparse
from backend import Backend

class TestBackend(unittest.TestCase):

    def test_backend_initialization(self):
        url = "http://example.com"
        backend = Backend(url=url)
        self.assertEqual(backend.url, urlparse(url))
        self.assertTrue(backend.alive)

    def test_backend_post_init(self):
        url = "http://example.com"
        backend = Backend(url=url)
        self.assertEqual(backend.url, urlparse(url))

if __name__ == '__main__':
    unittest.main()
