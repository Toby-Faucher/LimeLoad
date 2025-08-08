import sys
import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.health_checker import check_server_health
from load_balancer.algorithms.error import HealthCheckFailedError


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
