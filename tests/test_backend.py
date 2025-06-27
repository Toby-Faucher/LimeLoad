import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, ParseResult
from threading import RLock
import requests
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
        self.assertTrue(hasattr(backend._lock, 'acquire'))
        self.assertTrue(hasattr(backend._lock, 'release'))
        self.assertIsInstance(backend._session, requests.Session)
        self.assertEqual(backend._session.headers['Connection'], 'keep-alive')

    def test_set_alive(self):
        backend = Backend(url="http://example.com")
        self.assertTrue(backend.is_alive())
        backend.set_alive(False)
        self.assertFalse(backend.is_alive())

    @patch('requests.Session.head')
    def test_health_check_alive(self, mock_head):
        mock_head.return_value.status_code = 200
        backend = Backend(url="http://example.com")
        backend.health_check()
        self.assertTrue(backend.is_alive())

    @patch('requests.Session.head')
    def test_health_check_dead(self, mock_head):
        mock_head.side_effect = requests.exceptions.RequestException
        backend = Backend(url="http://example.com")
        backend.health_check()
        self.assertFalse(backend.is_alive())

    def test_proxy_request(self):
        url = "http://example.com"
        backend = Backend(url=url)
        
        with patch.object(backend._session, 'request') as mock_request:
            method = "GET"
            path = "/test"
            headers = {"Content-Type": "application/json"}
            data = '{"key": "value"}'
            
            backend.proxy_request(method, path, headers=headers, data=data)
            
            parsed_url = backend.url if isinstance(backend.url, ParseResult) else urlparse(backend.url)
            expected_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
            mock_request.assert_called_once_with(
                method,
                expected_url,
                headers=headers,
                data=data
            )

if __name__ == '__main__':
    unittest.main()
