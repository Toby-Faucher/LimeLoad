import pytest
import threading
import time
from unittest.mock import Mock, patch
from typing import List

from load_balancer.algorithms.round_robin import RoundRobin
from load_balancer.algorithms.base import Server, ServerStatus, ServerMetrics, LoadBalancingContext
from load_balancer.algorithms.error import (
    NoHealthyServersError,
    ServerAlreadyExistsError,
    ServerNotFoundError,
    InvalidServerConfigurationError
)


class TestRoundRobin:
    """Test suite for the Round Robin load balancing algorithm."""

    @pytest.fixture
    def round_robin(self):
        """Create a fresh RoundRobin instance for each test."""
        return RoundRobin()

    @pytest.fixture
    def sample_servers(self):
        """Create sample servers for testing."""
        return [
            Server(id="server1", address="192.168.1.1", port=8080, weight=1.0),
            Server(id="server2", address="192.168.1.2", port=8080, weight=1.0),
            Server(id="server3", address="192.168.1.3", port=8080, weight=1.0),
        ]

    @pytest.fixture
    def unhealthy_server(self):
        """Create an unhealthy server for testing."""
        server = Server(id="unhealthy", address="192.168.1.4", port=8080)
        server.status = ServerStatus.UNHEALTHY
        return server

    def test_initialization(self, round_robin):
        """Test that RoundRobin initializes correctly."""
        assert round_robin.name == "Round Robin"
        assert round_robin.current_server_index == 0
        assert len(round_robin.servers) == 0
        assert len(round_robin.healthy_servers) == 0
        assert round_robin._lock is not None

    def test_add_single_server(self, round_robin, sample_servers):
        """Test adding a single server to the pool."""
        server = sample_servers[0]
        round_robin.add_server(server)

        assert len(round_robin.servers) == 1
        assert len(round_robin.healthy_servers) == 1
        assert round_robin.get_server("server1") == server

    def test_add_multiple_servers(self, round_robin, sample_servers):
        """Test adding multiple servers to the pool."""
        for server in sample_servers:
            round_robin.add_server(server)

        assert len(round_robin.servers) == 3
        assert len(round_robin.healthy_servers) == 3

        for server in sample_servers:
            assert round_robin.get_server(server.id) == server

    def test_add_duplicate_server(self, round_robin, sample_servers):
        """Test that adding a duplicate server raises an exception."""
        server = sample_servers[0]
        round_robin.add_server(server)

        with pytest.raises(ServerAlreadyExistsError):
            round_robin.add_server(server)

    def test_add_invalid_server(self, round_robin):
        """Test adding servers with invalid configurations."""
        # Server with empty ID
        invalid_server1 = Server(id="", address="192.168.1.1", port=8080)
        with pytest.raises(InvalidServerConfigurationError):
            round_robin.add_server(invalid_server1)

        # Server with empty address
        invalid_server2 = Server(id="test", address="", port=8080)
        with pytest.raises(InvalidServerConfigurationError):
            round_robin.add_server(invalid_server2)

        # Server with invalid port
        invalid_server3 = Server(id="test", address="192.168.1.1", port=0)
        with pytest.raises(InvalidServerConfigurationError):
            round_robin.add_server(invalid_server3)

        # Server with negative weight
        invalid_server4 = Server(id="test", address="192.168.1.1", port=8080, weight=-1.0)
        with pytest.raises(InvalidServerConfigurationError):
            round_robin.add_server(invalid_server4)

    def test_remove_existing_server(self, round_robin, sample_servers):
        """Test removing an existing server from the pool."""
        for server in sample_servers:
            round_robin.add_server(server)

        result = round_robin.remove_server("server1")

        assert result is True
        assert len(round_robin.servers) == 2
        assert len(round_robin.healthy_servers) == 2
        assert "server1" not in round_robin.servers
        assert "server1" not in round_robin.healthy_servers

    def test_remove_nonexistent_server(self, round_robin):
        """Test removing a server that doesn't exist."""
        with pytest.raises(ServerNotFoundError):
            round_robin.remove_server("nonexistent")

    def test_select_server_no_servers(self, round_robin):
        """Test server selection when no servers are available."""
        with pytest.raises(NoHealthyServersError):
            round_robin.select_server()

    def test_select_server_no_healthy_servers(self, round_robin, unhealthy_server):
        """Test server selection when no healthy servers are available."""
        round_robin.add_server(unhealthy_server)

        with pytest.raises(NoHealthyServersError):
            round_robin.select_server()

    def test_select_server_single_server(self, round_robin, sample_servers):
        """Test server selection with a single healthy server."""
        server = sample_servers[0]
        round_robin.add_server(server)

        selected = round_robin.select_server()

        assert selected == server
        assert round_robin.current_server_index == 0  # Should wrap to 0

    def test_select_server_round_robin_behavior(self, round_robin, sample_servers):
        """Test that server selection follows round-robin pattern."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Test multiple rounds to ensure proper cycling
        expected_order = ["server1", "server2", "server3", "server1", "server2", "server3"]

        for expected_id in expected_order:
            selected = round_robin.select_server()
            assert selected.id == expected_id

    def test_select_server_with_context(self, round_robin, sample_servers):
        """Test server selection with LoadBalancingContext."""
        for server in sample_servers:
            round_robin.add_server(server)

        context = LoadBalancingContext(
            client_ip="192.168.1.100",
            request_path="/api/test",
            request_method="GET"
        )

        selected = round_robin.select_server(context)
        assert selected is not None
        assert selected.id == "server1"

    def test_server_removal_index_adjustment(self, round_robin, sample_servers):
        """Test that current_server_index is properly adjusted when servers are removed."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Select server1 to advance the index
        round_robin.select_server()  # server1, index becomes 1

        # Remove server1 (index 0), which is before current index (1)
        round_robin.remove_server("server1")

        # Next selection should be server2 (originally index 1, now index 0)
        selected = round_robin.select_server()
        assert selected.id == "server2"

    def test_server_status_update_affects_selection(self, round_robin, sample_servers):
        """Test that server status updates affect which servers are selected."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Mark server2 as unhealthy
        round_robin.update_server_status("server2", ServerStatus.UNHEALTHY)

        # Only server1 and server3 should be selected
        selected_ids = set()
        for _ in range(6):  # Multiple rounds
            selected = round_robin.select_server()
            selected_ids.add(selected.id)

        assert selected_ids == {"server1", "server3"}
        assert "server2" not in selected_ids

    def test_server_status_recovery(self, round_robin, sample_servers):
        """Test that recovered servers are included in selection again."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Mark server2 as unhealthy, then recover it
        round_robin.update_server_status("server2", ServerStatus.UNHEALTHY)
        round_robin.update_server_status("server2", ServerStatus.HEALTHY)

        # All servers should be selectable again
        selected_ids = set()
        for _ in range(6):  # Multiple rounds
            selected = round_robin.select_server()
            selected_ids.add(selected.id)

        assert selected_ids == {"server1", "server2", "server3"}

    def test_thread_safety_concurrent_selection(self, round_robin, sample_servers):
        """Test that concurrent server selection is thread-safe."""
        for server in sample_servers:
            round_robin.add_server(server)

        selected_servers = []
        threads = []

        def select_servers():
            for _ in range(10):
                try:
                    server = round_robin.select_server()
                    selected_servers.append(server.id)
                except Exception as e:
                    selected_servers.append(f"ERROR: {e}")

        # Start multiple threads
        for _ in range(5):
            thread = threading.Thread(target=select_servers)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All selections should succeed (no errors)
        errors = [s for s in selected_servers if s.startswith("ERROR:")]
        assert len(errors) == 0

        # Should have equal distribution (within reasonable variance)
        server_counts = {"server1": 0, "server2": 0, "server3": 0}
        for server_id in selected_servers:
            if server_id in server_counts:
                server_counts[server_id] += 1

        # Each server should be selected at least once
        assert all(count > 0 for count in server_counts.values())

    def test_thread_safety_concurrent_add_remove(self, round_robin):
        """Test that concurrent add/remove operations are thread-safe."""
        results = {"added": [], "removed": [], "errors": []}

        def add_servers():
            for i in range(5):
                try:
                    server = Server(id=f"add_server_{i}", address=f"192.168.1.{i+10}", port=8080)
                    round_robin.add_server(server)
                    results["added"].append(server.id)
                except Exception as e:
                    results["errors"].append(f"ADD ERROR: {e}")

        def remove_servers():
            for i in range(3):
                try:
                    round_robin.remove_server(f"add_server_{i}")
                    results["removed"].append(f"add_server_{i}")
                except Exception as e:
                    results["errors"].append(f"REMOVE ERROR: {e}")

        # Add some initial servers
        for i in range(3):
            server = Server(id=f"initial_{i}", address=f"192.168.1.{i}", port=8080)
            round_robin.add_server(server)

        # Start concurrent operations
        add_thread = threading.Thread(target=add_servers)
        remove_thread = threading.Thread(target=remove_servers)

        add_thread.start()
        time.sleep(0.01)  # Small delay to ensure some servers are added first
        remove_thread.start()

        add_thread.join()
        remove_thread.join()

        # Check that operations completed successfully
        assert len(results["added"]) == 5
        assert len(results["removed"]) == 3
        # Some remove operations might fail if servers aren't added yet, which is acceptable

    def test_index_reset_when_exceeds_healthy_servers(self, round_robin, sample_servers):
        """Test that index resets when it exceeds the number of healthy servers."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Advance to the last server
        round_robin.current_server_index = 2

        # Remove servers to make current index invalid
        round_robin.remove_server("server2")
        round_robin.remove_server("server3")

        # Selection should work and reset index
        selected = round_robin.select_server()
        assert selected.id == "server1"
        assert round_robin.current_server_index == 0

    def test_statistics_tracking(self, round_robin, sample_servers):
        """Test that statistics are properly tracked during selections."""
        for server in sample_servers:
            round_robin.add_server(server)

        initial_stats = round_robin.get_statistics()

        # Make several successful selections
        for _ in range(5):
            round_robin.select_server()

        stats = round_robin.get_statistics()

        assert stats['total_requests'] == initial_stats['total_requests'] + 5
        assert stats['successful_selections'] == initial_stats['successful_selections'] + 5
        assert stats['failed_selections'] == initial_stats['failed_selections']

    def test_statistics_tracking_failures(self, round_robin):
        """Test that failed selections are tracked in statistics."""
        initial_stats = round_robin.get_statistics()

        # Try to select from empty pool
        try:
            round_robin.select_server()
        except NoHealthyServersError:
            pass

        stats = round_robin.get_statistics()

        assert stats['total_requests'] == initial_stats['total_requests'] + 1
        assert stats['failed_selections'] == initial_stats['failed_selections'] + 1

    def test_get_healthy_servers_excludes_unhealthy(self, round_robin, sample_servers, unhealthy_server):
        """Test that get_healthy_servers only returns healthy servers."""
        for server in sample_servers:
            round_robin.add_server(server)
        round_robin.add_server(unhealthy_server)

        healthy = round_robin.get_healthy_servers()
        healthy_ids = {server.id for server in healthy}

        assert len(healthy) == 3
        assert healthy_ids == {"server1", "server2", "server3"}
        assert "unhealthy" not in healthy_ids

    def test_server_metrics_update(self, round_robin, sample_servers):
        """Test that server metrics can be updated."""
        server = sample_servers[0]
        round_robin.add_server(server)

        # Update metrics
        result = round_robin.update_server_metrics(
            "server1",
            response_time=1.5,
            cpu_usage=0.7,
            error_rate=0.05
        )

        assert result is True
        updated_server = round_robin.get_server("server1")
        assert updated_server.metrics.response_time == 1.5
        assert updated_server.metrics.cpu_usage == 0.7
        assert updated_server.metrics.error_rate == 0.05

    def test_server_metrics_update_nonexistent_server(self, round_robin):
        """Test updating metrics for a nonexistent server."""
        with pytest.raises(ServerNotFoundError):
            round_robin.update_server_metrics("nonexistent", response_time=1.0)

    def test_logging_server_selection(self, round_robin, sample_servers):
        """Test that server selections are properly logged."""
        # Mock the logger instance directly
        mock_logger_instance = Mock()
        round_robin.logger = mock_logger_instance

        for server in sample_servers:
            round_robin.add_server(server)

        round_robin.select_server()

        # Verify that selection was logged
        mock_logger_instance.info.assert_called()

    def test_string_representation(self, round_robin, sample_servers):
        """Test string representations of the algorithm."""
        for server in sample_servers:
            round_robin.add_server(server)

        str_repr = str(round_robin)
        repr_repr = repr(round_robin)

        assert "Round Robin" in str_repr
        assert "servers: 3" in str_repr
        assert "healthy: 3" in str_repr

        assert "RoundRobin" in repr_repr
        assert "Round Robin" in repr_repr

    def test_edge_case_empty_healthy_servers_list(self, round_robin, sample_servers):
        """Test behavior when healthy_servers becomes empty during operation."""
        for server in sample_servers:
            round_robin.add_server(server)

        # Mark all servers as unhealthy
        for server in sample_servers:
            round_robin.update_server_status(server.id, ServerStatus.UNHEALTHY)

        # Should raise exception when no healthy servers
        with pytest.raises(NoHealthyServersError):
            round_robin.select_server()

    def test_weight_handling(self, round_robin):
        """Test that servers with different weights are handled correctly."""
        # Round robin should not consider weights for selection order,
        # but weights should be preserved
        weighted_servers = [
            Server(id="light", address="192.168.1.1", port=8080, weight=0.5),
            Server(id="heavy", address="192.168.1.2", port=8080, weight=2.0),
        ]

        for server in weighted_servers:
            round_robin.add_server(server)

        # Selection should still be round-robin regardless of weights
        first = round_robin.select_server()
        second = round_robin.select_server()
        third = round_robin.select_server()

        assert first.id == "light"
        assert second.id == "heavy"
        assert third.id == "light"  # Should cycle back

        # But weights should be preserved
        assert round_robin.get_server("light").weight == 0.5
        assert round_robin.get_server("heavy").weight == 2.0
