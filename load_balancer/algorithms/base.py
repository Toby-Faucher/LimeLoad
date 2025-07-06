from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
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
        self.servers: Dict[str, Server[ServerType]] = {}
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

    def update_sever_metrics(self, server_id: str, **metrics) -> bool:
        """
        Update metrics for a specific server.
        
        Args:
            server_id: ID of the server to update
            **metrics: Metric key-value pairs to update
            
        Returns:
            True if server was found and updated, False otherwise
        """
        server = self.get_server(server_id)

        if server:
            server.update_metrics(**metrics)
            self.on_server_metrics_updated(server)
            return True
        return False

    def update_server_status(self, server_id: str, status: ServerStatus) -> bool:
        """
        Update the status of a specific server.
        
        Args:
            server_id: ID of the server to update
            status: New server status
            
        Returns:
            True if server was found and updated, False otherwise
        """
        server = self.get_server(server_id)
        if server:
            old_status = server.status
            server.status = status
            self.on_server_status_updated(server, old_status, status)
            return True
        return False

    def get_server(self, server_id: str) -> Optional[Server[ServerType]]:
        """
        Get a server by its ID.
        
        Args:
            server_id: ID of the server to retrieve
            
        Returns:
            Server instance or None if not found
        """
        return self.servers.get(server_id)

    def get_healthy_servers(self) -> List[Server[ServerType]]:
        """
        Get list of healthy servers available for load balancing.
        
        Returns:
            List of healthy servers
        """
        return [server for server in self.servers.values() if server.is_available]

    def get_server_count(self) -> int:
        """ Get total number of servers in the pool"""
        return len(self.servers)

    def get_healthy_server_count(self) -> int:
        """ Get total number of healthy servers in the pool"""
        return len(self.get_healthy_servers())

    def reset_statistics(self) -> None:
        """Resets algo statistics"""
        self.statistics = {
                'total_requests': 0,
                'successful_selections': 0,
                'failed_selections': 0,
                'last_reset': time.time(),
        }
        self.on_statistics_reset()

    def get_statistics(self) -> Dict[str,Any]:
        """
        Get algorithm statistics.
        
        Returns:
            Dictionary containing algorithm statistics        
        """

        stats = self.statistics.copy()
        stats['success_rate'] = ( 
                stats['successful_selections'] / max(stats['total_requests'], 1 )
        )        
        stats['algorithm_name'] = self.name
        stats['server_count'] = self.get_server_count()
        stats['healthy_server_count'] = self.get_healthy_server_count()
        
        return stats

    # Hooks

    def on_server_added(self, server: Server[ServerType]) -> None:
        """
        Hook for when a server is added to the pool.

        Args:
            server: the server that was added
        """
        self.logger.info(f"Server {server.id} added to {self.name} algorithm")

    def on_server_removed(self, server: Server[ServerType]) -> None:
        """
        Hook for when a server is removed from the pool.

        Args:
            server: the server that was removed
        """
        self.logger.info(f"Server {server.id} removed from {self.name} algorithm")


    def on_server_selected(self, server: Server[ServerType], context: Optional[LoadBalancingContext]) -> None 
        """
        Hook for when a server is selected.

        Args:
            server: the server that was selected
            context: Request context for the selection
        """

        self.statistics['total_requests'] += 1
        self.statistics['successful_selections'] += 1
        self.logger.info(f"Selected server {server.id} using {self.name} algorithm")

    def on_selected_failed(self, context: Optional[LoadBalancingContext]) -> None 
        """
        Hook for when a server selection fails.

        Args:
            context: Request context for the selection
        """

        self.statistics['total_requests'] += 1
        self.statistics['failed_selections'] += 1
        self.logger.info(f"Server selection failed using {self.name} algorithm")

    def on_server_status_updated(self, server: Server[ServerType], old_status: ServerStatus, new_status: ServerStatus) -> None:
        """
        Hook called when the server status is updated.

       Args:
           server: The server whose status updated
           old_status: Previous server status
           new_status: New server status
        """
        self.logger.info(f"Server {server.id} status updated to {new_status.value} from {old_status.value}")

    def on_server_metrics_updated(self, server: Server[ServerType]]) -> None:
        """
        Hook called when a server's metrics are updated.
        
        Args:
            server: The server whose metrics were updated
        """
        pass # override in subclass if needed

    def on_statistics_reset(self) -> None:
        """Hook for when the statistics are reset"""
        
        self.logger.info(f"Server statistics reset for {self.name} algorithm")

    # Util methods

    def _validate_server(self, server: Server[ServerType]) -> bool:
        """
        Validate server configuration.
        
        Args:
            server: Server to validate
            
        Returns:
            True if server is valid, False otherwise
        """
        if not server.id or not server.address or server.port <= 0:
            return False
        if server.weight < 0:
            return False
        return True

    def _log_section(self, server: Optional[Server[ServerType]], context: Optional[LoadBalancingContext]) -> None:
        """
        Log the server selection result.
        
        Args:
            server: Selected server (None if selection failed)
            context: Request context
        """
        if server:
            self.on_server_selected(server, context)
        else:
            self.on_selected_failed(context)

    def __str__(self) -> str:
        """String representation of the algorithm."""
        return f"{self.name} (servers: {self.get_server_count()}, healthy: {self.get_healthy_server_count()})"

    def __repr__(self) -> str:
        """Detailed string representation of the algorithm."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"servers={self.get_server_count()},"
                f"healthy={self.get_healthy_server_count()}")
