from dataclasses import dataclass, field
from urllib.parse import ParseResult, urlparse
from threading import RLock
import requests

@dataclass
class Backend:
    """
    Represents a single backend server in the load balancer.

    Attributes:
        url (str | ParseResult): The URL of the backend server.
        alive (bool): Indicates if the backend is currently considered alive.
        _lock (RLock): A reentrant lock for thread-safe access to `alive` status.
        _session (requests.Session): A requests session for making HTTP requests to the backend.
        _parsed_url (ParseResult): The parsed URL of the backend.
        _base_url (str): The base URL (scheme://netloc) of the backend.
    """
    url: str | ParseResult
    alive: bool = True
    _lock: RLock = field(default_factory=RLock)
    _session: requests.Session = field(default_factory=requests.Session)
    _parsed_url: ParseResult = field(init=False)
    _base_url: str = field(init=False)

    def __post_init__(self):
        """
        Initializes the Backend instance after __init__ and sets up the parsed URL,
        base URL, and session headers.
        """
        if isinstance(self.url, str):
            self._parsed_url = urlparse(self.url)
        else:
            self._parsed_url = self.url
        self._base_url = f"{self._parsed_url.scheme}://{self._parsed_url.netloc}"
        # NOTE: Setup pooling options here
        self._session.headers.update( { 'Connection': 'keep-alive' } )

    def set_alive(self, alive: bool):
        """
        Sets the alive status of the backend in a thread-safe manner.

        Args:
            alive (bool): The new alive status.
        """
        with self._lock:
            self.alive = alive

    def is_alive(self) -> bool:
        """
        Checks if the backend is alive in a thread-safe manner.

        Returns:
            bool: True if the backend is alive, False otherwise.
        """
        with self._lock:
            return self.alive

    def health_check(self):
        """
        Performs a health check on the backend by sending a HEAD request to its base URL.
        Updates the `alive` status based on the response.
        """
        try:
            response = self._session.head(self._base_url, timeout=1)
            self.set_alive(response.status_code == 200)
        except requests.exceptions.RequestException:
            self.set_alive(False)

    def proxy_request( self, method, path, headers = None, data = None, **kwargs ):
        """
        Proxies an incoming request to this backend server.

        Args:
            method (str): The HTTP method of the request (e.g., 'GET', 'POST').
            path (str): The path of the request.
            headers (dict, optional): The headers of the request. Defaults to None.
            data (bytes, optional): The body of the request. Defaults to None.
            **kwargs: Additional keyword arguments to pass to the requests.request method.

        Returns:
            requests.Response: The response from the backend server.
        """
        target_url = f"{self._base_url}{path}"
        return self._session.request(
                method,
                target_url,
                headers = headers,
                data = data,
                **kwargs
                )
