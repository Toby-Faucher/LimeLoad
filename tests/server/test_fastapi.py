import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.api import app, set_load_balancer, get_load_balancer
from load_balancer.algorithms.base import LoadBalancingAlgorithm, Server, LoadBalancingContext, ServerStatus
from load_balancer.algorithms.error import ServerNotFoundError, HealthCheckFailedError


class ConcreteLoadBalancingAlgorithm(LoadBalancingAlgorithm):
    """Concrete implementation of LoadBalancingAlgorithm for FastAPI testing"""

    def __init__(self, name: str = "TestAlgorithm"):
        super().__init__(name=name)

    def select_server(self, context=None):
        """Simple selection: return first healthy server"""
        with self._lock:
            healthy_servers = self.get_healthy_servers()
            if not healthy_servers:
                self.on_selected_failed(context)
                return None

            server = healthy_servers[0]
            self.on_server_selected(server, context)
            return server

    def add_server(self, server):
        """Add server to the algorithm"""
        with self._lock:
            super().add_server(server)

    def remove_server(self, server_id):
        """Remove server from the algorithm"""
        with self._lock:
            return super().remove_server(server_id)


class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints"""

    @pytest.fixture(autouse=True)
    def setup_load_balancer(self):
        """Setup test load balancer with servers"""
        self.lb = ConcreteLoadBalancingAlgorithm("TestAPI")

        # Create test servers
        self.server1 = Server(id="server1", address="127.0.0.1", port=8080)
        self.server2 = Server(id="server2", address="127.0.0.2", port=8081)
        self.server3 = Server(id="server3", address="127.0.0.3", port=8082, status=ServerStatus.UNHEALTHY)

        # Add servers to load balancer
        self.lb.add_server(self.server1)
        self.lb.add_server(self.server2)
        self.lb.add_server(self.server3)

        # Set global load balancer
        set_load_balancer(self.lb)

        # Create test client
        self.client = TestClient(app)

        yield

        # Cleanup
        set_load_balancer(None)

    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Load Balancer API"
        assert data["status"] == "running"

    def test_health_check_existing_server_success(self):
        """Test health check for existing server with successful health check"""
        with patch('load_balancer.api.check_server_health') as mock_health_check:
            mock_health_check.return_value = {"status": "healthy"}

            response = self.client.get("/health/server1")

            assert response.status_code == 200
            data = response.json()
            assert data["server_id"] == "server1"
            assert data["server_address"] == "127.0.0.1"
            assert data["server_port"] == 8080
            assert data["status"] == "healthy"
            assert data["healthy"] == True

            mock_health_check.assert_called_once_with("127.0.0.1", 8080)

    def test_health_check_existing_server_failure(self):
        """Test health check for existing server with failed health check"""
        with patch('load_balancer.api.check_server_health') as mock_health_check:
            mock_health_check.side_effect = HealthCheckFailedError("Connection failed")

            response = self.client.get("/health/server1")

            assert response.status_code == 200
            data = response.json()
            assert data["server_id"] == "server1"
            assert data["server_address"] == "127.0.0.1"
            assert data["server_port"] == 8080
            assert data["status"] == "unhealthy"
            assert data["healthy"] == False
            assert "Connection failed" in data["error"]

    def test_health_check_nonexistent_server(self):
        """Test health check for non-existent server"""
        response = self.client.get("/health/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "Server nonexistent not found" in data["detail"]

    def test_select_server_post_success(self):
        """Test POST /select-server endpoint with successful selection"""
        request_data = {
            "client_ip": "192.168.1.1",
            "session_id": "session123",
            "request_path": "/api/test",
            "request_method": "GET"
        }

        response = self.client.post("/select-server", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server_id"] in ["server1", "server2"]  # One of the healthy servers
        assert data["server_address"] in ["127.0.0.1", "127.0.0.2"]
        assert data["endpoint"] is not None
        assert data["message"] == "Server selected successfully"

    def test_select_server_post_no_request_data(self):
        """Test POST /select-server endpoint with no request data"""
        response = self.client.post("/select-server")

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server_id"] in ["server1", "server2"]

    def test_select_server_get_success(self):
        """Test GET /select-server endpoint with parameters"""
        response = self.client.get("/select-server?client_ip=192.168.1.1&session_id=test123")

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server_id"] in ["server1", "server2"]

    def test_select_server_no_healthy_servers(self):
        """Test server selection when no healthy servers are available"""
        # Create a load balancer with only unhealthy servers
        unhealthy_lb = ConcreteLoadBalancingAlgorithm("UnhealthyTest")
        unhealthy_server = Server(id="unhealthy", address="127.0.0.1", port=8080, status=ServerStatus.UNHEALTHY)
        unhealthy_lb.add_server(unhealthy_server)
        set_load_balancer(unhealthy_lb)

        response = self.client.post("/select-server")

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == False
        assert data["message"] == "No healthy servers available"

    def test_list_servers(self):
        """Test /servers endpoint"""
        response = self.client.get("/servers")

        assert response.status_code == 200
        data = response.json()
        assert data["total_servers"] == 3
        assert data["healthy_servers"] == 2  # server1 and server2 are healthy
        assert data["algorithm"] == "TestAPI"
        assert len(data["servers"]) == 2  # Only healthy servers are listed

        # Check server details
        server_ids = [s["id"] for s in data["servers"]]
        assert "server1" in server_ids
        assert "server2" in server_ids
        assert "server3" not in server_ids  # Unhealthy server not in healthy list

    def test_get_statistics(self):
        """Test /stats endpoint"""
        # Generate some statistics by selecting servers
        self.client.post("/select-server")
        self.client.post("/select-server")

        response = self.client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert data["algorithm"] == "TestAPI"
        assert data["server_count"] == 3
        assert data["healthy_server_count"] == 2
        assert data["statistics"]["total_requests"] == 2
        assert data["statistics"]["successful_selections"] == 2

    def test_reset_statistics(self):
        """Test POST /stats/reset endpoint"""
        # Generate some statistics first
        self.client.post("/select-server")

        response = self.client.post("/stats/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Statistics reset successfully"

        # Verify statistics were reset
        stats_response = self.client.get("/stats")
        stats_data = stats_response.json()
        assert stats_data["statistics"]["total_requests"] == 0
        assert stats_data["statistics"]["successful_selections"] == 0

    def test_no_load_balancer_initialized(self):
        """Test endpoints when load balancer is not initialized"""
        set_load_balancer(None)

        response = self.client.get("/health/server1")
        assert response.status_code == 500
        assert "Load balancer is not initialized." in response.json()["detail"]

        response = self.client.post("/select-server")
        assert response.status_code == 500
        assert "Load balancer is not initialized." in response.json()["detail"]

        response = self.client.get("/servers")
        assert response.status_code == 500
        assert "Load balancer is not initialized." in response.json()["detail"]

    def test_select_server_post_with_metadata(self):
        """Test POST /select-server with metadata"""
        request_data = {
            "client_ip": "192.168.1.1",
            "metadata": {
                "user_id": "user123",
                "session_type": "premium"
            },
            "headers": {
                "User-Agent": "TestClient",
                "Accept": "application/json"
            }
        }

        response = self.client.post("/select-server", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server_id"] is not None

    def test_health_check_endpoint_parameter_types(self):
        """Test health check endpoint properly handles server_id as string"""
        with patch('load_balancer.api.check_server_health') as mock_health_check:
            mock_health_check.return_value = {"status": "healthy"}

            response = self.client.get("/health/server1")

            assert response.status_code == 200
            # Verify the server_id is handled as string
            data = response.json()
            assert isinstance(data["server_id"], str)
            assert data["server_id"] == "server1"

    def test_select_server_get_with_all_parameters(self):
        """Test GET /select-server with all possible parameters"""
        params = {
            "client_ip": "192.168.1.100",
            "session_id": "session456",
            "request_path": "/api/data",
            "request_method": "POST"
        }

        response = self.client.get("/select-server", params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["selected"] == True
        assert data["server_id"] in ["server1", "server2"]

    def test_server_list_detailed_info(self):
        """Test that /servers endpoint returns detailed server information"""
        response = self.client.get("/servers")

        assert response.status_code == 200
        data = response.json()

        for server_info in data["servers"]:
            assert "id" in server_info
            assert "address" in server_info
            assert "port" in server_info
            assert "endpoint" in server_info
            assert "status" in server_info
            assert "weight" in server_info
            assert "is_available" in server_info

            # Verify endpoint format
            expected_endpoint = f"{server_info['address']}:{server_info['port']}"
            assert server_info["endpoint"] == expected_endpoint
