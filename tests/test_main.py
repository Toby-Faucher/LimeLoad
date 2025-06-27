import unittest
from unittest.mock import patch, MagicMock
from main import LoadBalancer

class TestLoadBalancer(unittest.TestCase):

    @patch('main.pool')
    @patch('http.server.BaseHTTPRequestHandler.__init__')
    def test_health_check(self, mock_init, mock_pool):
        mock_init.return_value = None
        mock_backend1 = MagicMock()
        mock_backend2 = MagicMock()
        mock_pool.backends = [mock_backend1, mock_backend2]

        handler = LoadBalancer(None, None, None)
        handler.path = '/health'
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = MagicMock()

        handler.health_check()

        mock_backend1.health_check.assert_called_once()
        mock_backend2.health_check.assert_called_once()
        handler.send_response.assert_called_with(200)
        handler.end_headers.assert_called_once()
        handler.wfile.write.assert_called_with(b"Health checks performed.")

if __name__ == '__main__':
    unittest.main()
