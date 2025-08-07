import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.algorithms.base import LoadBalancingAlgorithm, Server, LoadBalancingContext
from load_balancer.algorithms.error import ServerNotFoundError
from typing import Optional
import pytest


class ConcreteLoadBalancingAlgorithm(LoadBalancingAlgorithm):
    """Concrete test implementation of LoadBalancingAlgorithm for testing"""

    def __init__(self, name: str = "TestAlgorithm"):
        super().__init__(name=name)

    def select_server(self, context: Optional[LoadBalancingContext] = None) -> Optional[Server]:
        """Simple selection: return first healthy server"""
        with self._lock:
            healthy_servers = self.get_healthy_servers()
            if not healthy_servers:
                self.on_selected_failed(context)
                return None

            server = healthy_servers[0]
            self.on_server_selected(server, context)
            return server

    def add_server(self, server: Server) -> None:
        """Add server to the algorithm"""
        with self._lock:
            super().add_server(server)

    def remove_server(self, server_id: str) -> bool:
        """Remove server from the algorithm"""
        with self._lock:
            return super().remove_server(server_id)


def test_algorithm_initialization():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    assert test_lb is not None
    assert test_lb.name == "Test"
    assert test_lb.get_server_count() == 0
    assert test_lb.get_healthy_server_count() == 0


def test_add_server():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)

    test_lb.add_server(server)

    assert test_lb.get_server_count() == 1
    assert test_lb.get_healthy_server_count() == 1
    assert test_lb.get_server("server1") is not None


def test_remove_server():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)

    test_lb.add_server(server)
    assert test_lb.get_server_count() == 1

    result = test_lb.remove_server("server1")

    assert result == True
    assert test_lb.get_server_count() == 0

    # Should raise exception when trying to get removed server
    with pytest.raises(ServerNotFoundError):
        test_lb.get_server("server1")


def test_select_server_no_servers():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")

    selected = test_lb.select_server()

    assert selected is None


def test_select_server_with_healthy_server():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)

    test_lb.add_server(server)
    selected = test_lb.select_server()

    assert selected is not None
    assert selected.id == "server1"


def test_select_server_with_context():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)
    context = LoadBalancingContext(client_ip="192.168.1.1")

    test_lb.add_server(server)
    selected = test_lb.select_server(context)

    assert selected is not None
    assert selected.id == "server1"


def test_algorithm_statistics():
    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)

    test_lb.add_server(server)
    test_lb.select_server()  # Should succeed

    stats = test_lb.get_statistics()

    assert stats['total_requests'] == 1
    assert stats['successful_selections'] == 1
    assert stats['failed_selections'] == 0
    assert stats['algorithm_name'] == "Test"
    assert stats['server_count'] == 1
    assert stats['healthy_server_count'] == 1


def test_multiple_servers():
    from load_balancer.algorithms.base import ServerStatus

    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server1 = Server(id="server1", address="localhost", port=8080)
    server2 = Server(id="server2", address="localhost", port=8081)
    server3 = Server(id="server3", address="localhost", port=8082, status=ServerStatus.UNHEALTHY)

    test_lb.add_server(server1)
    test_lb.add_server(server2)
    test_lb.add_server(server3)

    assert test_lb.get_server_count() == 3
    assert test_lb.get_healthy_server_count() == 2  # server3 is unhealthy

    # Should select a healthy server
    selected = test_lb.select_server()
    assert selected is not None
    assert selected.id in ["server1", "server2"]


def test_server_status_update():
    from load_balancer.algorithms.base import ServerStatus

    test_lb = ConcreteLoadBalancingAlgorithm("Test")
    server = Server(id="server1", address="localhost", port=8080)

    test_lb.add_server(server)
    assert test_lb.get_healthy_server_count() == 1

    # Update server status to unhealthy
    test_lb.update_server_status("server1", ServerStatus.UNHEALTHY)
    assert test_lb.get_healthy_server_count() == 0

    # Update server status back to healthy
    test_lb.update_server_status("server1", ServerStatus.HEALTHY)
    assert test_lb.get_healthy_server_count() == 1
