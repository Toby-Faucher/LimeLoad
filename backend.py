from dataclasses import dataclass, field
from urllib.parse import ParseResult, urlparse
from threading import RLock
import requests

@dataclass
class Backend:
    url: str | ParseResult
    alive: bool = True
    _lock: RLock = field(default_factory=RLock)
    _session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self):
        if isinstance(self.url, str):
            self.url = urlparse(self.url)
            # NOTE: Setup pooling options here
            self._session.headers.update( { 'Connection': 'keep-alive' } )

    def set_alive(self, alive: bool):
        with self._lock:
            self.alive = alive

    def is_alive(self) -> bool:
        with self._lock:
            return self.alive

    def health_check(self):
        """Performs a health check on the backend."""
        try:
            parsed_url = self.url if isinstance(self.url, ParseResult) else urlparse(self.url)
            target_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            response = self._session.head(target_url, timeout=1)
            self.set_alive(response.status_code == 200)
        except requests.exceptions.RequestException:
            self.set_alive(False)

    def proxy_request( self, method, path, headers = None, data = None, **kwargs ):
        # Handles the proxying
        parsed_url = self.url if isinstance(self.url, ParseResult) else urlparse(self.url)
        target_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
        return self._session.request(
                method,
                target_url,
                headers = headers,
                data = data,
                **kwargs
                )
