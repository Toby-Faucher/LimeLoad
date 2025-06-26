
import unittest
from backend import Backend
from pool import ServerPool

class TestServerPool(unittest.TestCase):

    def test_pool_initialization(self):
        backends = [Backend(url="http://localhost:8080"), Backend(url="http://localhost:8081")]
        pool = ServerPool(backends=backends)
        self.assertEqual(pool.backends, backends)
        self.assertEqual(pool.current, 0)

    def test_get_next_backend_empty(self):
        pool = ServerPool(backends=[])
        with self.assertRaises(IndexError):
            pool.get_next_backend()

    def test_get_next_backend_rotation(self):
        b1 = Backend(url="http://localhost:8080")
        b2 = Backend(url="http://localhost:8081")
        pool = ServerPool(backends=[b1, b2])
        
        self.assertEqual(pool.get_next_backend(), b1)
        self.assertEqual(pool.get_next_backend(), b2)
        self.assertEqual(pool.get_next_backend(), b1)

if __name__ == '__main__':
    unittest.main()
