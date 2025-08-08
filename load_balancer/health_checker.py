from .algorithms.base import Server, ServerStatus
from .algorithms.error import HealthCheckFailedError

from fastapi import FastAPI, Request

import httpx

app = FastAPI()


@app.get("/health/{server_ip}/{server_port}")
async def check_server_health(server_ip: str, server_port: int):
    """
    Checks the health of a server by making a GET request to its health check endpoint.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{server_ip}:{server_port}/health")
            response.raise_for_status()
            return {"status": "healthy"}
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        raise HealthCheckFailedError(f"Health check failed for {server_ip}:{server_port}: {e}") from e
