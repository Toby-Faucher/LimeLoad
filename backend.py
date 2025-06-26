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
