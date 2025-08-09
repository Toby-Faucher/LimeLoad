import threading
from typing import Optional
from .base import LoadBalancingAlgorithm, LoadBalancingContext, Server, ServerType
from load_balancer.algorithms.error import NoHealthyServersError, InvalidServerConfigurationError, ServerAlreadyExistsError, ServerNotFoundError

class RoundRobin(LoadBalancingAlgorithm):
    def __init__(self):
        super().__init__("Round Robin")
        self.current_server_index = 0
        self._lock = threading.RLock()

    def select_server(self, context: Optional[LoadBalancingContext] = None) -> Optional[Server]:
        with self._lock:
            healthy_servers = self.get_healthy_servers()
            if not healthy_servers:
                self._log_selection(None, context)
                raise NoHealthyServersError("No healthy servers available")

            if self.current_server_index >= len(healthy_servers):
                self.current_server_index = 0

            selected_server = healthy_servers[self.current_server_index]
            self.current_server_index = (self.current_server_index + 1) % len(healthy_servers)
            self._log_selection(selected_server, context)
            return selected_server

    def add_server(self, server: Server[ServerType]) -> None:
        super().add_server(server)

    def remove_server(self, server_id: str) -> bool:
        with self._lock:
            if server_id in self.healthy_servers:
                removed_server = self.healthy_servers[server_id]
                healthy_server_list = self.get_healthy_servers()
                if removed_server in healthy_server_list:
                    removed_index = healthy_server_list.index(removed_server)
                    if removed_index < self.current_server_index:
                        self.current_server_index = (self.current_server_index - 1) % len(healthy_server_list)
        return super().remove_server(server_id)
