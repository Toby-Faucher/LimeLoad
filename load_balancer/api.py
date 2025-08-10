from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import urllib.parse

from .algorithms.base import LoadBalancingAlgorithm, Server, LoadBalancingContext, ServerStatus
from .algorithms.error import ServerNotFoundError, HealthCheckFailedError
from .health_checker import check_server_health
from .config import load_config

app = FastAPI(title="LimeLoad API", version="1.0.0")
logger = logging.getLogger(__name__)

class LoadBalancerService:
    def __init__(self):
        self._load_balancer: Optional[LoadBalancingAlgorithm] = None
        self._config = load_config()

    def get_load_balancer(self) -> LoadBalancingAlgorithm:
        if self._load_balancer is None:
            self._load_balancer = self._create_from_config()
        return self._load_balancer

    def _create_from_config(self) -> LoadBalancingAlgorithm:
        algorithm_type = self._config.get('load_balancer', {}).get('algorithm')

        match algorithm_type:
            case 'round_robin':
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from .algorithms.round_robin import RoundRobin
                lb = RoundRobin()
            case _:
                raise ValueError(f"Unknown algorithm: {algorithm_type}")

        servers_config = self._config.get('load_balancer', {}).get('servers', {})
        for server_id, server_url in servers_config.items():
            parsed = urllib.parse.urlparse(server_url)
            server = Server(
                id=server_id,
                address=parsed.hostname or 'localhost',
                port=parsed.port or 8080
            )
            lb.add_server(server)

        return lb

_service = LoadBalancerService()

def get_load_balancer() -> LoadBalancingAlgorithm:
    """Dependency to get the load balancer instance"""
    if _service._load_balancer is None:
        raise HTTPException(status_code=500, detail="Load balancer is not initialized.")
    try:
        return _service.get_load_balancer()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load balancer initialization failed: {e}")

def set_load_balancer(lb: Optional[LoadBalancingAlgorithm]):
    """Set the global load balancer instance (for testing)"""
    global _service
    _service._load_balancer = lb


class ServerSelection(BaseModel):
    """Response model for server selection"""
    server_id: Optional[str] = None
    server_address: Optional[str] = None
    server_port: Optional[int] = None
    endpoint: Optional[str] = None
    selected: bool = False
    message: Optional[str] = None


class SelectServerRequest(BaseModel):
    """Request model for server selection"""
    client_ip: Optional[str] = None
    session_id: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = "GET"
    headers: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LimeLoad API", "status": "running"}

@app.post("/select-server")
async def select_server(
    request_data: Optional[SelectServerRequest] = None,
    lb: LoadBalancingAlgorithm = Depends(get_load_balancer)
) -> ServerSelection:
    """
    Select an available server based on the load balancing algorithm
    """
    try:
        context = None
        if request_data:
            context = LoadBalancingContext(
                client_ip=request_data.client_ip,
                session_ip=request_data.session_id,
                request_path=request_data.request_path or "",
                request_method=request_data.request_method or "GET",
                request_headers=request_data.headers or {},
                metadata=request_data.metadata or {}
            )

        selected_server = lb.select_server(context)

        if selected_server:
            return ServerSelection(
                server_id=selected_server.id,
                server_address=selected_server.address,
                server_port=selected_server.port,
                endpoint=selected_server.endpoint,
                selected=True,
                message="Server selected successfully"
            )
        else:
            return ServerSelection(
                selected=False,
                message="No healthy servers available"
            )

    except Exception as e:
        logger.error(f"Error selecting server: {e}")
        raise HTTPException(status_code=500, detail="Failed to select server")


@app.get("/select-server")
async def select_server_get(
    client_ip: Optional[str] = None,
    session_id: Optional[str] = None,
    request_path: Optional[str] = None,
    request_method: Optional[str] = "GET",
    lb: LoadBalancingAlgorithm = Depends(get_load_balancer)
) -> ServerSelection:
    """
    Select an available server (GET version for simple requests)
    """
    request_data = SelectServerRequest(
        client_ip=client_ip,
        session_id=session_id,
        request_path=request_path,
        request_method=request_method
    )
    return await select_server(request_data, lb)


@app.get("/servers")
async def list_servers(lb: LoadBalancingAlgorithm = Depends(get_load_balancer)):
    """
    List all servers in the load balancer pool
    """
    try:
        healthy_servers = lb.get_healthy_servers()
        all_servers_count = lb.get_server_count()

        servers_info = []
        for server in healthy_servers:
            servers_info.append({
                "id": server.id,
                "address": server.address,
                "port": server.port,
                "endpoint": server.endpoint,
                "status": server.status.value,
                "weight": server.weight,
                "is_available": server.is_available
            })

        return {
            "servers": servers_info,
            "total_servers": all_servers_count,
            "healthy_servers": len(healthy_servers),
            "algorithm": lb.name
        }

    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list servers")


@app.get("/stats")
async def get_statistics(lb: LoadBalancingAlgorithm = Depends(get_load_balancer)):
    """
    Get load balancer statistics
    """
    try:
        stats = lb.get_statistics()
        return {
            "statistics": stats,
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@app.post("/stats/reset")
async def reset_statistics(lb: LoadBalancingAlgorithm = Depends(get_load_balancer)):
    """
    Reset load balancer statistics
    """
    try:
        lb.reset_statistics()
        return {"message": "Statistics reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset statistics")
