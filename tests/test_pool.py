
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
        with self.assertRaises(ConnectionError):
            pool.get_next_backend()

    def test_get_next_backend_all_dead(self):
        b1 = Backend(url="http://localhost:8080")
        b1.set_alive(False)
        b2 = Backend(url="http://localhost:8081")
        b2.set_alive(False)
        pool = ServerPool(backends=[b1, b2])
        with self.assertRaises(ConnectionError):
            pool.get_next_backend()

    def test_get_next_backend_rotation(self):
        b1 = Backend(url="http://localhost:8080")
        b2 = Backend(url="http://localhost:8081")
        pool = ServerPool(backends=[b1, b2])
        
        self.assertEqual(pool.get_next_backend(), b1)
        self.assertEqual(pool.get_next_backend(), b2)
        self.assertEqual(pool.get_next_backend(), b1)

    def test_get_next_backend_skips_dead(self):
        b1 = Backend(url="http://localhost:8080")
        b2 = Backend(url="http://localhost:8081")
        b2.set_alive(False)
        b3 = Backend(url="http://localhost:8082")
        pool = ServerPool(backends=[b1, b2, b3])

        self.assertEqual(pool.get_next_backend(), b1)
        self.assertEqual(pool.get_next_backend(), b3)
        self.assertEqual(pool.get_next_backend(), b1)

if __name__ == '__main__':
    unittest.main()
