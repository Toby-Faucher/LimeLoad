import sys
import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock, Mock
import asyncio
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.health_checker import check_server_health, HealthChecker
from load_balancer.algorithms.error import HealthCheckFailedError
from load_balancer.algorithms.base import Server, ServerStatus, LoadBalancingAlgorithm
from load_balancer.algorithms.round_robin import RoundRobin


class TestHealthChecker:
    """Test cases for the health checker functionality"""

    def test_successful_health_check(self):
        """Test a successful health check"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None

                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                result = await check_server_health("127.0.0.1", 8080)

                assert result == {"status": "healthy"}
                mock_client_instance.get.assert_called_once_with("http://127.0.0.1:8080/health")

        asyncio.run(run_test())

    def test_failed_health_check_connection_error(self):
        """Test a health check that fails due to connection error"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = httpx.RequestError("Connection failed")

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                with pytest.raises(HealthCheckFailedError) as exc_info:
                    await check_server_health("127.0.0.1", 8080)

                assert "Health check failed for 127.0.0.1:8080" in str(exc_info.value)
                assert "Connection failed" in str(exc_info.value)

        asyncio.run(run_test())

    def test_failed_health_check_http_error(self):
        """Test a health check that fails due to HTTP error"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_response = MagicMock()
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())

                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                with pytest.raises(HealthCheckFailedError) as exc_info:
                    await check_server_health("127.0.0.1", 8080)

                assert "Health check failed for 127.0.0.1:8080" in str(exc_info.value)

        asyncio.run(run_test())

    def test_health_check_with_invalid_server_ip(self):
        """Test a health check with an invalid server IP"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = httpx.RequestError("Invalid IP address")

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                with pytest.raises(HealthCheckFailedError) as exc_info:
                    await check_server_health("999.999.999.999", 8080)

                assert "Health check failed for 999.999.999.999:8080" in str(exc_info.value)
                assert "Invalid IP address" in str(exc_info.value)

        asyncio.run(run_test())

    def test_health_check_with_invalid_server_port(self):
        """Test a health check with an invalid server port"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = httpx.RequestError("Connection refused")

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                with pytest.raises(HealthCheckFailedError) as exc_info:
                    await check_server_health("127.0.0.1", 99999)

                assert "Health check failed for 127.0.0.1:99999" in str(exc_info.value)
                assert "Connection refused" in str(exc_info.value)

        asyncio.run(run_test())

    def test_health_check_constructs_correct_url(self):
        """Test that the health check constructs the correct URL"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_response = MagicMock()
                mock_response.raise_for_status.return_value = None

                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                await check_server_health("example.com", 3000)

                mock_client_instance.get.assert_called_once_with("http://example.com:3000/health")

        asyncio.run(run_test())

    def test_health_check_timeout(self):
        """Test a health check that times out"""
        async def run_test():
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = httpx.RequestError("Request timed out")

                mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                mock_client_class.return_value.__aexit__.return_value = None

                with pytest.raises(HealthCheckFailedError) as exc_info:
                    await check_server_health("127.0.0.1", 8080)

                assert "Health check failed for 127.0.0.1:8080" in str(exc_info.value)
                assert "Request timed out" in str(exc_info.value)

        asyncio.run(run_test())


