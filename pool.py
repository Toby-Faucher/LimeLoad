from dataclasses import dataclass, field
from threading import RLock
from typing import List
from backend import Backend

@dataclass
class ServerPool:
    """
    Manages a pool of backend servers and provides a round-robin mechanism
    to select the next available backend.
    """
    backends: List[Backend]
    current: int = 0
    _lock: RLock = field( default_factory = RLock )

    def get_next_backend(self) -> Backend:
        """
        Returns the next available backend server using a round-robin approach.
        If a backend is not alive, it skips it and tries the next one.

        Raises:
            ConnectionError: If no backends are available or all backends are down.

        Returns:
            Backend: The next available Backend instance.
        """
        with self._lock:
            if not self.backends:
                raise ConnectionError("No backends available")

            start = self.current
            for i in range(len(self.backends)):
                index = (start + i) % len(self.backends)
                backend = self.backends[index]
                if backend.is_alive():
                    self.current = (index + 1) % len(self.backends)
                    return backend
            raise ConnectionError("All backends are down")


    def add_backend(self, backend: Backend):
        """
        Adds a new backend server to the pool.

        Args:
            backend (Backend): The Backend instance to add.
        """
        with self._lock:
            self.backends.append(backend)

    def remove_backend(self, backend: Backend):
        """
        Removes a backend server from the pool.

        Args:
            backend (Backend): The Backend instance to remove.
        """
        with self._lock:
            self.backends.remove(backend)
