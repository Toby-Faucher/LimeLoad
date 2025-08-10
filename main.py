import uvicorn

from load_balancer.api import app, set_load_balancer
from load_balancer.config import load_config
from load_balancer.algorithms.base import Server
from load_balancer.algorithms.round_robin import RoundRobin


def initialize_load_balancer():
    """
    Initializes the load balancer from the configuration.
    """
    config = load_config()
    lb_config = config.get("load_balancer", {})
    # Temp
    algorithm_name = lb_config.get("algorithm", {})
    servers_config = lb_config.get("servers", {})
    # Switch this to a match statement
    match algorithm_name:
        case "round_robin":
            lb = RoundRobin()
        case _:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

    for server_id, server_info in servers_config.items():
        server = Server(
            id=server_id,
            address=server_info["address"],
            port=server_info["port"],
        )
        lb.add_server(server)

    return lb

@app.on_event("startup")
async def startup_event():
    """Initialize the load balancer and start the health checker."""
    lb_instance = initialize_load_balancer()
    set_load_balancer(lb_instance)

if __name__ == "__main__":
    config = load_config()
    fastapi_config = config.get("fastapi", {})
    host = fastapi_config.get("host", "0.0.0.0")
    port = fastapi_config.get("port")

    uvicorn.run(app, host=host, port=port)