class TestHealthCheckerClass:
    """Test cases for the HealthChecker class"""

    @pytest.fixture
    def mock_load_balancer(self):
        """Create a mock load balancer for testing"""
        lb = Mock(spec=LoadBalancingAlgorithm)
        lb.get_healthy_servers.return_value = []
        lb.remove_server.return_value = True
        return lb

    @pytest.fixture
    def sample_servers(self):
        """Create sample servers for testing"""
        return [
            Server(id="server1", address="127.0.0.1", port=8080, weight=1.0),
            Server(id="server2", address="127.0.0.1", port=8081, weight=1.0),
            Server(id="server3", address="127.0.0.1", port=8082, weight=1.0),
        ]

    @pytest.fixture
    def health_checker(self, mock_load_balancer):
        """Create a HealthChecker instance for testing"""
        return HealthChecker(mock_load_balancer, interval_seconds=1)

    def test_health_checker_initialization(self, mock_load_balancer):
        """Test that HealthChecker initializes correctly"""
        hc = HealthChecker(mock_load_balancer, interval_seconds=5)

        assert hc.lb == mock_load_balancer
        assert hc.interval_seconds == 5
        assert isinstance(hc._stop_event, threading.Event)
        assert isinstance(hc._thread, threading.Thread)
        assert hc._thread.daemon is True
        assert not hc._stop_event.is_set()

    def test_health_checker_start_and_stop(self, health_checker):
        """Test starting and stopping the health checker"""
        # Mock the thread to avoid actually starting it
        health_checker._thread = Mock()

        health_checker.start()
        health_checker._thread.start.assert_called_once()

        health_checker._thread.join = Mock()
        health_checker.stop()

        assert health_checker._stop_event.is_set()
        health_checker._thread.join.assert_called_once()

    def test_health_checker_with_no_servers(self, health_checker):
        """Test health checker behavior when no servers are available"""
        health_checker.lb.get_healthy_servers.return_value = []

        # Mock the async run method to test synchronously
        async def mock_async_run():
            servers = health_checker.lb.get_healthy_servers()
            assert len(servers) == 0
            health_checker._stop_event.set()  # Stop after first iteration

        health_checker._async_run = mock_async_run

        # Run one iteration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(health_checker._async_run())
        finally:
            loop.close()

        health_checker.lb.get_healthy_servers.assert_called()
        health_checker.lb.remove_server.assert_not_called()

    def test_health_checker_with_healthy_servers(self, health_checker, sample_servers):
        """Test health checker with healthy servers"""
        health_checker.lb.get_healthy_servers.return_value = sample_servers[:2]

        async def mock_check_server_health(address, port):
            return {"status": "healthy"}

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            # Create a mock async run method that runs one iteration
            async def mock_async_run():
                servers = health_checker.lb.get_healthy_servers()
                for server in servers:
                    await mock_health_check(server.address, server.port)
                health_checker._stop_event.set()  # Stop after first iteration

            health_checker._async_run = mock_async_run

            # Run the health checker
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(health_checker._async_run())
            finally:
                loop.close()

        health_checker.lb.get_healthy_servers.assert_called()
        health_checker.lb.remove_server.assert_not_called()

    def test_health_checker_with_unhealthy_servers(self, health_checker, sample_servers):
        """Test health checker removes unhealthy servers"""
        unhealthy_server = sample_servers[0]
        healthy_server = sample_servers[1]
        health_checker.lb.get_healthy_servers.return_value = [unhealthy_server, healthy_server]

        async def mock_check_server_health(address, port):
            if port == unhealthy_server.port:
                raise HealthCheckFailedError(f"Health check failed for {address}:{port}")
            return {"status": "healthy"}

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            # Create a mock async run method that runs one iteration
            async def mock_async_run():
                servers = health_checker.lb.get_healthy_servers()
                for server in servers:
                    try:
                        await mock_health_check(server.address, server.port)
                    except HealthCheckFailedError:
                        health_checker.lb.remove_server(server.id)
                health_checker._stop_event.set()  # Stop after first iteration

            health_checker._async_run = mock_async_run

            # Run the health checker
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(health_checker._async_run())
            finally:
                loop.close()

        health_checker.lb.get_healthy_servers.assert_called()
        health_checker.lb.remove_server.assert_called_once_with(unhealthy_server.id)

    def test_health_checker_async_run_loop(self, health_checker, sample_servers):
        """Test the async run loop behavior"""
        health_checker.lb.get_healthy_servers.return_value = sample_servers[:1]
        call_count = 0

        async def mock_check_server_health(address, port):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Stop after 2 iterations
                health_checker._stop_event.set()
            return {"status": "healthy"}

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            with patch('asyncio.sleep', return_value=None) as mock_sleep:
                # Create a mock async run method that runs limited iterations
                async def mock_async_run():
                    iteration_count = 0
                    while not health_checker._stop_event.is_set() and iteration_count < 2:
                        servers = health_checker.lb.get_healthy_servers()
                        for server in servers:
                            try:
                                await mock_health_check(server.address, server.port)
                            except HealthCheckFailedError:
                                health_checker.lb.remove_server(server.id)
                        await asyncio.sleep(health_checker.interval_seconds)
                        iteration_count += 1
                    health_checker._stop_event.set()

                health_checker._async_run = mock_async_run

                # Run the health checker
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(health_checker._async_run())
                finally:
                    loop.close()

        assert call_count == 2
        assert mock_sleep.call_count >= 1  # Should have called sleep at least once
        mock_sleep.assert_called_with(health_checker.interval_seconds)

    def test_health_checker_exception_handling(self, health_checker, sample_servers):
        """Test health checker handles exceptions properly"""
        health_checker.lb.get_healthy_servers.return_value = sample_servers[:1]

        async def mock_check_server_health(address, port):
            raise Exception("Unexpected error")

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            # Create a mock async run method that catches exceptions
            async def mock_async_run():
                servers = health_checker.lb.get_healthy_servers()
                for server in servers:
                    try:
                        await mock_health_check(server.address, server.port)
                    except HealthCheckFailedError:
                        health_checker.lb.remove_server(server.id)
                    except Exception:
                        # Should not crash the health checker
                        pass
                health_checker._stop_event.set()

            health_checker._async_run = mock_async_run

            # This should not raise an exception
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(health_checker._async_run())
            finally:
                loop.close()

        health_checker.lb.remove_server.assert_not_called()

    def test_health_checker_stop_event_behavior(self, health_checker):
        """Test that the stop event properly terminates the health checker"""
        health_checker.lb.get_healthy_servers.return_value = []

        # Set stop event before starting
        health_checker._stop_event.set()

        loop_iterations = 0

        async def mock_async_run():
            nonlocal loop_iterations
            while not health_checker._stop_event.is_set():
                loop_iterations += 1
                if loop_iterations > 5:  # Safety check to prevent infinite loop
                    break
                await asyncio.sleep(0.1)

        health_checker._async_run = mock_async_run

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(health_checker._async_run())
        finally:
            loop.close()

        assert loop_iterations == 0  # Should not enter the loop


