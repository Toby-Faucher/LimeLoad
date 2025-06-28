from abc import ABC, abstractmethod
from re import L
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import time
import logging


ServerType = TypeVar('ServerType')

class ServerStatus(Enum):
    """Server health status enum"""
    HEALTHY = "healthly"
    UNHEALTHY = "unhealthly"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


@dataclass
class ServerMetrics:
    """Container for server performance"""
    response_time: float = 0.0
    active_connections: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    last_updated: float = field( default_factory = time.time )

    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()
    
    @property
    def is_stale(self, threshold: float = 30.0) -> bool:
        """Check if metrics are stale based on 30 second threshold"""
        # TODO: When the config file structure is created make the threshold changable
        return time.time() - self.last_updated > threshold 


@dataclass
class Server(Generic[ServerType]):
    """Represents the backend server in the LB pool"""
    id: str
    address: str
    port: int
    weight: float = 1.0
    status: ServerStatus = ServerStatus.HEALTHY
    metrics: ServerMetrics = field( default_factory = ServerMetrics)
    metadata: Dict[ str, Any ] = field( default_factory = dict)
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ServerMetrics()

    @property
    def is_available(self) -> bool:
        """Checks if the server is available to handle requests"""
        return self.status == ServerStatus.HEALTHY

    @property
    def endpoint(self) -> str:
        """Get the servers endpoint"""
        return f"{self.address}:{self.port}"

    def update_metrics(self, **kwargs) -> None:
        """Update the servs metrics with new values"""
            
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
            self.metrics.last_updated = time.time()

@dataclass
class LoadBalancingContext:
    """Context info for LB decisions"""
    client_ip: Optional[str] = None
    session_ip: Optional[str] = None
    request_headers: Dict[str, str] = field( default_factory = dict)
    request_path: str = ""
    request_method: str = "GET"
    previous_server: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[ str, Any ] = field( default_factory = dict )

    def __post_init__(self):
        if self.request_headers is None:
            self.request_headers = {}
        if self.metadata is None:
            self.metadata = {}


class LoadBalancingAlgorithm(ABC, Generic[ServerType]):
    """
    Abstract base class for load balancing algorithms.

     This class defines the interface that all load balancing algorithms
     will implement, along with some util.
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """
        Initializes the load balancer

        Args:
            name: Name of the algo
            logger: Optional logger instance
        """

        self.name = name
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.servers: List[Server[ServerType]] = []
        self.statistics = {
            'total_requests': 0,
            'successful_selections': 0,
            'failed_selections': 0,
            'last_reset': time.time(),
        }

    @abstractmethod
    def select_server(self, context: Optional[LoadBalancingContext] = None) -> Optional[Server[ServerType]]:
        """
        Select the best server based on your needs

        Args:
            context: Optional context info about the request

        Returns:
            Selected Server or None if no servers are available
        """
        pass

    @abstractmethod
    def add_server(self, server: Server[ServerType]) -> None:
        """
        Adds a server to the LB pool.

        Args:
            server: Server instance to add
        """
        pass
    
    @abstractmethod
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server from the LB pool.

        Args:
            server_id: ID of the server to remove

        Returns:
            True if server was removed, False if not found
        """
        pass
