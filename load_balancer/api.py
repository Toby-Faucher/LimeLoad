from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from .algorithms.base import LoadBalancingAlgorithm, Server, LoadBalancingContext, ServerStatus
from .algorithms.error import ServerNotFoundError, HealthCheckFailedError
from .health_checker import check_server_health

app = FastAPI(title="LimeLoad API", version="1.0.0")
logger = logging.getLogger(__name__)

# Global load balancer instance - in production this would be dependency injected
_load_balancer: Optional[LoadBalancingAlgorithm] = None


def get_load_balancer() -> LoadBalancingAlgorithm:
    """Dependency to get the load balancer instance"""
    global _load_balancer
    if _load_balancer is None:
        raise HTTPException(status_code=500, detail="Load balancer not initialized")
    return _load_balancer


def set_load_balancer(lb: Optional[LoadBalancingAlgorithm]):
    """Set the global load balancer instance"""
    global _load_balancer
    _load_balancer = lb


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
    return {"message": "Load Balancer API", "status": "running"}


@app.get("/health/{server_id}")
async def health_check_server(server_id: str, lb: LoadBalancingAlgorithm = Depends(get_load_balancer)):
    """
    Check the health of a specific server by server ID
    """
    try:
        server = lb.get_server(server_id)
        assert server is not None

        health_result = await check_server_health(server.address, server.port)

        return {
            "server_id": server_id,
            "server_address": server.address,
            "server_port": server.port,
            "status": health_result.get("status", "unknown"),
            "healthy": True
        }

    except ServerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
    except HealthCheckFailedError as e:
        try:
            server = lb.get_server(server_id)
            assert server is not None
            return {
                "server_id": server_id,
                "server_address": server.address,
                "server_port": server.port,
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
        except ServerNotFoundError:
            raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error checking health for server {server_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
            "algorithm": lb.name,
            "server_count": lb.get_server_count(),
            "healthy_server_count": lb.get_healthy_server_count()
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
