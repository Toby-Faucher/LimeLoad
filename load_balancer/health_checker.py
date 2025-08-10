import threading
import asyncio
from typing import List
from .algorithms.error import HealthCheckFailedError
from .algorithms.base import Server, LoadBalancingAlgorithm
from fastapi import FastAPI, Request

import httpx

app = FastAPI()


class HealthChecker:
    def __init__(self, lb: LoadBalancingAlgorithm, interval_seconds: int):
        self.lb = lb
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def _run_in_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run())

    async def run(self):
        while not self._stop_event.is_set():
            servers = self.lb.get_healthy_servers()
            for server in servers:
                try:
                    await check_server_health(server.address, server.port)
                except HealthCheckFailedError:
                    self.lb.remove_server(server.id)
            await asyncio.sleep(self.interval_seconds)

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