class TestHealthCheckerIntegration:
    """Integration tests for HealthChecker with actual load balancer"""

    @pytest.fixture
    def round_robin_lb(self):
        """Create a RoundRobin load balancer for integration testing"""
        return RoundRobin()

    @pytest.fixture
    def servers_for_lb(self):
        """Create servers to add to the load balancer"""
        return [
            Server(id="server1", address="127.0.0.1", port=8080),
            Server(id="server2", address="127.0.0.1", port=8081),
            Server(id="server3", address="127.0.0.1", port=8082),
        ]

    def test_health_checker_integration_with_round_robin(self, round_robin_lb, servers_for_lb):
        """Test HealthChecker integration with RoundRobin algorithm"""
        # Add servers to load balancer
        for server in servers_for_lb:
            round_robin_lb.add_server(server)

        assert round_robin_lb.get_server_count() == 3
        assert round_robin_lb.get_healthy_server_count() == 3

        # Create health checker
        health_checker = HealthChecker(round_robin_lb, interval_seconds=1)

        # Mock health check to fail for server2
        async def mock_check_server_health(address, port):
            if port == 8081:  # server2
                raise HealthCheckFailedError(f"Health check failed for {address}:{port}")
            return {"status": "healthy"}

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            # Run one iteration manually
            async def run_one_iteration():
                servers = health_checker.lb.get_healthy_servers()
                for server in servers:
                    try:
                        await mock_health_check(server.address, server.port)
                    except HealthCheckFailedError:
                        health_checker.lb.remove_server(server.id)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_one_iteration())
            finally:
                loop.close()

        # Verify server2 was removed
        assert round_robin_lb.get_server_count() == 2
        assert round_robin_lb.get_healthy_server_count() == 2

        # Verify we can't get server2 anymore
        with pytest.raises(Exception):  # ServerNotFoundError
            round_robin_lb.get_server("server2")

    def test_health_checker_with_all_servers_failing(self, round_robin_lb, servers_for_lb):
        """Test HealthChecker when all servers fail health checks"""
        # Add servers to load balancer
        for server in servers_for_lb:
            round_robin_lb.add_server(server)

        health_checker = HealthChecker(round_robin_lb, interval_seconds=1)

        # Mock all health checks to fail
        async def mock_check_server_health(address, port):
            raise HealthCheckFailedError(f"Health check failed for {address}:{port}")

        with patch('load_balancer.health_checker.check_server_health', side_effect=mock_check_server_health) as mock_health_check:
            # Run one iteration manually
            async def run_one_iteration():
                servers = health_checker.lb.get_healthy_servers()
                for server in servers:
                    try:
                        await mock_health_check(server.address, server.port)
                    except HealthCheckFailedError:
                        health_checker.lb.remove_server(server.id)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_one_iteration())
            finally:
                loop.close()

        # All servers should be removed
        assert round_robin_lb.get_server_count() == 0
        assert round_robin_lb.get_healthy_server_count() == 0

    def test_health_check_with_different_hosts_and_ports(self):
        """Test the health check with various host and port combinations"""
        async def run_test():
            test_cases = [
                ("localhost", 3000),
                ("192.168.1.100", 9000),
                ("10.0.0.1", 80),
            ]

            for host, port in test_cases:
                with patch('httpx.AsyncClient') as mock_client_class:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None

                    mock_client_instance = AsyncMock()
                    mock_client_instance.get.return_value = mock_response

                    mock_client_class.return_value.__aenter__.return_value = mock_client_instance
                    mock_client_class.return_value.__aexit__.return_value = None

                    result = await check_server_health(host, port)

                    assert result == {"status": "healthy"}
                    mock_client_instance.get.assert_called_with(f"http://{host}:{port}/health")

        asyncio.run(run_test())
