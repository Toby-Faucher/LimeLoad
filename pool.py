from dataclasses import dataclass, field
from threading import RLock
from typing import List
from backend import Backend

@dataclass
class ServerPool:
    backends: List[Backend]
    current: int = 0
    _lock: RLock = field( default_factory = RLock )

    def get_next_backend(self) -> Backend:
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
