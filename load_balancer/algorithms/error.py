from typing import Optional

class BaseLoadBalancingError(Exception):
    """Base exception for all load balancing errors."""

class ServerError(BaseLoadBalancingError):
    """
    Base exception for server-related errors that can potentially be handled
    without terminating the load balancer.
    """

    def __init__(self, *args, server_id: Optional[str] = None) -> None:
        """
        Initializes the ServerError.

        Args:
            *args: Arguments to pass to the base Exception class.
            server_id: The ID of the server related to the error.
        """
        super().__init__(*args)
        self.server_id = server_id


class NoHealthyServersError(ServerError):
    """Raised when no healthy servers are available to handle a request."""

class ServerNotFoundError(ServerError):
    """Raised when a specific server is not found in the pool."""

class ServerAlreadyExistsError(ServerError):
    """Raised when attempting to add a server that already exists in the pool."""

class InvalidServerConfigurationError(ServerError):
    """Raised when a server's configuration is invalid."""

class InvalidMetricKeyError(ServerError):
    """Raised when an invalid metric key is provided."""

class AlgorithmError(BaseLoadBalancingError):
    """Base exception for algorithm-specific errors."""

class AlgorithmConfigurationError(AlgorithmError):
    """Raised when a load balancing algorithm is configured incorrectly."""

class SelectionError(AlgorithmError):
    """Raised when an error occurs during the server selection process."""

class ContextError(BaseLoadBalancingError):
    """Base exception for errors related to the request context."""

class InvalidContextError(ContextError):
    """Raised when the request context is invalid or incomplete."""

class HealthCheckError(BaseLoadBalancingError):
    """Base exception for errors related to health checks."""

class HealthCheckFailedError(HealthCheckError):
    """Raised when a health check fails for a server."""

class HealthCheckConfigurationError(HealthCheckError):
    """Raised when a health check is configured incorrectly."""
