from dataclasses import dataclass
from typing import List
from backend import Backend

@dataclass
class ServerPool:
    backends: List[Backend]
    current: int = 0

    def get_next_backend(self) -> Backend:
        backend = self.backends[self.current]
        self.current = (self.current + 1) % len(self.backends)
        return backend
